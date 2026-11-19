"""Runs the whole blueprint: python -m aab.run

Generates synthetic raw data, builds the data lake, computes KPIs, the business case, value
stream metrics, the portfolio summary and the weekly policy digest. Outputs go to out/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import business_case, dashboard, lake, policy_digest, portfolio, synth, value_stream

ROOT = Path(__file__).resolve().parent.parent
RUN_DATE = "2026-11-27"   # last Friday of the 12-week pilot


def main() -> int:
    out = ROOT / "out"
    out.mkdir(exist_ok=True)
    counts = synth.write_all(ROOT / "data" / "raw")
    res = lake.run(ROOT / "data" / "raw", out / "lake", RUN_DATE)
    active = sum(r["active_users_last_4_weeks"] for r in res["gold"]["kpi_adoption_by_region"])
    bc = business_case.compute(res["gold"]["kpi_weekly"], active)
    (out / "business-case.md").write_text(business_case.markdown(bc), encoding="utf-8")
    (out / "adoption_dashboard.html").write_text(dashboard.render(res["gold"], res["quality"], bc), encoding="utf-8")
    vs_md, vs_rows = value_stream.report(ROOT / "blueprint" / "value_streams.json")
    (out / "value-streams.md").write_text(vs_md, encoding="utf-8")
    pf_md, blocked = portfolio.summary(ROOT / "governance" / "ai_portfolio.csv")
    (out / "portfolio.md").write_text(pf_md, encoding="utf-8")
    dg_md, queue = policy_digest.digest(res["news"], RUN_DATE)
    (out / "policy_digest.md").write_text(dg_md, encoding="utf-8")
    (out / "rapid_response_queue.json").write_text(json.dumps(queue, indent=2), encoding="utf-8")
    summary = {"raw": counts, "quality": res["quality"], "business_case": bc, "value_streams": vs_rows,
               "portfolio_blocked": len(blocked), "rapid_response_items": len(queue)}
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps({"quality": res["quality"], "base_roi": bc["scenarios"]["base"]["roi"],
                      "value_streams": [(r["stream"], r["touch_hours_saved_per_year"], r["lead_time_reduction"]) for r in vs_rows],
                      "rapid_response_items": len(queue)}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
