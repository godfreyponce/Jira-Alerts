# Design: Teams toast formatting (#15)

Date: 2026-07-31
Status: approved by owner

## The constraint that drives everything

Teams builds the macOS notification banner from the chat message: HTML tags
stripped, first ~4 lines shown. There is no separate notification-text field.
So `<p>` breaks, bold, and links do nothing in the toast — its only structure
comes from **wording, order, and punctuation**. Any toast fix necessarily
changes the chat text too; the goal is to change it in ways the chat survives.

Owner's scope decision: fix the toast. The chat message is fine today, and the
chat reorder in §2 is accepted as the cost of getting comment text into the toast.

## What's wrong today

1. **Run-on.** Headlines carry no terminal punctuation, so the flattened toast
   reads as one sentence: `Tag, you're it RustConversion-4923 — Convert...`
2. **Redundancy.** Assignments say it twice (`Tag, you're it` +
   `This ticket is now on your plate`); mentions say `You were mentioned` *and*
   `Bob commented:`. Both burn the ~4-line budget.
3. **Summary hogs the front.** The flow renders `ticket — summary` second, ahead
   of `subline` and `snippet`, so a long summary pushes the comment text and the
   new-assignee line — the things worth reading — past the truncation point.

## 1. `src/cards.py` — `headline` becomes the lead sentence

`headline` stops being a short accent tag and becomes a complete sentence that
already names the ticket and ends in terminal punctuation. The ticket key then
comes *off* the summary line (§2) so it is never said twice.

| Alert | `headline` | `subline` | `snippet` |
|---|---|---|---|
| comment | `{author} commented on {ticket}:` | `""` | comment text |
| mention | `{author} mentioned you on {ticket}:` | `""` | comment text |
| assigned | `Tag, you're it — {ticket}.` | `""` | `""` |
| reassigned | `Not yours anymore :) {ticket}.` | `Now assigned to {who}.` / `Now unassigned.` | `""` |
| digest | `Update burst.` | `{parts}.` | boilerplate (unchanged) |

Per-function detail:

- **`comment_payload`** — headline picks the mention or plain wording off
  `c.mentions_me`; `subline` becomes `""` (its `"{author} commented:"` content
  moved into the headline). `snippet` unchanged.
- **`assigned_payload`** — `subline` drops entirely. `"This ticket is now on
  your plate"` said nothing `"Tag, you're it"` didn't.
- **`reassigned_payload`** — the colon goes (`Now assigned to: Jane` →
  `Now assigned to Jane.`) so it reads as a sentence when flattened. The
  `new_assignee is None` case becomes `Now unassigned.` rather than the
  awkward `Now assigned to Unassigned.` — the existing `or "Unassigned"`
  fallback is replaced by that branch.
- **`digest_payload`** — punctuation only: headline `Update burst` gains a
  period, and the joined `parts` subline gains one. Field roles are unchanged.

**Sanitization.** `headline` now interpolates a Jira-supplied author name, so
`_payload` must run it through `_sanitize` like the other text fields. The
inline `_sanitize(c.author)` in `comment_payload` then becomes redundant and
comes out. `_sanitize` leaves apostrophes alone, so `Tag, you're it` and
`Not yours anymore :)` survive it intact.

The module docstring's field contract is rewritten to match: `headline` as the
lead sentence, `subline` as an optional second sentence, and the flow's new
paragraph order.

## 2. Power Automate HTML — one line moved

```html
@{if(empty(triggerBody()?['headline']), '', concat('<p><strong>', triggerBody()?['headline'], '</strong></p>'))}
@{if(empty(triggerBody()?['subline']), '', concat('<p><strong>', triggerBody()?['subline'], '</strong></p>'))}
@{if(empty(triggerBody()?['snippet']), '', concat('<p>', triggerBody()?['snippet'], '</p>'))}
<p><strong>@{triggerBody()?['summary']}</strong></p>
<p><a href="@{triggerBody()?['url']}">Open Ticket #@{last(split(triggerBody()?['ticket'], '-'))}</a></p>
```

Two changes from today: the summary line moves from position 2 to position 4
(below `subline` and `snippet`), and `@{triggerBody()?['ticket']} — ` comes off
it. The `subline` and `snippet` lines are byte-identical to today's, just
shifted up. `ticket` is still sent — the Open link's `split()` needs it.

Ordering rule this encodes: **what happened → the one extra fact → the quoted
text → the ticket's own summary.** The summary is context, so it goes last of
the text blocks; everything ahead of it is news.

The headline's `if(empty(...))` guard is now dead (headline is always
populated) but stays as a cheap guard against a future empty string.

This is a flow-side edit in Power Automate; the repo can only document it.

## 3. Resulting toasts

Comment on a long-summary ticket:

```
Bob Smith commented on RustConversion-4923:
I think we should start with the parser module
before touching billing Migrate the entire
billing service off the legacy…
```

Assignment:

```
Tag, you're it — RustConversion-4923. Migrate
the entire billing service off the legacy
pipeline and document the rollback plan
```

Reassignment — the new owner now lands before the summary:

```
Not yours anymore :) RustConversion-4923. Now
assigned to Jane Chen. Migrate the entire
billing service off the legacy pipeline and…
```

Chat, comment: bold lead sentence → comment text → bold summary → Open link.

## 4. Docs and test script

- **`scripts/send-test.sh`** — the fake payload still uses the old field
  semantics. Rewrite its strings so the test renders a realistic new-contract
  shape: headline as a lead sentence naming `TEST-0000`, `subline` as a second
  sentence.
- **`docs/ONBOARDING.md` §4** — replace the HTML block, and rewrite the
  paragraph under it: the claim that "plain comments lead with the ticket line"
  becomes false once every alert carries a headline.
- **`docs/ONBOARDING.md` "Prefer the card look?"** — its Adaptive Card body
  renders `[@{ticket}](@{url}) @{summary}`, which duplicates the key now living
  in the headline, and orders its blocks the old way. Update it to stay coherent
  with the new contract.
- **`README.md`** — the one-line layout description ("bold headline, ticket key
  as a link, a short snippet") is stale in both order and detail. Refresh it.
- **`src/cards.py`** — module docstring, per §1.

## Not doing

- No summary length cap and no truncation logic — owner passed on it; macOS
  truncates, and the lead sentence is inside the budget regardless.
- No new payload fields and none removed. The contract stays six fields, so one
  flow covers every alert type.
- **Known wart, deliberately left alone:** the digest's link renders as
  `Open Ticket #Digest`, because `ticket` is the literal `"Digest"` and
  `split(…, '-')` finds no dash. Pre-existing and out of scope for #15.

## Verify

No test suite. Success is the owner reading a live banner.

1. `python -m py_compile src/*.py`
2. Apply the §2 flow edit in Power Automate, then `./scripts/send-test.sh` —
   expect HTTP 202 and a correctly ordered message in Teams.
3. A real `python -m src.run` cycle covering at least one comment alert and one
   assignment alert; owner confirms both toasts read cleanly.

Docs, `docs/HISTORY.md`, and `STATE.md` land after the owner accepts, per
`AGENTS.md`.
