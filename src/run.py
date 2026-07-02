"""Entry point: one polling cycle.

Three alert streams, all delivered through the same Teams webhook:
  1. New comments on tickets you've worked on
  2. New comments that @mention you
  3. Assignment changes on your breadcrumbed tickets:
       - a ticket becomes assigned to you      -> "Assigned to you"
       - a ticket leaves you (reassigned/unassigned) -> "Reassigned from you"

Comments dedup via a seen-set. Assignments are detected by diffing the set of
tickets currently assigned to you against last cycle's set (stored in
state['assignees']) -- inherently idempotent, so no seen-set needed. A ticket
that leaves you is dropped from tracking; if it ever returns it re-fires.

FIRST RUN seeds both comments and the current assignment set silently, so you
aren't flooded with your existing backlog.
"""

import sys
from datetime import datetime, timezone

from . import config, state
from .cards import assigned_payload, comment_payload, reassigned_payload
from .jira_client import (
    collect_relevant_comments,
    current_assignments,
    fetch_assignees,
    ticket_url,
)
from .notifier import send


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def main() -> int:
    st = state.load(config.STATE_PATH)
    comments = collect_relevant_comments()
    assignments_now = current_assignments()          # {key: summary}
    current_keys = set(assignments_now.keys())

    # ---- First run: seed everything silently ----
    if not st["initialized"]:
        for c in comments:
            state.mark_seen(st, c.comment_id)
        st["assignees"] = {k: _now() for k in current_keys}
        st["initialized"] = True
        state.prune(st, config.PRUNE_DAYS)
        state.save(config.STATE_PATH, st)
        print(
            f"Initialized: seeded {len(comments)} comment(s) and "
            f"{len(current_keys)} current assignment(s) without notifying."
        )
        return 0

    sent = 0

    # ---- Assignment seed guard ----
    # If we've never tracked assignments before (map empty, e.g. this feature
    # was added after the system was already running), seed the current set
    # silently so we don't fire an alert for every ticket already assigned to
    # you. This is independent of the global comment 'initialized' flag.
    if not st["assignees"] and current_keys:
        st["assignees"] = {k: _now() for k in current_keys}
        state.save(config.STATE_PATH, st)
        print(f"Seeded {len(current_keys)} current assignment(s) silently.")
        # fall through to handle comments normally this cycle

    # ---- Stream 1+2: new comments ----
    new_comments = [c for c in comments if not state.is_seen(st, c.comment_id)]
    new_comments.sort(key=lambda c: c.created)
    for c in new_comments:
        try:
            send(comment_payload(c))
            state.mark_seen(st, c.comment_id)
            sent += 1
            tag = " (mention)" if c.mentions_me else ""
            print(f"Comment alert: {c.issue_key} {c.comment_id}{tag}")
        except Exception as e:  # noqa: BLE001
            print(f"Failed comment {c.issue_key} {c.comment_id}: {e}", file=sys.stderr)

    # ---- Stream 3: assignment changes ----
    tracked = set(st["assignees"].keys())
    newly_assigned = current_keys - tracked
    left_me = tracked - current_keys

    for k in sorted(newly_assigned):
        try:
            send(assigned_payload(k, assignments_now[k], ticket_url(k)))
            sent += 1
            print(f"Assigned alert: {k}")
        except Exception as e:  # noqa: BLE001
            print(f"Failed assigned {k}: {e}", file=sys.stderr)

    if left_me:
        info = fetch_assignees(left_me)
        for k in sorted(left_me):
            meta = info.get(k, {})
            # Still assigned to you -> it left the active set for another reason
            # (e.g. you closed it), which is not a reassignment. Don't alert.
            if meta.get("is_me"):
                print(f"Skipped {k}: left active set but still yours (closed?)")
                continue
            who = meta.get("assignee")
            summ = meta.get("summary", "")
            try:
                send(reassigned_payload(k, summ, ticket_url(k), who))
                sent += 1
                print(f"Reassigned alert: {k} -> {who or 'Unassigned'}")
            except Exception as e:  # noqa: BLE001
                print(f"Failed reassigned {k}: {e}", file=sys.stderr)

    # Tracking always reflects the current set: newly added are now tracked,
    # departed ones are dropped (re-fire if they ever return).
    st["assignees"] = {k: st["assignees"].get(k, _now()) for k in current_keys}

    state.prune(st, config.PRUNE_DAYS)
    state.save(config.STATE_PATH, st)
    print(
        f"Cycle complete: {sent} notification(s), "
        f"{len(comments)} comment(s) scanned, {len(current_keys)} assigned to you."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())