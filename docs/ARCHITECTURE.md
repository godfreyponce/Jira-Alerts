# Architecture

How one polling cycle works, and why it is shaped the way it is. Everything
here is written from the code in `src/`.

## The shape

619 lines of Python across six modules, one dependency (`requests`):

| File | Lines | Role |
|---|---|---|
| `run.py` | 152 | The cycle: collect, diff, send, save |
| `jira_client.py` | 213 | Talks to Jira DC, classifies comments |
| `cards.py` | 109 | Builds the flat payloads |
| `config.py` | 54 | Environment variables, tuning defaults |
| `state.py` | 69 | Dedup state, a local JSON file |
| `notifier.py` | 22 | POSTs to the Teams webhook |

Nothing stays resident. launchd starts a cycle every 300 seconds, the process
lives about 15 seconds, and the only thing that persists between runs is
`state.json`.

## One cycle, start to finish

1. **Load state.** `state.json` holds a seen-set of comment IDs and the set of
   tickets assigned to me as of last cycle. A missing or corrupt file becomes a
   clean first run rather than a crash.
2. **Collect comments.** Two JQL queries, unioned: `assignee = currentUser()`
   for my tickets, `comment ~ my username` for mentions anywhere. Every comment
   on a matched issue is classified; it is relevant if it sits on a
   currently-assigned ticket or its body contains a mention token. My own
   comments are always skipped. Tickets I merely watch or reported never
   trigger comment alerts; they proved too noisy.
3. **Diff assignments.** The current assigned set is compared against last
   cycle's. Newly present means "Tag, you're it". Newly absent gets one more
   look before alerting: a ticket that left the active set but is still mine
   (say, I closed it) is not a reassignment, so it stays silent. Diffing state
   instead of listening for events means a missed run never loses a change.
4. **The flood valve.** If everything above wants more than
   `MAX_CARDS_PER_CYCLE` cards (default 10), the cycle sends one digest card
   with the counts and suppresses the burst. State still advances, so the burst
   never replays. The valve exists because one early burst wanted about 42
   cards.
5. **Send and save.** Each alert POSTs to the webhook. A comment is only marked
   seen after its send succeeds, so failed comment alerts retry next cycle.
   Assignment alerts are fire-once. The seen-set is pruned to 30 days and
   state is written back.

The very first run does none of the sending: it seeds state silently with
everything it can see, because nobody wants their whole backlog delivered as
notifications.

## The six-field contract

Every alert kind sends the same flat payload: `ticket`, `summary`, `headline`,
`subline`, `snippet`, `url`. The message layout lives in the Power Automate
flow, which drops those fields into HTML; the Python side only ever sends data.
That split is what makes the wording editable without touching the flow, and
the flow editable without touching Python.

The macOS notification banner is the Teams message flattened: HTML stripped,
first few lines kept. So structure has to come from wording and punctuation,
not markup. `headline` is one complete sentence that already names the ticket
("Bob commented on ABC-1:"), and the ticket's own summary renders last, as
context rather than news. Interpolated values are sanitized (no quotes,
backslashes, or control characters) so a comment can never break the flow's
string literals.

## What Jira Data Center forced

- **Search uses GET, not POST.** On DC, `POST /search` can be rejected with a
  401 by an XSRF check even when the PAT is valid. The GET form takes JQL as a
  query parameter and is not subject to that check.
- **Mention search is best-effort.** `comment ~ username` depends on how the
  DC text index tokenizes. If the server rejects the query, the cycle degrades
  gracefully to the assigned-tickets set instead of failing.
- **Two identity values.** A mention can appear as `[~username]` or
  `[~accountid:userkey]`, so both the username and the internal user key are
  required, and both are checked when skipping my own comments.

## What Teams forced

The obvious approach, Power Automate's "Post card" action with an Adaptive
Card, hardcodes the notification banner to "Sent a card". That is a Microsoft
limitation of the action (open feature request: microsoft/AdaptiveCards#8647),
and the banner is the part I actually read. So the flow posts a plain HTML
message whose first line is the real headline. The card layout still exists in
ONBOARDING for anyone who prefers it.

## Why polling, and why a local timer

Instant delivery needs a Jira webhook, which needs admin rights, plus a public
always-on listener. Polling as my own user needs neither, at the cost of about
5 minutes of latency.

The timer started as GitHub Actions cron. After an outage it delivered roughly
one run per hour against a nominal twelve; scheduled workflows are best-effort
and get deprioritized. A notifier with a 30-minute comment lookback cannot
tolerate hourly ticks, events age out and are lost, so the timer moved to a
launchd LaunchAgent on my own Mac (`StartInterval` 300). The workflow file
stays in the repo as a fallback for machines that cannot run a local timer.
