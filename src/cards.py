"""Builds the flat data payloads sent to the Teams Workflows webhook.

The Adaptive Card LAYOUT lives in the Power Automate flow as a literal card with
@{triggerBody()?['field']} tokens. This script only sends the *data*. The field
contract is shared by all three alert kinds so the flow card never changes:

    ticket       - issue key (clickable + Open button)
    summary      - issue summary
    headline     - accent line: "You were mentioned" / "Assigned to you" /
                   "Reassigned from you" / "" (empty for plain comments)
    subline      - the line under the header (e.g. "Bob commented:",
                   "Now on your plate", "Now assigned to: Jane")
    snippet      - comment text (empty for assignment events)
    url          - link to the ticket / focused comment

NOTE: 'headline' and 'subline' replace the old 'mentionLine'/'author' field
names. Update the flow card tokens to match (see README).

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
        "headline": headline,
        "subline": _sanitize(subline),
        "snippet": _sanitize(snippet),
        "url": url,
    }


def comment_payload(c: RelevantComment) -> dict:
    snippet = _sanitize(clean_snippet(c.body, config.SNIPPET_CHARS)) or "(no text body)"
    headline = "You were mentioned" if c.mentions_me else ""
    return _payload(
        ticket=c.issue_key,
        summary=c.issue_summary,
        headline=headline,
        subline=f"{_sanitize(c.author)} commented:",
        snippet=snippet,
        url=c.url,
    )


def assigned_payload(ticket: str, summary: str, url: str) -> dict:
    return _payload(
        ticket=ticket,
        summary=summary,
        headline="Assigned to you",
        subline="This ticket is now on your plate",
        snippet="",
        url=url,
    )


def reassigned_payload(ticket: str, summary: str, url: str, new_assignee) -> dict:
    who = new_assignee or "Unassigned"
    return _payload(
        ticket=ticket,
        summary=summary,
        headline="Reassigned from you",
        subline=f"Now assigned to: {who}",
        snippet="",
        url=url,
    )