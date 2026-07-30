# Design: self-comment filter (#6) + README refresh (#12)

Date: 2026-07-30
Status: approved by owner

## #6 — Skip comment alerts authored by the owner

**Decision: always filter, no escape hatch.** (Owner chose this over an
`ALERT_ON_SELF` env toggle.)

- In `collect_relevant_comments()` (`src/jira_client.py`), inside the per-comment
  loop: read the comment's `author` dict and skip the comment when
  `author.name == JIRA_USERNAME` or `author.key == JIRA_USER_KEY` — the same
  identity check `fetch_assignees()` already uses.
- Self-authored comments are skipped even if they contain a mention token.
- Assignment alerts are untouched: assigning yourself a ticket still alerts
  (state change, not self-talk).
- Side effect (accepted): self-comments are no longer seeded into dedup state.
  Harmless — they can never alert.
- Remove the "Comments you write on your own tickets currently alert you too"
  bullet from `docs/ONBOARDING.md` Known quirks (it references this fix).

**Verify:** `python -m py_compile src/*.py`, then a real cycle after commenting
on an owned ticket — success is *no* DM and a normal cycle in the log.
`./scripts/send-test.sh` still confirms the Teams path.

**Testing tradeoff (accepted):** self-commenting was the one-person end-to-end
test. After this, `send-test.sh` covers the Teams half; the full pipeline needs
a real event (second person, or an assignment change).

## #12 — README slimmed to overview + pointer

**Decision: slim, don't fix in place.** One source of truth for setup
(`docs/ONBOARDING.md`) so the card-binding drift class of bug dies permanently.

New README structure:

1. **What it is** — Jira DC → Teams DM notifier; plain message with card-like
   layout via Power Automate webhook.
2. **How it works** — diagram updated for the launchd era: LaunchAgent
   (300 s) → `scripts/run-local.sh` → `src/run.py` → Jira REST → dedup
   (`state.json`, local file) → webhook → Teams. Keep the "sink behind one
   function" swap note.
3. **Setup** — a pointer to `docs/ONBOARDING.md`. No duplicated steps.
4. **Run & verify locally** — `.env` + `python -m src.run`, seed reset,
   `send-test.sh`.
5. **Notes & tradeoffs** — launchd-era: ~5 min latency; no alerts while the
   Mac sleeps (wake catch-up: assignments recover, comments older than
   `LOOKBACK_MINUTES` drop); mention-search degradation; tuning env vars;
   short "why a local timer, not GitHub Actions cron" note (~1 run/hour story).
6. **Possible next steps** — kept (still accurate).

Dropped entirely: GH-repo setup steps, Actions cache notes, the trailing
"Workflow editor" URL section (config data in a public README) and the
"Jira_PAT" section (expiry already tracked in STATE.md and ONBOARDING).

README is public-facing prose → humanizer pass before delivery.

## Out of scope

- No changes to assignment/mention logic beyond the author skip.
- No new env vars, no test suite.
