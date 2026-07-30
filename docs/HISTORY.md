# JiraAlerts — Build History & Reference

*Created at convention adoption 2026-07-13. STATE.md is the thin quick-resume snapshot; per-feature detail accrues here as the owner accepts work. The work queue lives in GitHub Issues. v1 behavior, setup, and tradeoffs are documented in README.md.*

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
