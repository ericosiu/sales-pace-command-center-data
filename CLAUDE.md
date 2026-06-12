# Sales Pace Command Center — Operating Spec

This file is the persistent contract for any agent or human working on this system.
Read it before changing anything.

## Mission
A daily standup-ready revenue command center. Every session must preserve the ability
to answer, in under 30 seconds of reading:
1. Are we on track? 2. What changed since yesterday? 3. What changed since last Friday?
4. Which source produced each metric? 5. What is stale, missing, or contradictory?

## Canonical rules (do not relitigate)
- **$10M is the operating target and drives all status pills.** $20M stretch gaps may
  appear in the daily topline as clearly labeled columns (rule amended by Eric
  2026-06-12) but never determine status.
- **Canonical pace = Q2+Q3 linear** (target × complete-days / 183 over
  2026-04-01..2026-09-30; Eric 2026-06-12). Calendar-year pace is deprecated.
- **Headline "booked" = CRM Q2+Q3 closed-won** (`daily.actual_revenue`). The untraced
  $1.20M figure is retired (Eric 2026-06-12).
- **Deck generation contract lives in DECK_SPEC.md** — the Mac deck session must fetch
  the live JSONs, never regenerate numbers from session memory.
- **HubSpot CRM is canonical** for forecast, revenue, pipeline, and risk counts.
  When a live CRM read disagrees with the Google Sheet snapshot, CRM wins and the
  disagreement gets flagged, not silently resolved.
- **Closed-won period = Q2+Q3 2026** (closedate 2026-04-01..2026-09-30). Verified 2026-06-11.
- **Capacity model is recovery potential**, not attainment, until backed by weighted CRM.
- **Open deal = `hs_is_closed = false`.** Any other definition must be reconciled to this.
- Zero vs zero is "No activity / no movement", never "stable/better".

## Design principles (non-negotiable)
1. **Data cleanliness over features.** A number without a source + timestamp does not ship.
   Stale, blocked, or contradictory values are flagged inline (`data_quality_flags`,
   `source-map.json` contradictions) — never deleted, never silently carried as fresh.
2. **Readable in 30 seconds.** Gap first, deltas vs yesterday and vs last Friday next,
   flags last. No metric appears without its day-over-day direction.
3. **Diffs must be real.** change-log.json distinguishes genuine day/week movement from
   carried baseline values. A carried value is labeled "carried", never shown as a diff.
4. **No PII.** Aggregates only. No client names, raw CRM records, Slack text, or secrets
   in this repo — it is served publicly via GitHub Pages.
5. **Additive schema only.** The V1 UI reads these JSONs; never rename or remove fields.

## Current state (2026-06-11)
- daily/weekly/source-map/change-log refreshed and live-verified against HubSpot
  (read-only MCP aggregates). Forecast $1,992,000; gap −$8,008,000; OFF TRACK.
- Write access granted 2026-06-11; branch `claude/beautiful-fermi-of0to7` pushed.
  Pages serves from `main` — verified data goes live when this branch merges.

## Open items toward production (in order)
1. Push pending commit once write access is granted; confirm Pages/Vercel pickup.
2. Ingest Hermes handoff: Vercel project, deploy repo, UI data-fetch URL.
3. Resolve flagged contradiction: $804K open-pipeline / 20-deal drop on Jun 10-11
   (only $38K explained by closed-lost). Untrusted until explained.
4. Replace dead sheet Actuals Log with approved HubSpot stage mapping for
   proposals/discoveries (log already missed a real $15K close in week of Jun 1-7).
5. Weekday auto-refresh (GitHub Action with read-only HubSpot key as repo secret,
   or scheduled Claude session).
6. Gong/Granola connectors (signals currently carried from sheet, flagged stale);
   `hs_latest_meeting_activity` is hidden in the portal — unhide or drop the metric.

## Pipeline scoping (discovered 2026-06-11, live CRM)
Portal-wide aggregates mix four pipelines and mislead. Per-pipeline open deals:
Enterprise 27 / $2,616,000 (18 missing next step); Karrot ABM 105 / $162,000
(101 missing next step — automation noise); Upsell 4 / $534,000; Single Brain
6 / $100,000. Hygiene and risk metrics MUST be reported per-pipeline; the
working set that matters is Enterprise + SB + Upsell (~$3.25M), not the
headline 142/128 counts.

## Presentation spec (2026-06-11)
Eric's 13-slide standup deck (uploads/0a0cebab-20260611dailystandup_1.html) is the
target layout: topline current/target/gap table, named owner + due date on every
action, what-one-close-costs funnel, required-vs-actual lanes, first-touch SLA,
gray "not wired" pills for uninstrumented metrics. Its DATA is unverified —
known conflicts vs CRM: closed-won $1.20M (CRM: $824.6K CY2026 / $401.6K Q2+Q3),
"zero deals created 6/10" (CRM: 4 / $270K), ACV $180K (sheet-approved ASP: $100K).
Lead-level slides contain client names → private deploy only, NEVER this repo.

## Reconciliation decisions (Eric, 2026-06-11)
1. **Operating view = Enterprise + Single Brain + Upsell.** Karrot ABM is shown as a
   separate labeled automation lane, never blended into hygiene or status counts.
2. **Canonical ACV = $180K.** NOTE: the sheet's assumption cell still says $100K
   ("approved ASP") — sheet is now inconsistent with this decision and its capacity
   model math is stale until Eric updates the cell (agents are read-only on Sheets).
   All required-cadence math in the dashboard uses $180K.
3. The 13-slide deck was generated by Fable 5 in a Claude Code session. Its layout is
   the presentation spec; its DATA remains unverified — $1.20M closed-won and the
   MQL/SAL/SQL lead-stage numbers are still untraced to any reachable source and must
   show as "not wired" until traced.

## Leverage reminder
This system is instrumentation (~3/10 revenue leverage). It exists to point the daily
standup at the actual leverage: the discovery→proposal chokepoint and the no-next-step
deal list in Deal Risk Signals. Do not gold-plate the dashboard.
