# DECK SPEC — Daily Standup Deck Generator Contract

Audience: the Claude Code session on Eric's Mac that generates the daily standup
deck (the 13/14-section HTML). Read this whole file before generating. The repo's
CLAUDE.md rules apply too; where they conflict, this file is newer (2026-06-12).

## Step 0 — Fetch the verified data FIRST
Every number on slides 1, 2, 7, and 9 must come from these endpoints, not from
session memory, prior decks, or local estimates:

    https://ericosiu.github.io/sales-pace-command-center-data/daily.json
    https://ericosiu.github.io/sales-pace-command-center-data/weekly.json
    https://ericosiu.github.io/sales-pace-command-center-data/source-map.json
    https://ericosiu.github.io/sales-pace-command-center-data/change-log.json

(Or read the same four files from a local clone of ericosiu/sales-pace-command-center-data.)
If `generated_at_utc` is older than the last weekday 13:05 UTC, say so on the deck
("data as of <timestamp>") rather than regenerating numbers yourself.

## Field mapping (deck ← daily.json)
| Deck element | Field | Notes |
|---|---|---|
| Booked / closed-won headline | `actual_revenue` | **$401,600 as of Jun 12. The $1.20M figure is RETIRED (Eric 2026-06-12) — never show it.** |
| Forecast / revenue attainment | `crm_forecast` | closed-won + weighted open, CRM-canonical |
| Gap to $10M | `gap_to_target` | |
| Behind-pace-by ($10M) | `pace_gap` | Canonical pace = Q2+Q3 linear (`pace_convention`). Calendar-year pace is deprecated — do not use 44.7%-of-year math. |
| Target-to-date mark | `target_to_date` | |
| $20M stretch columns | `upside.*` | ALLOWED in daily topline (rule amended by Eric 2026-06-12) but must be labeled "stretch" and never drive a status pill. Status keys off $10M only. |
| Weighted pipeline / coverage numerator | `weighted_pipeline` (portal) or `pipelines.operating_view` for the SG+SB view — say which you used | |
| Open deals / hygiene universe | `pipelines.*` | Use per-pipeline counts. Never portal-wide 142/128-style counts without the ABM split. Keep ONE deal-count universe per deck — no 14-vs-18 drift between header and body. |
| No-next-step list size | `pipelines.operating_view.open_missing_next_step` | |
| Closes / revenue this wk vs last | weekly.json `weekly_summary.closed_won_deals`, `.revenue_booked` | CRM-verified |
| What changed | change-log.json `daily_diff` / `weekly_diff` | values marked "carried" are NOT diffs |

## Things the data layer does NOT have (show as "not wired" gray pills)
- MQL / SAL / SQL lead-stage counts and conversion rates — until their source is
  traced and wired, label every funnel number "session-derived · not yet verified".
- Gong call discipline (no connector). First-touch SLA numbers from local analysis
  are fine but must carry their n= and "derived" labels (the Jun 12 deck did this well).

## Hard rules
1. Lead-level content (client names, lead cards, engagement-by-lead) NEVER goes in
   the public data repo and only ships in the private/protected deploy.
2. Every derived or assumed number is labeled `derived` / `assumed` inline.
3. If a deck number disagrees with daily.json, the deck is wrong by definition —
   fix the deck or flag the discrepancy on the slide; never ship it silently.
4. Self-check before output: booked == actual_revenue; behind-pace == pace_gap;
   one open-deal universe; $20M columns labeled stretch.

## Current canonical constants (2026-06-12)
ACV $180K · SB pilot $15K · closed-won period Q2+Q3 2026 · operating pipelines =
Enterprise + Single Brain + Upsell · pace = Q2+Q3 linear · status target $10M.
