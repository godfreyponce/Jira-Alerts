# JiraAlerts — Project State

Jira → Teams notifier. Python 3.12 + `requests`. A launchd timer on the owner's Mac
polls Jira Data Center every 5 min (`scripts/run-local.sh` → `python -m src.run`) and
DMs the owner in Microsoft Teams (plain message, card-like layout, via a Power Automate
webhook) on new comments, @mentions, and assignment changes.
Repo: github.com/godfreyponce/Jira-Alerts (PUBLIC).

*Thin snapshot — update continuously as work progresses. Per-feature detail: `docs/HISTORY.md`.
Work queue: GitHub Issues (`gh issue list`). Protocol: `AGENTS.md`.*

**Last updated: 2026-07-31**

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
- **Rollout prep**: #4 (`.env.example`), #8 (`docs/ONBOARDING.md`), #7
  (`scripts/send-test.sh`), and #11 all **done and closed** (owner confirmed
  2026-07-30). The flow now posts a plain message with a card-like layout — banner
  previews the alert; detail in `docs/HISTORY.md`. Guide is coworker-ready.
- **#6 and #12 done and closed (owner confirmed 2026-07-30)**: comments you author
  yourself no longer alert, and the README is now a launchd-era overview that delegates
  all setup to `docs/ONBOARDING.md` (the stale card-binding step is gone). Detail:
  `docs/HISTORY.md`.
- **#13 done and closed (owner confirmed 2026-07-31)**: the `RelevantComment`
  construction site reuses the comment loop's `author` var — duplicated lookup gone,
  latent null-author crash gone. Noted in the #6 entry in `docs/HISTORY.md`.
- **#14 done and closed (owner confirmed 2026-07-31)**: the "How JiraAlerts works"
  explainer artifact now describes the launchd model (same URL and visual design;
  dark-mode background bug also fixed). Detail: `docs/HISTORY.md`. Queue is now just
  #9, the dormant cloud-fallback contingency.

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
