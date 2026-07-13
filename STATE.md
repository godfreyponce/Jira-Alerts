# JiraAlerts — Project State

Jira → Teams notifier. Python 3.12 + `requests`. A GitHub Actions cron polls Jira Data
Center every 5 min (`python -m src.run`) and DMs the owner in Microsoft Teams (Adaptive
Card via Power Automate webhook) on new comments, @mentions, and assignment changes.
Repo: github.com/godfreyponce/Jira-Alerts (PUBLIC).

*Thin snapshot — update continuously as work progresses. Per-feature detail: `docs/HISTORY.md`.
Work queue: GitHub Issues (`gh issue list`). Protocol: `AGENTS.md`.*

**Last updated: 2026-07-13**

## Now

- Nothing mid-flight. Session convention adopted 2026-07-13; README's "Possible next steps"
  are now GitHub Issues #1–#4 (none `ready-for-agent` yet — confirm with the owner first).
- v1 is live; the Actions cron (`.github/workflows/poll.yml`) is the production path.

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
