---
glass: jiraalerts
status: in-progress
last_worked_on: 2026-07-31
next_action: "#15 — Teams toast formatting. Design is approved and committed at docs/superpowers/specs/2026-07-31-toast-formatting-design.md; the ticket carries the four sections. Next step is /plan-ticket 15 in a fresh window — no code yet."
blocked_on: ""
phase: "v1 shipped and onboarding-ready. #4-#8 and #10-#14 closed and owner-accepted (see docs/HISTORY.md): .env.example, docs/ONBOARDING.md, send-test.sh, plain card-like Teams message, self-comment filter, launchd-era README, author-var cleanup, explainer artifact. Timer moved off the GitHub Actions cron to a local launchd LaunchAgent 2026-07-30 (#10) after the cloud scheduler delivered ~1 run/hour against a nominal 12. #15 toast formatting designed 2026-07-31, not built. Ticket protocol bootstrapped from ~/Developer/docs/ticket-protocol-template.md 2026-07-31."
---

# JiraAlerts — Project State

Jira → Teams notifier. Python 3.12 + `requests`. A launchd timer on the owner's Mac polls Jira
Data Center every 5 min (`scripts/run-local.sh` → `python -m src.run`) and DMs the owner in
Microsoft Teams (plain message, card-like layout, via a Power Automate webhook) on new comments,
@mentions, and assignment changes. Repo: github.com/godfreyponce/Jira-Alerts (**PUBLIC**).

*Thin snapshot, written once per ticket at accept time. Per-feature detail: `docs/HISTORY.md`.
Work queue: GitHub Issues (`gh issue list`). Protocol: `AGENTS.md`.*

## Now

- **#15 Teams toast formatting** — design approved, nothing built. The macOS banner is the flattened
  first ~4 lines of the chat message, so the fix is wording/order/punctuation, not markup.
- **#9** (external cron → `workflow_dispatch`) is a dormant fallback for alerts-while-the-Mac-sleeps;
  **#1** (Anthropic-summarized comments) and **#2** (GitHub notification source) are backlog. All
  three are unlabeled — they need owner green-light before anyone starts.

## Run / verify (do this first)

```bash
set -a; source .env; set +a   # .env is local-only (gitignored, real secrets — never commit/quote)
python -m src.run             # one polling cycle; first run seeds silently
```

No test suite — verify = `python -m py_compile src/*.py`, then `./scripts/send-test.sh` (expect
HTTP 202) and a real cycle. Production is the LaunchAgent `com.jiraalerts.poll` (every 300 s);
log at `~/Library/Logs/jiraalerts.log`; manual run = `./scripts/run-local.sh`.

## Gotchas (short form)

- Jira PAT **expires 2027-01-16** — the notifier goes silent until a new one is set in the local
  `.env` (`JIRA_PAT`; also the Actions repo secret if the cloud fallback is ever revived).
- **The Teams message layout is not in this repo.** It lives in the owner's Power Automate flow;
  only the owner can edit it. `send-test.sh` proves the webhook, not the layout.
- `state.json` is the app's dedup state (gitignored, local) — NOT this file. Reset it to
  `{"initialized": false, "seen": {}}` to re-trigger the silent seed.
- No alerts while the Mac sleeps. On wake, launchd runs a catch-up cycle: assignment diffs recover
  fully; comments older than `LOOKBACK_MINUTES` (30) are dropped by design.
- @mention detection depends on Jira DC text-index tokenization; degrades gracefully if the server
  rejects text search.
- Assignment alerts never retry a failed send (the diff advances regardless) — only comment alerts retry.
- If ever reverting to the cloud cron (`gh workflow enable poll.yml`): its cached state is stale →
  it will silently re-seed; GitHub also pauses crons after 60 idle days.
