# Sales Pace Command Center — Operating Spec

This file is the persistent contract for any agent or human working on this system.
Read it before changing anything.

## Mission
A daily standup-ready revenue command center. Every session must preserve the ability
to answer, in under 30 seconds of reading:
1. Are we on track? 2. What changed since yesterday? 3. What changed since last Friday?
4. Which source produced each metric? 5. What is stale, missing, or contradictory?

## Canonical rules (do not relitigate)
- **$10M is the operating target.** $20M is upside scoreboard only — never daily status.
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
- Commit e3093d1 ready on `claude/beautiful-fermi-of0to7`; push blocked pending
  write access for the Claude GitHub app.

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

## Leverage reminder
This system is instrumentation (~3/10 revenue leverage). It exists to point the daily
standup at the actual leverage: the discovery→proposal chokepoint and the no-next-step
deal list in Deal Risk Signals. Do not gold-plate the dashboard.
