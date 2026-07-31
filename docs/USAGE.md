# Day-to-day usage

Running cycles by hand, reading the output, tuning, and the quirks that have
already bitten. Setup from zero is [ONBOARDING.md](ONBOARDING.md); how the
pieces fit is [ARCHITECTURE.md](ARCHITECTURE.md).

## Run one cycle by hand

```bash
set -a; source .env; set +a
python -m src.run
```

The script is a single polling cycle, not a daemon: it queries Jira, sends
whatever is new, saves state, and exits in about 15 seconds. The console prints
one line per decision, so a cycle's output reads like a receipt:

```
Comment alert: ABC-123 456789 (mention)
Assigned alert: ABC-130
Reassigned alert: ABC-101 -> Jane Doe
Cycle complete: 3 notification(s), 7 comment(s) scanned, 12 assigned to you.
```

## The first run seeds silently

A fresh `state.json` means the first cycle records every comment and assignment
it can currently see without sending anything, then prints:

```
Initialized: seeded N comment(s) and M current assignment(s) without notifying.
```

That is deliberate: without the seed, the first poll would flood you with your
entire backlog. To re-seed from scratch, reset `state.json` to
`{"initialized": false, "seen": {}}`.

## Test the Teams half without Jira

```bash
./scripts/send-test.sh
```

Fires a fake alert at your webhook and prints the HTTP status. Expect 202, and
a "Test alert" message in your Teams chat a moment later. To test the whole
pipeline including Jira, comment on a ticket assigned to you (or have someone
@mention you) and run a cycle.

## Watch the timer

The launchd setup in ONBOARDING logs every cycle to
`~/Library/Logs/jiraalerts.log`. If alerts stop, that file is the first place
to look: cycles still completing means Jira and the webhook are fine and the
problem is upstream (nothing happened, or the PAT expired, see below).

## Tuning

All optional, all environment variables, defaults in `src/config.py`:

| Variable | Default | What it does |
|---|---|---|
| `LOOKBACK_MINUTES` | 30 | How far back the comment JQL looks. Keep it comfortably larger than the timer interval so overlapping windows never leave a gap; dedup prevents repeats. |
| `PRUNE_DAYS` | 30 | Remembered comment IDs older than this are dropped so `state.json` stays small. |
| `COMMENTS_PER_ISSUE` | 20 | Max comments inspected per issue per cycle, most recent first. |
| `SNIPPET_CHARS` | 280 | Comment snippet length in the alert. |
| `MAX_CARDS_PER_CYCLE` | 10 | The flood valve: a cycle wanting more cards than this sends one digest instead. |
| `STATE_PATH` | `state.json` | Where dedup state lives. |

## Known quirks

- Assignment alerts fire once and never retry a failed send. Comment alerts do
  retry: a comment stays unseen until its send succeeds.
- When the PAT expires, everything goes quiet with no error you will ever see.
  Write the expiry date down when you create the token and set a reminder.
- The GitHub Actions fallback (`.github/workflows/poll.yml`, ONBOARDING option
  B) keeps state in the Actions cache, which GitHub evicts after about 7 days
  without use. After eviction the next run re-seeds silently and you miss
  whatever happened in between.

## Possible next steps

- Run the comment through the Anthropic API to generate a one-line summary
  instead of a raw snippet.
- Add a GitHub source (PR review-requests and @mentions) behind the same
  notifier.
