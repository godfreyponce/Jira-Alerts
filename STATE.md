---
glass: jiraalerts
status: in-progress
last_worked_on: 2026-08-06
next_action: "No feature ticket is green-lit. #9 (external cron → workflow_dispatch), #1 (Anthropic-summarized comments), and #2 (GitHub notification source) are all unlabeled; none may be started until the owner adds ready-for-agent. Do not pick one yourself. What IS actionable is two pieces of bookkeeping left by PR #16, both described under Now: (a) write the missing docs/HISTORY.md entry for #16, reconstructable from its PR body and diff, then let the owner review it; (b) delete the merged readme-refresh branch from the remote. Neither is a blocker, both are safe, and (b) needs nothing but a confirmation. If the owner has since green-lit a ticket, that ticket wins over both."
blocked_on: "Feature work only: no open issue carries ready-for-agent, so the queue needs owner triage before any of #9, #1, or #2 can start. The two #16 cleanups are not blocked."
phase: "v1 shipped, onboarding-ready, alert wording settled, and the repo is now recruiter-facing. #4-#8 and #10-#15 closed and owner-accepted (see docs/HISTORY.md): .env.example, docs/ONBOARDING.md, send-test.sh, plain card-like Teams message, self-comment filter, launchd-era README, author-var cleanup, explainer artifact, toast formatting. Timer moved off the GitHub Actions cron to a local launchd LaunchAgent 2026-07-30 (#10) after the cloud scheduler delivered ~1 run/hour against a nominal 12. Ticket protocol bootstrapped from ~/Developer/docs/ticket-protocol-template.md 2026-07-31; #15 was the first ticket built under it and the first to use a ticket branch. PR #16 (merged 2026-08-06, built in a parallel session with no backing issue) rewrote README as a first-person recruiter front door and added docs/USAGE.md, docs/ARCHITECTURE.md, a site/index.html Pages one-pager, docs/media screenshots and a demo clip, and .github/workflows/pages.yml. Reader-facing prose went em-dash-free the same day. Nothing is queued — every open issue awaits owner green-light."
---

# JiraAlerts — Project State

Jira → Teams notifier. Python 3.12 + `requests`. A launchd timer on the owner's Mac polls Jira
Data Center every 5 min (`scripts/run-local.sh` → `python -m src.run`) and DMs the owner in
Microsoft Teams (plain message, card-like layout, via a Power Automate webhook) on new comments,
@mentions, and assignment changes. Repo: github.com/godfreyponce/Jira-Alerts (**PUBLIC**).

*Thin snapshot, written once per ticket at accept time. Per-feature detail: `docs/HISTORY.md`.
Work queue: GitHub Issues (`gh issue list`). Protocol: `AGENTS.md`.*

## Docs map (six surfaces now — edit the right one)

- `README.md` — recruiter front door. First person, media-heavy. **Not** the Pages site.
- `site/index.html` — the Pages one-pager for non-technical visitors. Deploys on its own.
- `docs/ONBOARDING.md` — fork-and-set-up walkthrough for someone standing their own copy up.
- `docs/USAGE.md` — day-to-day running, reading output, tuning, quirks.
- `docs/ARCHITECTURE.md` — how one cycle works and why it is shaped that way.
- `docs/HISTORY.md` — per-feature build archive. Protocol itself: `AGENTS.md`.

## Now

- Nothing in flight. **#9** (external cron → `workflow_dispatch`) is a dormant fallback for alerts-while-the-Mac-sleeps;
  **#1** (Anthropic-summarized comments) and **#2** (GitHub notification source) are backlog. All
  three are unlabeled — they need owner green-light before anyone starts.
- **PR #16 has no `docs/HISTORY.md` entry.** It was built in a parallel session and bypassed the
  ticket protocol, so the archive has a hole where the biggest docs change in the repo should be.
  Reconstructable without guesswork: `gh pr view 16` for the intent, `git show 12e3db5 --stat` for
  the surface. Follow the file's shape (What changed / Why / Verification, middot heading, no em
  dashes) and file it under 2026-08-06 above the entry this session wrote.
- **The merged `readme-refresh` branch is still on the remote.** `git push origin --delete
  readme-refresh` once the owner confirms; it is fully merged into main, so nothing is lost.

## Run / verify (do this first)

```bash
set -a; source .env; set +a   # .env is local-only (gitignored, real secrets — never commit/quote)
python -m src.run             # one polling cycle; first run seeds silently
```

No test suite — verify = `python -m py_compile src/*.py`, then `./scripts/send-test.sh` (expect
HTTP 202) and a real cycle. Production is the LaunchAgent `com.jiraalerts.poll` (every 300 s);
log at `~/Library/Logs/jiraalerts.log`; manual run = `./scripts/run-local.sh`.

Docs-only changes need none of that. The Pages site is a separate pipeline:
`.github/workflows/pages.yml` publishes `site/` on pushes touching `site/**`, `docs/media/**`,
or the workflow itself (`gh run list --workflow=pages.yml` to check).

## Gotchas (short form)

- Jira PAT **expires 2027-01-16** — the notifier goes silent until a new one is set in the local
  `.env` (`JIRA_PAT`; also the Actions repo secret if the cloud fallback is ever revived).
- **The Teams message layout is not in this repo.** It lives in the owner's Power Automate flow;
  only the owner can edit it. `send-test.sh` proves the webhook, not the layout.
- **The macOS banner is the chat message flattened** — HTML stripped, first ~4 lines kept, no
  separate notification field. Line breaks and markup do not survive into it, so banner layout
  (e.g. putting the Open link on its own line) is not achievable from either the repo or the flow.
  Wording, order, and punctuation are the only levers (#15).
- `state.json` is the app's dedup state (gitignored, local) — NOT this file. Reset it to
  `{"initialized": false, "seen": {}}` to re-trigger the silent seed.
- No alerts while the Mac sleeps. On wake, launchd runs a catch-up cycle: assignment diffs recover
  fully; comments older than `LOOKBACK_MINUTES` (30) are dropped by design.
- @mention detection depends on Jira DC text-index tokenization; degrades gracefully if the server
  rejects text search.
- Assignment alerts never retry a failed send (the diff advances regardless) — only comment alerts retry.
- If ever reverting to the cloud cron (`gh workflow enable poll.yml`): its cached state is stale →
  it will silently re-seed; GitHub also pauses crons after 60 idle days.
- **`git pull` before starting.** Work has landed on main from a parallel Claude session and
  from direct edits on GitHub. On 2026-08-06 that cost a rejected push and a rebase when PR #16
  rewrote README mid-session. Check `git log origin/main` before planning anything.
- **GitHub Pages serves `site/index.html`, not `README.md`.** It moved there in #16; editing the
  README changes nothing on godfreyponce.github.io, and the deploy only fires on the paths above.
- **Reader-facing docs are em-dash-free** (`README.md`, `docs/ONBOARDING.md`, `docs/HISTORY.md`,
  `docs/ARCHITECTURE.md`, `docs/USAGE.md`, `site/index.html`, as of 2026-08-06); do not
  reintroduce them there. Agent-facing files (this one, `AGENTS.md`, `.claude/commands/`, plans
  and specs) and the `src/cards.py` alert strings deliberately keep theirs, so the em dashes
  still in HISTORY are all verbatim quotes of those strings.
