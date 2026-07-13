# Read STATE.md first, then check the issue queue

`STATE.md` is a **thin snapshot** of right-now state: what's mid-flight, how to run/verify,
and the gotchas that have already bitten. Read it before doing anything. Per-feature detail
lives in `docs/HISTORY.md`; v1 behavior and tradeoffs are in `README.md`.

**The work queue is GitHub Issues** (`gh issue list`). The `ready-for-agent` label means the
owner has green-lit that item; anything unlabeled still needs owner confirmation before
starting. Reference issues in commits (`fixes #N`) so they close automatically.
⚠️ This repo is PUBLIC (recruiter-visible): write issues about features and architecture —
never env values, credentials, or the owner's personal data. The local `.env` holds real
secrets (gitignored) — never commit it or quote its values anywhere. `state.json` is the
app's dedup state (gitignored), unrelated to STATE.md — never commit it either.

**Keep state current as you work, not as an end-of-session dump:**
- Update STATE.md's "Now" section when what's mid-flight changes; keep the file under ~40 lines.
- New work discovered mid-session → `gh issue create` immediately; don't let it live only in conversation.
- After a feature is built **and the owner confirms it's good**: close its issue, refresh
  STATE.md, add the feature's detail section to `docs/HISTORY.md`, and commit them alongside
  the feature. Don't record work the owner hasn't accepted yet.

# Session hygiene — keep the window lean (owner rule, 2026-07-12)

Target **≤140k tokens of working context per session.** This works because state lives
OUTSIDE the conversation: `STATE.md` (snapshot), GitHub Issues (queue), `docs/HISTORY.md`
(archive). Suggest a fresh window at natural seams — phase acceptance, plan approval,
deploy — rather than letting a session balloon; a decision that lives only in conversation
memory doesn't exist, so write it to the right file the moment it's made.

# Project rules

## Project
Jira → Microsoft Teams notifier. Python 3.12, single dependency (`requests`). Polls Jira
Data Center for new comments on worked-on tickets, @mentions, and assignment changes; DMs
the owner in Teams via a Power Automate webhook (Adaptive Cards). No always-on server.

## Run locally
```bash
set -a; source .env; set +a   # .env is local-only (gitignored, real secrets)
python -m src.run             # one polling cycle
```
First run seeds silently. Reset `state.json` to `{"initialized": false, "seen": {}}` to
re-trigger the seed.

## Production
GitHub Actions cron (`.github/workflows/poll.yml`) runs the same entrypoint every 5 minutes.
Secrets/vars live in the repo's Actions settings; dedup state persists via the Actions cache.

## Verification
There is NO test suite. Verifying a change means a real run with live creds from `.env`,
or at minimum `python -m py_compile src/*.py` / an import check. Config is env-var driven
(`src/config.py` `_require()` exits clearly on missing vars).
