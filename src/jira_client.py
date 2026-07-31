"""Jira Data Center client.

Auth is a Personal Access Token sent as a Bearer header (this is the DC/Server
scheme; Jira *Cloud* uses email+token Basic auth instead).

Two JQL queries run each cycle and their issue sets are unioned:

  A) "assigned"   -> issues currently assigned to you
  B) "mentions"   -> issues whose comments text-match your username

For every matched issue we pull recent comments and classify each one. A comment
is relevant if it's on a currently-assigned issue OR its body contains a mention
marker. Tickets you merely watch, reported, or were once assigned to do NOT
trigger comment alerts (they proved too noisy).

Comments you authored yourself are always skipped — you don't need a DM
about your own words.
"""

import re
from dataclasses import dataclass
from typing import Dict, List

import requests

from . import config


@dataclass
class RelevantComment:
    issue_key: str
    issue_summary: str
    comment_id: str
    author: str
    body: str
    created: str
    mentions_me: bool

    @property
    def url(self) -> str:
        return f"{config.JIRA_BASE_URL}/browse/{self.issue_key}?focusedCommentId={self.comment_id}"


_SESSION = requests.Session()
_SESSION.headers.update(
    {
        "Authorization": f"Bearer {config.JIRA_PAT}",
        "Accept": "application/json",
        "Content-Type": "application/json",
        # Jira DC XSRF guard: harmless on GETs, prevents 401s on any POSTs.
        "X-Atlassian-Token": "no-check",
    }
)

_TIMEOUT = 30


def _search(jql: str) -> List[dict]:
    """Return issues (key + summary) matching a JQL query.

    Uses GET (not POST). On Jira Data Center the POST /search endpoint can be
    rejected with 401 by an XSRF check even when the PAT is valid; the GET form
    takes JQL as a query param and isn't subject to that check.
    """
    resp = _SESSION.get(
        f"{config.JIRA_BASE_URL}/rest/api/2/search",
        params={
            "jql": jql,
            "fields": "summary",
            "maxResults": 100,
            "validateQuery": "warn",
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("issues", [])


def _comments(issue_key: str) -> List[dict]:
    """Return the most recent comments on an issue (newest first)."""
    resp = _SESSION.get(
        f"{config.JIRA_BASE_URL}/rest/api/2/issue/{issue_key}/comment",
        params={
            "orderBy": "-created",
            "maxResults": config.COMMENTS_PER_ISSUE,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("comments", [])


def _mentions_me(body: str) -> bool:
    return any(token in body for token in config.MENTION_TOKENS)


def collect_relevant_comments() -> List[RelevantComment]:
    window = config.LOOKBACK_MINUTES

    assigned_jql = (
        "assignee = currentUser() "
        f"AND updated >= -{window}m ORDER BY updated DESC"
    )
    # Note: comment text search is best-effort, and the ONLY way to catch
    # mentions on tickets not currently assigned to you.
    mention_jql = (
        f'comment ~ "{config.JIRA_USERNAME}" '
        f"AND updated >= -{window}m ORDER BY updated DESC"
    )

    assigned_issues = {i["key"]: i for i in _search(assigned_jql)}
    try:
        mention_issues = {i["key"]: i for i in _search(mention_jql)}
    except requests.HTTPError:
        # Some DC text-index configs reject `comment ~`; degrade gracefully.
        mention_issues = {}

    all_issues: Dict[str, dict] = {**mention_issues, **assigned_issues}

    results: List[RelevantComment] = []
    for key, issue in all_issues.items():
        summary = issue.get("fields", {}).get("summary", "") or "(no summary)"
        on_assigned_issue = key in assigned_issues
        for c in _comments(key):
            author = c.get("author", {}) or {}
            if (
                author.get("name") == config.JIRA_USERNAME
                or author.get("key") == config.JIRA_USER_KEY
            ):
                continue  # your own comments are noise, not news (#6)
            body = c.get("body", "") or ""
            mentions = _mentions_me(body)
            if not (on_assigned_issue or mentions):
                continue
            results.append(
                RelevantComment(
                    issue_key=key,
                    issue_summary=summary,
                    comment_id=str(c["id"]),
                    author=author.get("displayName", "Unknown"),
                    body=body,
                    created=c.get("created", ""),
                    mentions_me=mentions,
                )
            )
    return results


def ticket_url(issue_key: str) -> str:
    return f"{config.JIRA_BASE_URL}/browse/{issue_key}"


def current_assignments() -> Dict[str, str]:
    """Tickets currently assigned to you, as {issue_key: summary}.

    No time window: this is current state, not an event feed. We diff this set
    against the previous cycle's set to detect 'assigned to you' (newly present)
    and 'reassigned away' (newly absent).
    """
    jql = "assignee = currentUser() ORDER BY updated DESC"
    out: Dict[str, str] = {}
    for issue in _search(jql):
        out[issue["key"]] = issue.get("fields", {}).get("summary", "") or "(no summary)"
    return out


def fetch_assignees(keys) -> Dict[str, dict]:
    """For tickets that left your plate, look up who has them now.

    Returns {issue_key: {"assignee": display_or_None, "summary": str}}.
    """
    keys = list(keys)
    if not keys:
        return {}
    key_list = ",".join(keys)
    resp = _SESSION.get(
        f"{config.JIRA_BASE_URL}/rest/api/2/search",
        params={
            "jql": f"key in ({key_list})",
            "fields": "summary,assignee",
            "maxResults": 100,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    out: Dict[str, dict] = {}
    for issue in resp.json().get("issues", []):
        fields = issue.get("fields", {})
        assignee = fields.get("assignee")
        name = assignee.get("name") if assignee else None
        akey = assignee.get("key") if assignee else None
        is_me = bool(assignee) and (
            name == config.JIRA_USERNAME or akey == config.JIRA_USER_KEY
        )
        out[issue["key"]] = {
            "assignee": assignee.get("displayName") if assignee else None,
            "is_me": is_me,
            "summary": fields.get("summary", "") or "(no summary)",
        }
    return out


# --- helpers used by the card builder ---

_MENTION_RE = re.compile(r"\[~(?:accountid:)?([^\]]+)\]")


def clean_snippet(body: str, limit: int) -> str:
    """Turn raw wiki-markup comment body into a short, readable snippet."""
    text = _MENTION_RE.sub(lambda m: "@" + m.group(1), body)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > limit:
        text = text[: limit - 1].rstrip() + "\u2026"  # ellipsis
    return text