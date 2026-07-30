# JiraAlerts — Project State

Jira → Teams notifier. Python 3.12 + `requests`. A GitHub Actions cron polls Jira Data
Center every 5 min (`python -m src.run`) and DMs the owner in Microsoft Teams (Adaptive
Card via Power Automate webhook) on new comments, @mentions, and assignment changes.
Repo: github.com/godfreyponce/Jira-Alerts (PUBLIC).

*Thin snapshot — update continuously as work progresses. Per-feature detail: `docs/HISTORY.md`.
Work queue: GitHub Issues (`gh issue list`). Protocol: `AGENTS.md`.*

**Last updated: 2026-07-30**

## Now

- **#5 closed 2026-07-30**: comment narrowing + flood valve accepted — owner confirmed the
  TEST card and a real end-to-end "Assigned to you" card in Teams. Detail: `docs/HISTORY.md`.
- **Watch: cron scheduler resume.** No schedule-triggered run since re-enable (last one
  2026-06-30; today's runs were manual dispatches). The close-out push to main should
  re-register the schedule — confirm a `schedule`-event run appears in
  `gh run list --workflow=poll.yml` within ~30 min of the push; if not, that's a new issue.

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
