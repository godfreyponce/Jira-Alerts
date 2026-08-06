# JiraAlerts Build History & Reference

*Created at convention adoption 2026-07-13. STATE.md is the thin quick-resume snapshot; per-feature detail accrues here as the owner accepts work. The work queue lives in GitHub Issues. v1 behavior, setup, and tradeoffs are documented in README.md.*

## 2026-07-31 · Teams toast formatting: headline as lead sentence (#15)

**What changed (repo side, `src/cards.py`).** `headline` is now a complete sentence that
names the ticket and ends in terminal punctuation, and it carries what `subline` used to
say. Comments read `Doe, John commented on ABC-1:` (`mentioned you on` when it's an
@mention) with an empty `subline`; assignments read `Tag, you're it — ABC-1.` and drop
their `subline` entirely, since "This ticket is now on your plate" said nothing the
headline didn't and cost a line of the four-line banner budget; reassignments read
`Not yours anymore :) ABC-1.` plus `Now assigned to Jane.`, with `Now unassigned.` as its
own wording instead of the old "Now assigned to: Unassigned"; the digest gained terminal
periods. `_payload` now sanitizes `headline` too (it interpolates a Jira-supplied author
name), and the inline `_sanitize(c.author)` went. The six-field contract is unchanged, so
`src/run.py`, `src/notifier.py`, and `src/jira_client.py` were untouched.

**What changed (owner side, the Power Automate flow).** The summary moved from position 2
to position 4, and the `@{ticket} — ` prefix came off it because the headline names the
ticket now. Docs carrying that HTML were updated to match: ONBOARDING §4 (the block, the
paragraph under it, and the Adaptive Card body), the README layout line, and the
`cards.py` module docstring.

**Why.** The macOS banner is the chat message flattened (HTML stripped, first ~4 lines
kept), and there is no separate notification field, so wording, order, and punctuation are
the only levers. A long summary sitting in position 2 pushed the comment text out of the
banner completely. Full reasoning:
`docs/superpowers/specs/2026-07-31-toast-formatting-design.md`; plan:
`docs/superpowers/plans/2026-07-31-issue-15.md`.

**Verification.** `py_compile` clean. A payload dump across all six alert shapes matched
the design's strings character for character, including the sanitizer proof: an author
name containing double quotes renders as `'Bobby'`. A live `python3 -m src.run` cycle ran
clean but quiet (0 notifications), so it proved the code runs, not the wording. After the
owner applied the flow edit: `send-test.sh` returned 202 and the banner showed the new
order, then assigned / reassigned / mention payloads generated from `cards.py` were fired
live and confirmed in macOS notifications by the owner.

**Accepted limits.** The Open link cannot be given its own banner line: the toast flattens
all HTML, so no markup lever exists. The owner accepted this at close. No summary length
cap or truncation (explicitly passed on). The digest's `Open Ticket #Digest` link is still
broken, pre-existing and out of scope.

**Process note.** First ticket built under the `AGENTS.md` two-session protocol
(`/plan-ticket` → `/clear` → `/build-ticket`) and the first to use a ticket branch,
`ticket/15-toast-formatting`, with one commit per task.

## 2026-07-31 · Explainer artifact rewritten for the launchd model (#14)

The shareable "How JiraAlerts works" artifact (link is with the owner; findable via the
Artifact list as "How JiraAlerts works") was rewritten in place (same URL, same visual
design). Content changes: pipeline stage 1 is now the launchd LaunchAgent instead of a
GitHub Actions runner; `state.json` described as a local file; the Teams stage is the
flat six-field payload → Power Automate flow → plain card-like message (#11); the
self-comment skip (#6) is mentioned; the timing bar dropped the GitHub-scheduler-lag
column and gained the sleep/catch-up tradeoff note; setup steps now mirror
ONBOARDING (.env, `send-test.sh`, local timer, Actions cron as fallback). Also fixed a
pre-existing dark-mode bug: the page set its ground color only on `html`, so in dark
theme the platform's light body background showed through under near-white text; the
background is now set on `body` too.

## 2026-07-30 · Self-comment filter + README refresh (#6 + #12, commits ec51a57 + 2cd6c72)

**What changed (#6).** `collect_relevant_comments()` now skips any comment whose author
matches `JIRA_USERNAME` or `JIRA_USER_KEY`, the same identity check the assignment diff
uses. The guard sits before the mention check, so a self-@mention is skipped too.
Decided tradeoff: no escape hatch (an `ALERT_ON_SELF` env var was considered and
rejected), which retires self-commenting as the one-person end-to-end test.
`send-test.sh` covers the Teams half; the full pipeline needs a real event. The
"self-comments alert you" known-quirk bullet was removed from ONBOARDING (the #8 entry
below still lists it as it stood then). Review follow-up #13 (reuse the new `author`
var at the `RelevantComment` construction site; fixes a latent crash on a null author)
landed 2026-07-31 in commit 2c1cb09 and closed.

**What changed (#12).** README rewritten as a launchd-era overview: what it is, updated
flow diagram, run/verify basics, tradeoffs (including the why-not-Actions story), with
all setup delegated to `docs/ONBOARDING.md`, so setup instructions now live in exactly
one file. Dropped: the card-binding step that contradicted `cards.py`'s flat payload
(the drift that spawned this issue), GH-repo/Actions setup, and the trailing
workflow-editor URL and PAT-expiry stubs (operational detail that didn't belong in a
public README).

**Verification.** `py_compile` + import clean; README claims checked against source
(payload fields, env var names, JQL, 300 s interval) during review. Live check on the
launchd timer: owner confirmed 2026-07-30.

## 2026-07-30 · send-test.sh: verify the Teams flow without a real Jira event (#7, commit c3989d3)

**What changed.** `scripts/send-test.sh` sources `.env` and POSTs a fake alert payload
(`TEST-0000`, all six fields populated) to the Teams webhook, printing the HTTP status
(expect 202). ONBOARDING step 5 now points first-time setups at it, so coworkers can
verify their Power Automate flow before waiting on a real Jira event.

**Verification.** Ran live against the owner's webhook: 202 returned, "Test alert"
message received in Teams, owner confirmed 2026-07-30.

## 2026-07-30 · Real notification previews: flow switched to plain message (#11)

**What changed.** The Power Automate flow's action changed from "Post card in a chat
or channel" to "Post message in a chat or channel" (flow-side only: no repo code, no
webhook URL change). The message is HTML built from the same six payload fields; its
first line is `headline` with an `if(empty(...))` fallback to `subline`, so the Teams
notification banner now previews the actual alert ("Assigned to you — ABC-1234: …")
instead of the hardcoded "Sent a card". Tradeoff accepted: no real card / Open
button. The layout was then polished to mirror the old card (owner confirmed both
shapes 2026-07-30): bold headline line, bold ticket-link and summary on one line, conditional
subline/snippet paragraphs via `concat()` (so empty fields render no blank gaps), and
an "Open <ticket>" hyperlink standing in for the button. ONBOARDING §4 documents the
plain-message flow as the default, with the Adaptive Card layout kept as a
"prefer the card look?" alternative.

**Why.** The toast for cards posted via the "Post card" action is hardcoded by
Microsoft (open feature request: microsoft/AdaptiveCards#8647); the owner reads the
banner, not the chat, so the preview text was the whole point.

**Verification.** Test payload POSTed to the live webhook from the owner's Mac →
HTTP 202 → owner confirmed the banner shows the test headline in Teams, 2026-07-30.

## 2026-07-30 · Rollout docs: tracked .env.example + fork onboarding guide (#4 + #8, commits 5feaff5 + 1744e6d)

**What changed.** `.env.example` is now tracked, holding the five required vars with
placeholder values only (the repo is public), so README's `cp .env.example .env` step
finally works. `docs/ONBOARDING.md` is the from-scratch fork path for coworkers: PAT
creation, user-key discovery via `/rest/api/2/myself`, the Power Automate flow build
against the flat payload contract (with a starter card layout), local timer
(launchd plist template / cron line) recommended over fork Actions, whose gotchas
(cron lag, 60-day pause, ~7-day cache eviction → silent re-seed) are spelled out,
plus known quirks (#6 self-comments, no-retry assignment sends, silent PAT expiry).

**Notes.** Issue #8 predated the config change that derives `MENTION_TOKENS` from
`JIRA_USERNAME`/`JIRA_USER_KEY`, so the guide documents those two values instead of a
hand-picked token list. Writing the guide surfaced README drift (setup step 2's
card-binding expression contradicts `cards.py`'s flat contract) → filed as #12.

**Verification.** Docs-only, no code touched. Owner read the guide, edited voice
directly on GitHub (ba832f6), and confirmed both items 2026-07-30.

## 2026-07-30 · Timer moved to launchd on the owner's Mac (#10, commit e30a86a)

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
Unassigned" card. All three ran with no manual triggering, and the owner confirmed
receipt in Teams.

## 2026-07-30 · Comment narrowing + per-cycle flood valve (#5, commit 50448a1)

**What changed.** Comment alerts now fire only for tickets *currently assigned* to the
owner (plus @mentions on any ticket, unchanged). Tickets merely watched, reported, or
once-assigned no longer trigger comment cards: they proved too noisy. Added
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
run was a manual `workflow_dispatch`. Pushing to main re-registers the schedule, and the
close-out commit itself serves as that nudge.
