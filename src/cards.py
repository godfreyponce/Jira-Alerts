"""Builds the flat data payloads sent to the Teams Workflows webhook.

The message LAYOUT lives in the Power Automate flow, which drops
@{triggerBody()?['field']} tokens into HTML. This script only sends the *data*.
Every alert kind shares one field contract so the flow never changes:

    ticket    - issue key (the flow's Open link splits it)
    summary   - issue summary; rendered LAST, as context
    headline  - the lead sentence: names the ticket, ends in terminal punctuation
                ("Bob commented on ABC-1:", "Tag, you're it — ABC-1.")
    subline   - optional second sentence ("Now assigned to Jane.")
    snippet   - comment text (empty for assignment events)
    url       - link to the ticket / focused comment

The macOS toast is this message flattened - HTML stripped, first ~4 lines kept -
so structure has to come from wording and punctuation, not markup. That's why the
headline carries the news and the summary comes last. Full reasoning:
docs/superpowers/specs/2026-07-31-toast-formatting-design.md

Interpolated values are sanitized (no quotes/backslashes/control chars) so they
can't break the card JSON when the flow drops them into a string literal.
"""

import re

from . import config
from .jira_client import RelevantComment, clean_snippet


def _sanitize(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\\", " ").replace('"', "'")
    text = re.sub(r"[\x00-\x1f]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _payload(ticket, summary, headline, subline, snippet, url) -> dict:
    return {
        "ticket": ticket,
        "summary": _sanitize(summary) or "(no summary)",
        "headline": _sanitize(headline),
        "subline": _sanitize(subline),
        "snippet": _sanitize(snippet),
        "url": url,
    }


def comment_payload(c: RelevantComment) -> dict:
    snippet = _sanitize(clean_snippet(c.body, config.SNIPPET_CHARS)) or "(no text body)"
    verb = "mentioned you on" if c.mentions_me else "commented on"
    return _payload(
        ticket=c.issue_key,
        summary=c.issue_summary,
        headline=f"{c.author} {verb} {c.issue_key}:",
        subline="",
        snippet=snippet,
        url=c.url,
    )


def assigned_payload(ticket: str, summary: str, url: str) -> dict:
    return _payload(
        ticket=ticket,
        summary=summary,
        headline=f"Tag, you're it — {ticket}.",
        subline="",
        snippet="",
        url=url,
    )


def digest_payload(n_comments: int, n_assigned: int, n_reassigned: int) -> dict:
    """Single card summarizing a burst that exceeded MAX_CARDS_PER_CYCLE.

    Uses the same field contract as every other card so the flow layout
    doesn't need to change.
    """
    total = n_comments + n_assigned + n_reassigned
    parts = []
    if n_comments:
        parts.append(f"{n_comments} new comment(s)")
    if n_assigned:
        parts.append(f"{n_assigned} ticket(s) assigned to you")
    if n_reassigned:
        parts.append(f"{n_reassigned} ticket(s) reassigned away")
    return _payload(
        ticket="Digest",
        summary=f"{total} Jira updates this cycle",
        headline="Update burst.",
        subline=", ".join(parts) + ".",
        snippet=(
            f"More than {config.MAX_CARDS_PER_CYCLE} alerts in one cycle were "
            "collapsed into this digest to avoid webhook throttling."
        ),
        url=f"{config.JIRA_BASE_URL}/issues/?jql=assignee%20%3D%20currentUser()",
    )


def reassigned_payload(ticket: str, summary: str, url: str, new_assignee) -> dict:
    subline = f"Now assigned to {new_assignee}." if new_assignee else "Now unassigned."
    return _payload(
        ticket=ticket,
        summary=summary,
        headline=f"Not yours anymore :) {ticket}.",
        subline=subline,
        snippet="",
        url=url,
    )