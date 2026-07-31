# STATE.md's head names the ticket. Start there.

`STATE.md` opens with a YAML head. **`next_action` names the issue that is up now** — go straight
to it. Do not read the issue list and decide for yourself what's important; the owner has already
decided, and that is what the field is for. Below the head, STATE.md is a thin snapshot: what's
mid-flight, how to run/verify, and the gotchas that have already bitten. The full build archive
and per-feature detail live in `docs/HISTORY.md`; v1 behavior and tradeoffs are in `README.md`.

**The work queue is GitHub Issues** (`gh issue list`). The `ready-for-agent` label means the issue
has its four template sections filled in **and** the owner has green-lit it — that's the eligible
pool. `next_action` picks one out of it. A ticket also isn't ready unless it is **buildable in one
fresh session** inside the lean-window target — too big means split it before green-lighting.
Anything unlabeled still needs owner confirmation before starting. Reference issues in commits
(`refs #N`).

⚠️ **This repo is PUBLIC** (recruiter-visible). Write issues about features and architecture —
never env values, credentials, or the owner's personal data.

# One ticket = two sessions

Planning and building do not share a window. A context that has read the issue, explored the code,
and written a plan is a **poor context to then write the code in** — so the plan goes to a file and
a fresh session builds from it.

- **`/plan-ticket [#N]`** — read the ticket, write `docs/superpowers/plans/YYYY-MM-DD-issue-N.md`,
  stop. No code. The owner reads the plan (**gate 1** — cheap; nothing is built yet).
- `/clear`
- **`/build-ticket [#N]`** — build from the plan file, run the verification, **paste the real
  output**, stop before landing anything on main. Multi-task plans build on a ticket branch with
  one commit per approved task; single-task plans stay uncommitted in the working tree. The owner
  reads the diff (**gate 2**).
- On the owner's accept: land the code (merge the branch, or commit the working tree), then a
  docs commit; push both together, close the issue, `/clear`.

# STATE.md is written exactly once per ticket

**In the accept-time docs commit, after the owner accepts. Never mid-session.**

Continuous updates are what makes this file drift and bloat, because a session writes it from a
context already full of its own work, and it ends up recording things the owner never accepted.
One write, at the seam:

- **Mid-session discoveries never touch STATE.md** → `gh issue create` immediately. The issue queue
  is the capture buffer (write anytime, cheap); STATE.md is the accepted-state snapshot (write once).
  Nothing is lost if a session dies — the plan file, the branch, and the issue all outlive it.
- **Acceptance lands as code commits + one docs commit, pushed together**: the code first — the
  ticket branch's per-task commits merged, or a single `type(scope)` commit for single-task
  tickets — then one docs commit carrying `STATE.md` (Now cleared of the finished item,
  `next_action` advanced to the next ticket, `last_worked_on` bumped) and the feature's section
  in `docs/HISTORY.md`. Then close the issue.
- **"Now" holds unaccepted work only.** The moment the owner accepts something it moves to
  `docs/HISTORY.md`. Keep "Now" under ~6 lines. Gotchas stay in STATE.md — they're the memory that
  earns its place — but a gotcha lives there only while it would still bite an agent working today.

# Session hygiene — keep the window lean

Target **≤140k tokens of working context per session.** This works because state lives
OUTSIDE the conversation: `STATE.md` (snapshot), GitHub Issues (queue), `docs/HISTORY.md`
(archive). Suggest a fresh window at natural seams — phase acceptance, plan approval, deploy —
rather than letting a session balloon; a decision that lives only in conversation memory doesn't
exist, so write it to the right file the moment it's made.

# Verification scope

**There is no test suite.** Verifying a change means running the real thing.

- **While iterating**, the cheap gate is `python -m py_compile src/*.py` (or an import check).
  Config is env-var driven — `src/config.py`'s `_require()` exits clearly on a missing var.
- **At the end of `/build-ticket`**, once: `./scripts/send-test.sh` for the Teams path (expect
  HTTP 202), then a full `python -m src.run` cycle against live Jira. Paste the real output —
  but never paste a webhook URL, token, or the Jira hostname; the repo and the transcript are public.
- **The Teams message layout is not in this repo.** It lives in the owner's Power Automate flow,
  and only the owner can edit it. A green `send-test.sh` proves the webhook works, not that a
  layout change landed.
- **Stop what you started.** The launchd timer (`com.jiraalerts.poll`) runs on its own; if you
  unload it to test something, load it back before ending the session.

---

# Project

Jira → Microsoft Teams notifier. Python 3.12, single dependency (`requests`). Polls Jira
Data Center for new comments on worked-on tickets, @mentions, and assignment changes; DMs the
owner in Teams via a Power Automate webhook. No always-on server.

## Run locally

```bash
set -a; source .env; set +a   # .env is local-only (gitignored, real secrets)
python -m src.run             # one polling cycle
```

First run seeds silently. Reset `state.json` to `{"initialized": false, "seen": {}}` to
re-trigger the seed.

## Production

A launchd LaunchAgent (`com.jiraalerts.poll`) on the owner's Mac runs `scripts/run-local.sh`
every 300 s; log at `~/Library/Logs/jiraalerts.log`. The GitHub Actions cron
(`.github/workflows/poll.yml`) is **disabled** — kept only as a documented fallback.

## Two files that are never committed

- **`.env`** — real secrets, gitignored. Never commit it or quote its values anywhere.
- **`state.json`** — the app's dedup state, gitignored. Unrelated to `STATE.md` despite the name.
