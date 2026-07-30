# JiraAlerts — Build History & Reference

*Created at convention adoption 2026-07-13. STATE.md is the thin quick-resume snapshot; per-feature detail accrues here as the owner accepts work. The work queue lives in GitHub Issues. v1 behavior, setup, and tradeoffs are documented in README.md.*

## 2026-07-30 — Real notification previews: flow switched to plain message (#11)

**What changed.** The Power Automate flow's action changed from "Post card in a chat
or channel" to "Post message in a chat or channel" (flow-side only — no repo code, no
webhook URL change). The message is HTML built from the same six payload fields; its
first line is `headline` with an `if(empty(...))` fallback to `subline`, so the Teams
notification banner now previews the actual alert ("Assigned to you — ABC-1234: …")
instead of the hardcoded "Sent a card". Tradeoff accepted: no card layout / Open
button; bold first line + hyperlink instead. ONBOARDING §4 now documents the
plain-message flow as the default, with the Adaptive Card layout kept as a
"prefer the card look?" alternative.

**Why.** The toast for cards posted via the "Post card" action is hardcoded by
Microsoft (open feature request: microsoft/AdaptiveCards#8647); the owner reads the
banner, not the chat, so the preview text was the whole point.

**Verification.** Test payload POSTed to the live webhook from the owner's Mac →
HTTP 202 → owner confirmed the banner shows the test headline in Teams, 2026-07-30.

## 2026-07-30 — Rollout docs: tracked .env.example + fork onboarding guide (#4 + #8, commits 5feaff5 + 1744e6d)

**What changed.** `.env.example` is now tracked, holding the five required vars with
placeholder values only (the repo is public), so README's `cp .env.example .env` step
finally works. `docs/ONBOARDING.md` is the from-scratch fork path for coworkers: PAT
creation, user-key discovery via `/rest/api/2/myself`, the Power Automate flow build
against the flat payload contract (with a starter card layout), local timer
(launchd plist template / cron line) recommended over fork Actions — whose gotchas
(cron lag, 60-day pause, ~7-day cache eviction → silent re-seed) are spelled out —
plus known quirks (#6 self-comments, no-retry assignment sends, silent PAT expiry).

**Notes.** Issue #8 predated the config change that derives `MENTION_TOKENS` from
`JIRA_USERNAME`/`JIRA_USER_KEY`, so the guide documents those two values instead of a
hand-picked token list. Writing the guide surfaced README drift (setup step 2's
card-binding expression contradicts `cards.py`'s flat contract) → filed as #12.

**Verification.** Docs-only, no code touched. Owner read the guide, edited voice
directly on GitHub (ba832f6), and confirmed both items 2026-07-30.

## 2026-07-30 — Timer moved to launchd on the owner's Mac (#10, commit e30a86a)

**What changed.** The polling timer is a macOS LaunchAgent
(`~/Library/LaunchAgents/com.jiraalerts.poll.plist`, not in the repo): every 300 s it runs
`scripts/run-local.sh`, which sources `.env` and runs one cycle; output appends to
`~/Library/Logs/jiraalerts.log`. `ProcessType Background` keeps it at the lowest scheduling
priority; the process lives ~15 s per tick and nothing stays resident. The GitHub workflow
was disabled entirely (which also disables `workflow_dispatch`; manual run =
`./scripts/run-local.sh`). Local `state.json` was reset for a silent re-seed at cutover.

**Why.** After the cron was re-enabled post-outage, GitHub's scheduler delivered roughly
one run per hour against a nominal twelve. Diagnostics cleared our side: workflow active,
poll.yml passed actionlint, no queued or stuck runs, githubstatus.com clean. Moving the
cron to off-peak minutes (`3-58/5`, c0218dd) produced zero scheduled runs in over an hour.
Scheduled events are best-effort and deprioritized; a notifier whose comment lookback is
30 minutes cannot tolerate hourly ticks (events age out of the window and are lost). The
owner has no NAS (#3 closed), so local launchd won over cloud alternatives: no new
credentials, no third-party service, punctual ticks. Accepted tradeoff: no alerts while
the Mac sleeps. Fallback if that ever matters: #9 (external cron → workflow_dispatch).

**Verification.** Seed run at load (silent, 42 assignments), second tick exactly 300 s
later delivered two real comment cards, third tick delivered a real "Reassigned →
Unassigned" card — all with no manual triggering, owner confirmed receipt in Teams.

## 2026-07-30 — Comment narrowing + per-cycle flood valve (#5, commit 50448a1)

**What changed.** Comment alerts now fire only for tickets *currently assigned* to the
owner (plus @mentions on any ticket, unchanged). Tickets merely watched, reported, or
once-assigned no longer trigger comment cards — they proved too noisy. Added
`MAX_CARDS_PER_CYCLE` (env-configurable, default 10): if one polling cycle wants more
cards than the cap, a single digest card is sent instead and the burst is suppressed.
Comment state still advances on digest, so a burst never replays; the digest card uses
the same Adaptive Card field contract, so no Power Automate flow change was needed.

**Why.** The 2026-07 flood incident (~42 cards in one burst, traced to local runs against
fresh state, not the cron) showed two gaps: comment scope was too broad, and nothing
bounded a single cycle's output.

**Verification.** Built during the Power Automate outage (2026-07-23 → 07-30), so
acceptance waited on the flow's return: `py_compile` clean and a live local run with the
narrowed JQL at build time; after the outage, webhook probe 202, TEST card confirmed in
Teams, and on 07-30 a real end-to-end card (new ticket assigned to owner → dispatch run
→ "Assigned to you" card delivered in Teams seconds after the run). Owner confirmed
receipt at 15:37 UTC.

**Caveat noted at close.** The GitHub Actions *scheduler* had not yet fired on its own
after the cron was re-enabled (last schedule-triggered run 2026-06-30); the acceptance
run was a manual `workflow_dispatch`. Pushing to main re-registers the schedule — the
close-out commit itself serves as that nudge.
