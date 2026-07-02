# jira-teams-notifier

Polls **Jira Data Center** (`jira.example.com`) every 5 minutes and DMs you in
**Microsoft Teams** when there's a new comment on a ticket you've worked on, or a
comment that @mentions you. Notifications arrive as an Adaptive Card (ticket key
as a clickable link, summary, author, and a short snippet) via a Power Automate
Workflows webhook.

No Jira admin and no always-on server required: it runs on GitHub Actions cron
and authenticates as you with a Personal Access Token.

## How it works

```
GitHub Actions (every 5 min)
        │
        ▼
   src/run.py ──► Jira REST API (Bearer PAT)
        │            • worked-on JQL: assignee was / reporter / watcher
        │            • mention JQL:   comment ~ your username
        │            • per-issue comments, classified
        ▼
   dedup (state.json, cached between runs by GitHub Actions)
        │
        ▼
   Adaptive Card ──► Teams Workflows webhook ──► your chat
```

The sink is deliberately behind one function (`notifier.send`). If the Teams
webhook ever dies (Microsoft churns this area, and it's tied to the organization's tenant),
swapping in ntfy / Discord / email is a one-file change.

## One-time setup

### 1. Generate a Jira Personal Access Token
Jira → your avatar → **Profile → Personal Access Tokens → Create token**. Name it,
set an expiry (write the date down — it dies silently when it expires), copy it.

### 2. Point the Workflows flow at the payload
In Power Automate, open your flow → **Edit** → the **Post card in a chat or channel**
action → **Adaptive Card** field → clear it → insert this expression (fx):

```
triggerBody()?['attachments']?[0]?['content']
```

Save. (This is the flat single-step flow — no For-each, so it's just the trigger
body, not `item()`.)

### 3. Create the GitHub repo
Push this folder to a **private** repo. Then in repo **Settings → Secrets and
variables → Actions**:

**Secrets** (encrypted):
- `JIRA_PAT` — the token from step 1
- `TEAMS_WEBHOOK_URL` — your Workflows webhook URL

**Variables** (not secret):
- `JIRA_BASE_URL` = `https://jira.example.com`
- `JIRA_USERNAME` = `your-jira-username`
- `JIRA_USER_KEY` = `JIRAUSER00000`

### 4. First run
Actions tab → run the workflow manually (**Run workflow**). The **first run seeds
silently** — it records every comment it currently sees without notifying, so you
don't get flooded with the backlog. From then on, only genuinely new comments are
sent. Comment in a test ticket (or have someone mention you) to confirm the card
lands.

## Local testing
```bash
cp .env.example .env      # fill in real values
pip install -r requirements.txt
set -a; source .env; set +a
python -m src.run
```
Delete `state.json`'s contents back to `{"initialized": false, "seen": {}}` to
re-trigger the silent seed.

## Notes & tradeoffs
- **Latency is ~5 min**, not instant. Instant would need a Jira webhook (admin
  access you don't have) + a public always-on listener. Polling avoids both.
- **state.json is persisted via the GitHub Actions cache** (not committed to git),
  so the repo stays free of ticket-activity data.
- **Mention-only tickets** (you're mentioned on a ticket you've never touched)
  rely on the `comment ~ username` text search, which depends on how the DC text
  index tokenizes. Most mentions are also caught by the worked-on query. If the
  text search is rejected by your instance, the script degrades gracefully and
  just uses the worked-on set.
- **Tuning** via env vars: `LOOKBACK_MINUTES`, `PRUNE_DAYS`, `COMMENTS_PER_ISSUE`,
  `SNIPPET_CHARS`.

## Possible next steps
- Run the comment through the Anthropic API to generate a one-line summary
  instead of a raw snippet (you already have the key + stack).
- Add a GitHub source (PR review-requests / @mentions) behind the same notifier.
- Move off GH Actions cron to a systemd timer on your NAS (swap state.json for a
  tiny store; everything else is unchanged).


## Workflow editor
- https://your-power-automate-webhook-url

## Jira_PAT
- Expires on January 16, 2027 (will go silent until I make a new one)
- GitHub pauses the cron after 60 days of zero repo activity, any commit resets it.
