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

- **Nothing mid-flight; queue is empty except #9** (external cron → `workflow_dispatch`,
  e.g. Cloudflare Worker) — dormant fallback if alerts-while-the-Mac-sleeps ever
  matters. Don't start it without owner green-light.
- **Timer is launchd on the owner's Mac (2026-07-30, #10)**: GitHub's scheduler was
  delivering ~1 run/hour vs a nominal 12, so the cron moved local. LaunchAgent
  `com.jiraalerts.poll` runs `scripts/run-local.sh` every 300 s; log:
  `~/Library/Logs/jiraalerts.log`. Cloud workflow **disabled entirely** (no Actions
  "Run workflow" button); manual run = `./scripts/run-local.sh`.
- **Onboarding-ready, all owner-confirmed**: #4–#8, #10–#14 closed — `.env.example`,
  `docs/ONBOARDING.md`, `send-test.sh`, plain card-like Teams message, self-comment
  filter, launchd-era README, author-var cleanup, and the "How JiraAlerts works"
  explainer artifact (rewritten for the launchd model, dark-mode bug fixed).
  Per-feature detail: `docs/HISTORY.md`.

## Run / verify (do this first)

```bash
set -a; source .env; set +a   # .env is local-only (gitignored, real secrets — never commit/quote)
python -m src.run             # one polling cycle; first run seeds silently
```
No test suite — verify = a real run with live creds, or `python -m py_compile src/*.py`.

## Gotchas (short form)

- Jira PAT **expires 2027-01-16** — the notifier goes silent until a new one is set in
  the local `.env` (`JIRA_PAT`; also the Actions repo secret if the cloud fallback is
  ever revived).
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
