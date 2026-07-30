# Self-Comment Filter (#6) + README Refresh (#12) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop alerting the owner about their own comments, and rewrite the README as a launchd-era overview that delegates all setup to `docs/ONBOARDING.md`.

**Architecture:** #6 is a guard clause in the per-comment loop of `collect_relevant_comments()` using the same identity check `fetch_assignees()` already uses. #12 replaces the README body; no code involved.

**Tech Stack:** Python 3.12, `requests` only. No test suite — verify via `python -m py_compile src/*.py` and real runs.

## Global Constraints

- Repo is PUBLIC (recruiter-visible): no env values, credentials, or personal data in any file. Jira URL stays sanitized as `jira.example.com`.
- Commit convention from history: feature commits use `refs #N`; issues are closed only after the owner confirms (per AGENTS.md).
- No new env vars (owner rejected the `ALERT_ON_SELF` escape hatch).
- README is human-facing prose → humanizer skill pass before finalizing.

---

### Task 1: Self-comment filter (#6)

**Files:**
- Modify: `src/jira_client.py` (per-comment loop, currently lines 121–136; module docstring lines 11–14)
- Modify: `docs/ONBOARDING.md` (Known quirks, first bullet)

**Interfaces:**
- Consumes: `config.JIRA_USERNAME`, `config.JIRA_USER_KEY` (already imported via `from . import config`)
- Produces: no signature changes; `collect_relevant_comments()` simply returns fewer results.

- [ ] **Step 1: Add the guard clause**

In `src/jira_client.py`, inside `collect_relevant_comments()`, at the top of the `for c in _comments(key):` loop body (before `body = ...`), insert:

```python
            author = c.get("author", {}) or {}
            if (
                author.get("name") == config.JIRA_USERNAME
                or author.get("key") == config.JIRA_USER_KEY
            ):
                continue  # your own comments are noise, not news (#6)
```

Note: `author` here shadows nothing; the dataclass field is set from `displayName` further down and is unaffected. Self-authored comments are skipped even when they contain a mention token — that ordering (guard before the mention check) is intentional.

- [ ] **Step 2: Update the module docstring**

In the same file's module docstring, after the sentence ending "do NOT trigger comment alerts (they proved too noisy).", add:

```
Comments you authored yourself are always skipped — you don't need a DM
about your own words.
```

- [ ] **Step 3: Verify it compiles and imports**

Run: `python -m py_compile src/*.py && python -c "from src.jira_client import collect_relevant_comments"`
Expected: no output, exit 0.

- [ ] **Step 4: Remove the stale Known quirk from ONBOARDING**

In `docs/ONBOARDING.md` → "Known quirks", delete this bullet (it documents the pre-fix behavior and references #6):

```
- Comments **you** write on your own tickets currently alert you too (a filter is
  planned, tracked in issue #6).
```

- [ ] **Step 5: Live verification**

Comment on a ticket currently assigned to the owner, then run:

```bash
set -a; source .env; set +a
python -m src.run
```

Expected: the cycle completes normally and **no** Teams DM arrives for that comment. (If no owned ticket is handy for commenting, note that in the report and rely on Steps 3 + code review; the launchd timer will exercise it within minutes anyway.)

- [ ] **Step 6: Commit**

```bash
git add src/jira_client.py docs/ONBOARDING.md
git commit -m "feat: skip comment alerts authored by the owner (refs #6)"
```

---

### Task 2: README refresh (#12)

**Files:**
- Modify: `README.md` (full-body replacement)

**Interfaces:**
- Consumes: nothing from Task 1 except one diagram line noting self-authored comments are skipped (if Task 1 somehow didn't land, drop that parenthetical).
- Produces: nothing downstream.

- [ ] **Step 1: Replace README.md with the draft below**

````markdown
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
````

Everything currently in README.md after the title is replaced by the above. Notably dropped, per the approved spec: the card-binding setup step (contradicted `cards.py`), GH-repo setup steps and Actions cache notes, the "Workflow editor" URL section, and the "Jira_PAT" expiry section.

- [ ] **Step 2: Humanizer pass**

Invoke the `humanizer` skill (`~/.claude/skills/humanizer`) on the new README and apply its edits. (If executing as a subagent without skill access, flag this step as pending for the main session instead of skipping it silently.)

- [ ] **Step 3: Sanity-check the links and claims**

Run: `ls docs/ONBOARDING.md scripts/send-test.sh scripts/run-local.sh .env.example`
Expected: all four exist (every file the README references).

Confirm the README nowhere mentions: the card-binding expression `triggerBody()?['attachments']`, Actions secrets setup, the real Jira hostname, or the webhook URL.

- [ ] **Step 4: Commit**

```bash
git add README.md
git commit -m "docs: README refresh for the launchd era, setup delegated to ONBOARDING (refs #12)"
```

---

## After both tasks (main session, not a task)

Per AGENTS.md: wait for owner confirmation, then close #6 and #12, refresh STATE.md's "Now" section, add detail sections to `docs/HISTORY.md`, and commit those together.
