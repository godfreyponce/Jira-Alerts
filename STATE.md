# JiraAlerts — Project State

Jira → Teams notifier. Python 3.12 + `requests`. A GitHub Actions cron polls Jira Data
Center every 5 min (`python -m src.run`) and DMs the owner in Microsoft Teams (Adaptive
Card via Power Automate webhook) on new comments, @mentions, and assignment changes.
Repo: github.com/godfreyponce/Jira-Alerts (PUBLIC).

*Thin snapshot — update continuously as work progresses. Per-feature detail: `docs/HISTORY.md`.
Work queue: GitHub Issues (`gh issue list`). Protocol: `AGENTS.md`.*

**Last updated: 2026-07-30**

## Now

- **Timer is launchd on the owner's Mac (2026-07-30, #10 closed)**: GitHub's scheduler
  delivered ~1 run/hour vs a nominal 12 despite healthy config, so the cron moved local.
  LaunchAgent `com.jiraalerts.poll` runs `scripts/run-local.sh` every 300 s
  (ProcessType Background); log: `~/Library/Logs/jiraalerts.log`. Cloud workflow is
  **disabled entirely** — that also kills the Actions "Run workflow" button; manual run =
  `./scripts/run-local.sh`. All three streams verified end-to-end on the new timer and
  owner-confirmed. #5 also closed today. Detail on both: `docs/HISTORY.md`.
- #9 (external cron → workflow_dispatch, e.g. Cloudflare Worker) stays open as the dormant
  fallback if alerts-while-the-Mac-sleeps ever matters.
- **Rollout prep**: #4 (`.env.example`) and #8 (`docs/ONBOARDING.md`) are **done and
  closed** (owner confirmed 2026-07-30). Still open: #7 test-card path and #6
  self-comment filter await green-light (#6 explicitly liked). #11 closed 2026-07-30:
  flow now posts a plain message (banner previews the alert; card layout dropped) —
  detail in `docs/HISTORY.md`.
  Shareable architecture explainer artifact exists (link with owner) — note it describes
  the GitHub-cron architecture and needs an update for the launchd model.
- README drift: setup step 2 tells you to bind the card to
  `triggerBody()?['attachments']?[0]?['content']`, but `cards.py` sends a flat payload
  with the layout living in the flow (#12). README also still describes the GH-cron era.

## Run / verify (do this first)

```bash
set -a; source .env; set +a   # .env is local-only (gitignored, real secrets — never commit/quote)
python -m src.run             # one polling cycle; first run seeds silently
```
No test suite — verify = a real run with live creds, or `python -m py_compile src/*.py`.

## Gotchas (short form)

- Jira PAT **expires 2027-01-16** — the notifier goes silent until a new one is set (repo
  secret `JIRA_PAT`).
- `state.json` is the app's dedup state (gitignored, lives locally now) — NOT related to
  STATE.md. Reset it to `{"initialized": false, "seen": {}}` to re-trigger the silent seed.
- No alerts while the Mac sleeps. On wake, launchd runs a catch-up cycle: assignment diffs
  recover fully; comments older than `LOOKBACK_MINUTES` (30) are dropped by design.
- @mention detection depends on Jira DC text-index tokenization; degrades gracefully if the
  server rejects text search.
- Assignment alerts never retry a failed send (the diff advances regardless) — only comment
  alerts retry.
- If ever reverting to the cloud cron (`gh workflow enable poll.yml`): its cached state is
  stale → it will silently re-seed; GitHub also pauses crons after 60 idle days.
