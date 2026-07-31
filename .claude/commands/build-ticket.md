---
description: Build a ticket from its plan file, prove it runs, and stop before landing anything on main.
argument-hint: "[#N] (optional — defaults to STATE.md's next_action)"
---

Build one ticket from its plan file. **Start from the plan, not from a conversation you weren't in.**

## Which ticket

`$ARGUMENTS` names the issue if set; otherwise read `next_action` from STATE.md's YAML head.
Load `docs/superpowers/plans/*-issue-N.md`. If no plan file exists, stop — run `/plan-ticket N`
first. Building without the plan is exactly the failure this split exists to prevent.

## Build it

1. Use the `superpowers:executing-plans` skill. Follow the plan task by task.
2. If the plan has more than one task, create a ticket branch and commit each task once its
   review passes (`type(scope): summary (refs #N)` per commit). Single-task plans stay
   uncommitted in the working tree. Either way, nothing touches main before gate 2.
3. Where the plan turns out to be wrong, **say so** rather than quietly improvising around it —
   a deviation the owner never sees is a deviation they can't catch at review.

## Prove it

There is no test suite. **Paste the real output**, never a claim about it:

```bash
python -m py_compile src/*.py            # syntax gate, cheap, run it always
./scripts/send-test.sh                   # Teams path — expect HTTP 202
set -a; source .env; set +a
python -m src.run                        # one real cycle against live Jira
```

`send-test.sh` and `python -m src.run` both hit live services with the owner's real credentials.
Run them, but do not paste anything they print that contains a webhook URL, a token, or the
owner's Jira hostname — this repo is public and so is the transcript.

If the ticket changed the alert's appearance, the flow edit in Power Automate is the owner's to
make. Say so plainly and give them the exact HTML; a green `send-test.sh` against an unedited
flow proves the webhook works, not that the layout changed.

## Then stop — before landing anything on main

Show the owner the diff (the ticket branch, or the working tree) and wait. Do not merge or
commit to main, do not push, do not close the issue.

## Only after the owner accepts

Code commits + one docs commit, pushed together:

- **the code** — merge the ticket branch's per-task commits, or for a single-task plan commit
  the working tree as one `type(scope): summary (refs #N)` commit,
- **then one docs commit** — `STATE.md` (clear the finished item out of `## Now`, advance
  `next_action` to the next ticket — ask the owner which if it isn't obvious — bump
  `last_worked_on`) together with the feature's section in `docs/HISTORY.md`.

Then push, close the issue with a one-line result, and tell the owner to `/clear` before the
next ticket.

This is STATE.md's **only** write moment. Anything you discovered along the way that isn't this
ticket goes to `gh issue create`, not into STATE.md.
