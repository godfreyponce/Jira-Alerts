# Setting this up for yourself (fork-based)

This walks you from zero → getting Jira alerts in your own Teams chat. You need a
Jira Data Center account, Microsoft Teams with Power Automate, a GitHub account, and
about 30 minutes. Nothing here requires Jira admin rights.

Each person runs their own copy: your fork, your Jira token, your Teams webhook. No
shared infrastructure, and nobody can see anyone else's tickets.

## 1. Fork and clone

Fork the repo on GitHub, then:

```bash
git clone https://github.com/<you>/Jira-Alerts.git
cd Jira-Alerts
```

Python 3.12+ and the `requests` package are the only runtime needs
(`pip install -r requirements.txt`).

## 2. Create a Jira Personal Access Token

Jira → your avatar → **Profile → Personal Access Tokens → Create token**. Name it, set
an expiry, copy the token. Write the expiry date somewhere you'll see it — when the
token dies, the notifier goes silent with no error you'll ever notice.

## 3. Find your username and user key

Your username is what you log in with. Your user key is internal and non-obvious; the
easiest way to get it is to ask Jira who you are:

```bash
curl -s -H "Authorization: Bearer <your-PAT>" \
  https://jira.example.com/rest/api/2/myself
```

In the JSON response, `name` is your `JIRA_USERNAME` and `key` (something like
`JIRAUSER12345`) is your `JIRA_USER_KEY`.

Both matter for @mention detection: the script treats a comment as mentioning you if
it contains `[~your-username]` or `[~accountid:your-user-key]`, and it builds those
tokens from these two values. Get either one wrong and mentions silently stop matching.

## 4. Build the Power Automate flow

The Python script does not talk to Teams directly. It POSTs a flat JSON payload to a
webhook, and a Power Automate flow you own turns that into a Teams DM. The script
always sends the same six fields — `ticket`, `summary`, `headline`, `subline`,
`snippet`, `url` — so one flow covers every alert type.

1. Go to [make.powerautomate.com](https://make.powerautomate.com) → **Create** →
   **Instant cloud flow** → skip → add the trigger
   **"When a Teams webhook request is received"**. Set *Who can trigger the flow* to
   **Anyone** (the URL itself is the secret — treat it like a password).
2. Add the action **"Post message in a chat or channel"**. Post as **Flow bot**, post
   in **Chat with Flow bot**, recipient: your own email.
3. In the **Message** box, switch to code view (the `</>` toggle) and paste:

```html
@{if(empty(triggerBody()?['headline']), '', concat('<p><strong>', triggerBody()?['headline'], '</strong></p>'))}
@{if(empty(triggerBody()?['subline']), '', concat('<p><strong>', triggerBody()?['subline'], '</strong></p>'))}
@{if(empty(triggerBody()?['snippet']), '', concat('<p>', triggerBody()?['snippet'], '</p>'))}
<p><strong>@{triggerBody()?['summary']}</strong></p>
<p><a href="@{triggerBody()?['url']}">Open Ticket #@{last(split(triggerBody()?['ticket'], '-'))}</a></p>
```

   The notification banner is this message with the HTML stripped and only the first few
   lines kept, so every alert leads with `headline` — one complete sentence that already
   names the ticket. `subline` and `snippet` follow, and the ticket's own summary comes
   last: it's context rather than news, and a long one up top would push the comment text
   out of the banner entirely. The `concat(...)` lines emit their paragraph only when the
   field has content, so empty fields don't render blank gaps. The last line is the
   message's only hyperlink, standing in for the card's Open button.

4. Save the flow and copy the **HTTP POST URL** from the trigger. That's your
   `TEAMS_WEBHOOK_URL`.

### Make the wording your own

The text and the layout live in different places:

- **What the alerts say** — the headlines and sublines are plain strings in
  `src/cards.py` (`comment_payload`, `assigned_payload`, `reassigned_payload`).
  This repo ships with "Tag, you're it" for new assignments and
  "Not yours anymore :)" for reassignments; edit those strings to taste. No flow
  changes needed — the flow just displays whatever the script sends.
- **How the message looks** — the HTML you pasted in step 3. Edit it in the flow;
  the script never needs to change.

### Prefer the card look?

Use the action **"Post card in a chat or channel"** instead, and paste an Adaptive
Card layout into the **Adaptive Card** field, using the same
`@{triggerBody()?['field']}` tokens:

```json
{
  "type": "AdaptiveCard",
  "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
  "version": "1.4",
  "body": [
    { "type": "TextBlock", "text": "@{triggerBody()?['headline']}",
      "wrap": true, "weight": "Bolder" },
    { "type": "TextBlock", "text": "@{triggerBody()?['subline']}",
      "wrap": true, "weight": "Bolder" },
    { "type": "TextBlock", "text": "@{triggerBody()?['snippet']}", "wrap": true },
    { "type": "TextBlock", "text": "@{triggerBody()?['summary']}",
      "wrap": true, "isSubtle": true }
  ],
  "actions": [
    { "type": "Action.OpenUrl", "title": "Open in Jira", "url": "@{triggerBody()?['url']}" }
  ]
}
```

The catch: card notifications always read "Sent a card" — a Microsoft limitation of
the action, nothing you or the payload can change. That's why the plain message above
is the default here.

## 5. Configure and do a first run

```bash
cp .env.example .env      # fill in the five values from steps 2-4
set -a; source .env; set +a
python -m src.run
```

The first run seeds silently: it records every comment and assignment it currently
sees without notifying, so you don't get flooded with backlog. It prints something
like `Initialized: seeded N comment(s) and M current assignment(s)`.

To confirm the webhook and flow work, run `./scripts/send-test.sh` — it fires a fake
alert at your webhook and prints the HTTP status (expect 202, and a "Test alert"
message in your Teams chat a moment later).

To confirm the whole pipeline including Jira, comment on a ticket assigned to you (or
have someone @mention you), wait a moment, and run `python -m src.run` again.

If you ever want to re-seed from scratch, reset `state.json` to
`{"initialized": false, "seen": {}}`.

## 6. Pick a timer

The script is one polling cycle; something has to run it every 5 minutes. Two options.

### Option A: a timer on your own machine (recommended)

This is what the repo owner runs. I originally used GitHub's scheduler and it
delivered roughly one run per hour against a nominal twelve, scheduled workflows are
best-effort and get deprioritized. A local timer ticks on time.

On a Mac, save this as `~/Library/LaunchAgents/com.jiraalerts.poll.plist`, replacing
the two `/Users/you/...` paths:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jiraalerts.poll</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/you/path/to/Jira-Alerts/scripts/run-local.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>ProcessType</key>
    <string>Background</string>
    <key>StandardOutPath</key>
    <string>/Users/you/Library/Logs/jiraalerts.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/you/Library/Logs/jiraalerts.log</string>
</dict>
</plist>
```

Then `launchctl load ~/Library/LaunchAgents/com.jiraalerts.poll.plist`. Check
`~/Library/Logs/jiraalerts.log` after 5 minutes to see cycles completing.

On Linux, a crontab line does the same job (`scripts/run-local.sh` is a zsh script,
so make sure zsh is installed):

```
*/5 * * * * /path/to/Jira-Alerts/scripts/run-local.sh >> $HOME/jiraalerts.log 2>&1
```

The tradeoff: no alerts while your machine is asleep or off. On wake, the next cycle
catches up, assignment changes are recovered fully, comments older than 30 minutes
(`LOOKBACK_MINUTES`) are dropped by design.

### Option B: GitHub Actions cron on your fork

Works from anywhere, including while your machine sleeps, but comes with the
scheduling problem above plus fork-specific gotchas. If you're on Windows or can't
leave a machine running, it's still the practical choice.

Setup: on your fork, go to the **Actions** tab and enable workflows (forks have them
disabled by default), then enable the `poll` workflow. In
**Settings → Secrets and variables → Actions** add:

- Secrets: `JIRA_PAT`, `TEAMS_WEBHOOK_URL`
- Variables: `JIRA_BASE_URL`, `JIRA_USERNAME`, `JIRA_USER_KEY`

Know what you're signing up for:

- **Cron lag.** Scheduled runs are best-effort. Expect delays, sometimes severe ones.
- **60-day pause.** GitHub disables the schedule after 60 days without repo activity.
  Any commit re-arms it.
- **Cache eviction.** Dedup state persists in the Actions cache, which GitHub evicts
  after ~7 days without use. After eviction the next run re-seeds silently — you miss
  whatever happened in between, with no error.

## Known quirks

- Assignment alerts fire once and never retry a failed send; comment alerts do retry.
- When the PAT expires, everything goes quiet with no warning. Set a calendar
  reminder for the expiry date you wrote down in step 2.
