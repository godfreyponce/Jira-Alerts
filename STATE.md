# JiraAlerts — Project State

Jira → Teams notifier. Python 3.12 + `requests`. A GitHub Actions cron polls Jira Data
Center every 5 min (`python -m src.run`) and DMs the owner in Microsoft Teams (Adaptive
Card via Power Automate webhook) on new comments, @mentions, and assignment changes.
Repo: github.com/godfreyponce/Jira-Alerts (PUBLIC).

*Thin snapshot — update continuously as work progresses. Per-feature detail: `docs/HISTORY.md`.
Work queue: GitHub Issues (`gh issue list`). Protocol: `AGENTS.md`.*

**Last updated: 2026-07-30**

## Now

- **Fully live in production (2026-07-30)**: #5 closed (comment narrowing + flood valve
  accepted; detail in `docs/HISTORY.md`). The scheduler resumed after the close-out push
  (it had been dormant since 06-30 — a push to main was indeed the fix), and the first
  scheduled run at 16:01 UTC verified all three alert streams in one cycle: comment,
  assigned, and reassigned cards all delivered. Nothing mid-flight; queue is in Issues.
- **Watch: offset cron (c0218dd)** moved the schedule to off-peak minutes (:03,:08,…) after
  scheduler lag left 20–30 min gaps. Awaiting the first scheduled runs at the new cadence;
  an owner comment on an assigned ticket is pending as the hands-off verification. If lag
  persists, #3 (NAS systemd timer) is the durable fix.
- **Rollout prep queued**: #8 onboarding guide (+#4 .env.example), #7 test-card dispatch,
  #6 self-comment filter — all awaiting owner green-light. Shareable architecture
  explainer artifact exists (link with owner).

## Run / verify (do this first)

```bash
set -a; source .env; set +a   # .env is local-only (gitignored, real secrets — never commit/quote)
python -m src.run             # one polling cycle; first run seeds silently
```
No test suite — verify = a real run with live creds, or `python -m py_compile src/*.py`.

## Gotchas (short form)

- Jira PAT **expires 2027-01-16** — the notifier goes silent until a new one is set (repo
  secret `JIRA_PAT`).
- GitHub pauses the Actions cron after 60 days of zero repo activity; any commit resets it.
- `state.json` is the app's dedup state (gitignored) — NOT related to STATE.md. Reset it to
  `{"initialized": false, "seen": {}}` to re-trigger the silent seed.
- README's `cp .env.example .env` step is broken — `.env.example` doesn't exist yet (#4).
- @mention detection depends on Jira DC text-index tokenization; degrades gracefully if the
  server rejects text search.
- Actions cache evicts after ~7 idle days → next cloud run silently re-seeds; events during
  the gap are dropped by design. Assignment alerts also never retry a failed send (the diff
  advances regardless) — only comment alerts retry.
