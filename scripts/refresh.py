#!/usr/bin/env python3
"""
Sales Pace Command Center — weekday refresh.

Replicates the CRM-canonical verification layer:
- HubSpot is canonical (hs_is_closed = false defines an open deal).
- Closed-won period: Q2+Q3 2026 (closedate 2026-04-01..2026-09-30).
- Operating view: Enterprise + Single Brain + Upsell; Karrot ABM is a
  separate automation lane (see CLAUDE.md, do not relitigate).
- Sheet-derived fields (capacity model, target_to_date, behavior signals)
  are carried forward and flagged, never silently treated as fresh.

Requires: HUBSPOT_READ_KEY env var (read-only private app token,
crm.objects.deals.read). Stdlib only — no pip installs.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

TOKEN = os.environ.get("HUBSPOT_READ_KEY")
if not TOKEN:
    sys.exit("HUBSPOT_READ_KEY is not set. Add it as a repo Actions secret (read-only HubSpot private app token).")

API = "https://api.hubapi.com/crm/v3/objects/deals/search"
NOW = datetime.now(timezone.utc)
NOW_ISO = NOW.strftime("%Y-%m-%dT%H:%M:%S.%f+00:00")
TODAY = NOW.date()

PIPELINES = {
    "15134857": "enterprise",
    "653361553": "karrot_abm_automation_lane",
    "745899055": "upsell",
    "891363949": "single_brain",
}
OPERATING = {"enterprise", "single_brain", "upsell"}
CLOSED_WON_START = "2026-04-01"
CLOSED_WON_END = "2026-09-30"
TARGET = 10_000_000


def search(filters, properties=None, fetch_all=False):
    """Run a deals search; return (total, records)."""
    records, after = [], None
    while True:
        body = {
            "filterGroups": [{"filters": filters}],
            "properties": properties or [],
            "limit": 200,
        }
        if after:
            body["after"] = after
        req = urllib.request.Request(
            API,
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.load(resp)
        total = data.get("total", 0)
        records.extend(data.get("results", []))
        paging = data.get("paging", {}).get("next", {})
        after = paging.get("after")
        if not fetch_all or not after:
            return total, records


def num(rec, prop):
    v = rec.get("properties", {}).get(prop)
    try:
        return float(v) if v not in (None, "") else 0.0
    except ValueError:
        return 0.0


def ts_ms(d):
    return str(int(datetime(d.year, d.month, d.day, tzinfo=timezone.utc).timestamp() * 1000))


# ---- Open deals (full fetch: amounts, weighted, per-pipeline, hygiene) ----
_, open_deals = search(
    [{"propertyName": "hs_is_closed", "operator": "EQ", "value": "false"}],
    ["amount_in_home_currency", "hs_projected_amount", "pipeline", "hs_next_step",
     "notes_next_activity_date", "notes_last_updated"],
    fetch_all=True,
)
open_count = len(open_deals)
open_sum = round(sum(num(d, "amount_in_home_currency") for d in open_deals))
weighted_sum = round(sum(num(d, "hs_projected_amount") for d in open_deals))

stale_cutoff = (NOW - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
per_pipe = {}
no_next_total = no_activity_total = stale_total = 0
for d in open_deals:
    p = d.get("properties", {})
    key = PIPELINES.get(p.get("pipeline"), "other")
    bucket = per_pipe.setdefault(key, {"open_deal_count": 0, "open_pipeline": 0, "open_missing_next_step": 0})
    bucket["open_deal_count"] += 1
    bucket["open_pipeline"] += round(num(d, "amount_in_home_currency"))
    missing_next = not p.get("hs_next_step")
    if missing_next:
        bucket["open_missing_next_step"] += 1
        no_next_total += 1
    if not p.get("notes_next_activity_date"):
        no_activity_total += 1
    last = p.get("notes_last_updated") or ""
    if last and last < stale_cutoff:
        stale_total += 1

op_view = {"open_deal_count": 0, "open_pipeline": 0, "open_missing_next_step": 0}
for k in OPERATING:
    for f in op_view:
        op_view[f] += per_pipe.get(k, {}).get(f, 0)

# ---- Closed-won, counts, activity ----
cw_total, cw = search(
    [{"propertyName": "hs_is_closed_won", "operator": "EQ", "value": "true"},
     {"propertyName": "closedate", "operator": "BETWEEN", "value": CLOSED_WON_START, "highValue": CLOSED_WON_END}],
    ["amount_in_home_currency"], fetch_all=True)
actual_revenue = round(sum(num(d, "amount_in_home_currency") for d in cw))

missing_close, _ = search([{"propertyName": "closedate", "operator": "NOT_HAS_PROPERTY"}])
missing_owner, _ = search([{"propertyName": "hubspot_owner_id", "operator": "NOT_HAS_PROPERTY"}])

yday = TODAY - timedelta(days=1)
created_total, created = search(
    [{"propertyName": "createdate", "operator": "BETWEEN", "value": ts_ms(yday), "highValue": ts_ms(TODAY + timedelta(days=1))}],
    ["amount_in_home_currency"], fetch_all=True)
created_sum = round(sum(num(d, "amount_in_home_currency") for d in created))
modified_total, _ = search(
    [{"propertyName": "hs_lastmodifieddate", "operator": "BETWEEN", "value": ts_ms(yday), "highValue": ts_ms(TODAY + timedelta(days=1))}])

monday = TODAY - timedelta(days=TODAY.weekday())
prev_monday = monday - timedelta(days=7)


def week_closed_won(start, end):
    t, recs = search(
        [{"propertyName": "hs_is_closed_won", "operator": "EQ", "value": "true"},
         {"propertyName": "closedate", "operator": "BETWEEN", "value": str(start), "highValue": str(end)}],
        ["amount_in_home_currency"], fetch_all=True)
    return t, round(sum(num(d, "amount_in_home_currency") for d in recs))


tw_count, tw_rev = week_closed_won(monday, monday + timedelta(days=6))
pw_count, pw_rev = week_closed_won(prev_monday, prev_monday + timedelta(days=6))

forecast = actual_revenue + weighted_sum
gap = forecast - TARGET

# ---- Load previous files (carried fields + diff baseline) ----
with open("daily.json") as f:
    prev = json.load(f)
with open("weekly.json") as f:
    weekly = json.load(f)
with open("source-map.json") as f:
    source_map = json.load(f)

prev_live_ts = prev.get("generated_at_utc", "")
daily = prev  # carried fields (capacity_model, target_to_date, behavior_signals, sheet sources) stay

capacity_model = prev.get("capacity_model")
daily.update({
    "generated_at_utc": NOW_ISO,
    "status": "OFF TRACK" if forecast < TARGET else "ON TRACK",
    "actual_revenue": actual_revenue,
    "crm_forecast": forecast,
    "capacity_not_backed_by_crm": (capacity_model - forecast) if capacity_model else None,
    "gap_to_target": gap,
    "open_pipeline": open_sum,
    "weighted_pipeline": weighted_sum,
    "actual_activity_yesterday_today": f"{created_sum} new pipeline / {modified_total} modified",
    "required_activity_today": (
        f"Clean {op_view['open_missing_next_step']} no-next-step deals in operating pipelines; "
        f"recover stale deals; create net-new pipeline"
    ),
    "recovery_action": (
        f"Assign owner for the {op_view['open_missing_next_step']} no-next-step deals in the operating pipelines "
        f"(Enterprise {per_pipe.get('enterprise', {}).get('open_missing_next_step', 0)}, "
        f"Single Brain {per_pipe.get('single_brain', {}).get('open_missing_next_step', 0)}, "
        f"Upsell {per_pipe.get('upsell', {}).get('open_missing_next_step', 0)}). "
        f"Karrot ABM's {per_pipe.get('karrot_abm_automation_lane', {}).get('open_missing_next_step', 0)} "
        f"are automation noise, handled as a separate lane."
    ),
})
rc = daily["risk_counts"]
rc.update({
    "open_deal_count": open_count,
    "open_missing_next_step": no_next_total,
    "stale_open_deals_30d": stale_total,
    "open_missing_next_activity": no_activity_total,
    "missing_close_date": missing_close,
    "missing_owner": missing_owner,
    "stale_open_deals_gt_30d": stale_total,
    "open_deals_missing_next_step": no_next_total,
    "open_deals_missing_next_activity": no_activity_total,
    "deals_missing_close_date": missing_close,
    "deals_missing_owner": missing_owner,
})
pipes = daily.setdefault("pipelines", {})
pipes["operating_view"] = {
    "definition": "Enterprise + Single Brain + Upsell (Eric, 2026-06-11). Karrot ABM excluded from status and hygiene counts.",
    **op_view,
}
for k, v in per_pipe.items():
    entry = pipes.setdefault(k, {})
    entry.update(v)
daily["sources"][0] = {
    "tab": "HubSpot Live (GitHub Action, read-only API aggregates)",
    "range": "DEAL aggregates, portal-wide and per-pipeline",
    "refreshed_at_utc": NOW_ISO,
}
flags = [f for f in daily.get("data_quality_flags", []) if not f.startswith("crm_forecast")]
daily["data_quality_flags"] = [
    f"crm_forecast, actual_revenue, open_pipeline, weighted_pipeline, risk_counts, and per-pipeline counts "
    f"verified live against HubSpot CRM (read-only API) at {NOW_ISO}. HubSpot is canonical."
] + flags

weekly.update({
    "generated_at_utc": NOW_ISO,
    "status": daily["status"],
})
ws = weekly["weekly_summary"]
ws["closed_won_deals"].update({
    "this_week": tw_count, "prior_week": pw_count, "delta": tw_count - pw_count,
    "direction": ("No activity / no movement" if tw_count == pw_count == 0
                  else "Better" if tw_count > pw_count else "Worse" if tw_count < pw_count else "Flat"),
})
ws["revenue_booked"].update({
    "this_week": tw_rev, "prior_week": pw_rev, "delta": tw_rev - pw_rev,
    "direction": ("No activity / no movement" if tw_rev == pw_rev == 0
                  else "Better" if tw_rev > pw_rev else "Worse" if tw_rev < pw_rev else "Flat"),
})

source_map["generated_at_utc"] = NOW_ISO
for m in source_map.get("metrics", []):
    if "live-connector" in m.get("source_type", ""):
        m["refreshed_at_utc"] = NOW_ISO
for c in source_map.get("live_connectors", []):
    if c["name"].startswith("HubSpot"):
        c["refreshed_at_utc"] = NOW_ISO

# ---- change-log: real diffs vs previous published snapshot ----
DIFF_FIELDS = ["crm_forecast", "gap_to_target", "open_pipeline", "weighted_pipeline",
               "actual_revenue", "capacity_not_backed_by_crm"]
with open("change-log.json") as f:
    changelog = json.load(f)
prev_snapshot = {k: None for k in DIFF_FIELDS}
try:
    with open("snapshots/latest.json") as f:
        prev_snapshot = json.load(f)
except FileNotFoundError:
    pass
changes = []
for k in DIFF_FIELDS:
    if prev_snapshot.get(k) is not None and prev_snapshot[k] != daily.get(k):
        changes.append({"field": k, "previous": prev_snapshot[k], "current": daily.get(k)})
changelog.update({
    "generated_at_utc": NOW_ISO,
    "baseline": False,
    "daily_diff": {
        "baseline": False,
        "compared_against": f"previous published snapshot ({prev_live_ts})",
        "changes": changes or [{"field": "all", "previous": "carried", "current": "carried",
                                "note": "No movement in tracked fields — labeled carried, not shown as a diff."}],
    },
    "weekly_diff": changelog.get("weekly_diff", {}),
})

os.makedirs("snapshots", exist_ok=True)
snap = {k: daily.get(k) for k in DIFF_FIELDS}
snap["generated_at_utc"] = NOW_ISO
snap["risk_counts"] = rc
with open("snapshots/latest.json", "w") as f:
    json.dump(snap, f, indent=2)
with open(f"snapshots/daily-{TODAY}.json", "w") as f:
    json.dump(snap, f, indent=2)

for name, obj in [("daily.json", daily), ("weekly.json", weekly),
                  ("source-map.json", source_map), ("change-log.json", changelog)]:
    with open(name, "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
        f.write("\n")

print(f"Refreshed {NOW_ISO}: forecast={forecast} gap={gap} open={open_count}/{open_sum} "
      f"weighted={weighted_sum} op_view_no_next_step={op_view['open_missing_next_step']}")
