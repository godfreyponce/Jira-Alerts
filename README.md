# jira-teams-notifier

Polls **Jira Data Center** every 5 minutes and DMs you in **Microsoft Teams** when
someone comments on a ticket assigned to you, @mentions you anywhere, or assigns a
ticket to you (or takes one away). Alerts land as a plain Teams message with a
card-like layout — bold headline, ticket key as a link, a short snippet — via a
Power Automate webhook.

No Jira admin rights, no server: a timer on your own machine runs one polling cycle
every 5 minutes, authenticating as you with a Personal Access Token.

## How it works

```
launchd LaunchAgent (every 300 s)
        │
        ▼
scripts/run-local.sh ──► src/run.py ──► Jira REST API (Bearer PAT)
        │                   • assigned JQL: assignee = currentUser()
        │                   • mention JQL:  comment ~ your username
        │                   • per-issue comments classified; your own are skipped
        ▼
   dedup (state.json, a local gitignored file)
        │
        ▼
   flat JSON payload ──► Teams Workflows webhook ──► Power Automate flow ──► your chat
```

The Teams sink sits behind one function (`notifier.send`). If the webhook ever dies
(Microsoft churns this area, and it's tied to your organization's tenant), swapping
in ntfy / Discord / email is a one-file change. The message layout lives in the
Power Automate flow, not in Python — the script always sends the same six fields.

## Setup

The full walkthrough — Jira token, finding your user key, building the Power
Automate flow, picking a timer — is in [docs/ONBOARDING.md](docs/ONBOARDING.md).
Budget about 30 minutes. Nothing in it needs Jira admin rights.

## Run and verify locally

```bash
cp .env.example .env      # fill in real values
pip install -r requirements.txt
set -a; source .env; set +a
python -m src.run         # one polling cycle
```

The first run seeds silently: it records what it currently sees without notifying,
so you aren't flooded with backlog. Reset `state.json` to
`{"initialized": false, "seen": {}}` to re-trigger the seed. To check the Teams
half without waiting for a real Jira event, `./scripts/send-test.sh` fires a fake
alert at your webhook.

## Notes and tradeoffs

- **Why a local timer and not GitHub Actions cron?** This started on Actions.
  GitHub's scheduler is best-effort and delivered roughly one run per hour against
  a nominal twelve, so the cron moved to launchd on the owner's Mac. The workflow
  file is still in the repo as a fallback; ONBOARDING covers both options.
- **Latency is ~5 min**, not instant. Instant would need a Jira webhook (admin
  access) plus a public always-on listener. Polling avoids both.
- **No alerts while the machine sleeps.** On wake, the next cycle catches up:
  assignment changes are recovered fully; comments older than `LOOKBACK_MINUTES`
  (default 30) are dropped by design.
- **Mention-only tickets** (you're mentioned somewhere you've never touched) rely
  on Jira's `comment ~ username` text search, which depends on how the DC text
  index tokenizes. If your instance rejects it, the script degrades gracefully to
  the assigned-tickets set.
- **Tuning** via env vars: `LOOKBACK_MINUTES`, `PRUNE_DAYS`, `COMMENTS_PER_ISSUE`,
  `SNIPPET_CHARS`.

## Possible next steps

- Run the comment through the Anthropic API to generate a one-line summary instead
  of a raw snippet.
- Add a GitHub source (PR review-requests / @mentions) behind the same notifier.
