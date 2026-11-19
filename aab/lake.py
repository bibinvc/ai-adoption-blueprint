"""Data lake proof of concept: bronze (raw + lineage), silver (validated), gold (KPIs, star schema).

Every rejected row goes to a quarantine file with its reason, so data curators can fix the source
instead of losing data silently. A catalog records owner, classification and columns per dataset.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

from .synth import START, TOOLS, WEEKS

EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b")


def _read_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write_csv(p: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or (list(rows[0]) if rows else [])
    with p.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def row_hash(row: dict) -> str:
    return hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()[:16]


# ---------------------------------------------------------------- bronze

def bronze(raw: Path, lake: Path, run_date: str) -> dict:
    """Copies raw files unchanged under an ingestion-date folder and writes a lineage manifest."""
    manifest = []
    for f in sorted(raw.iterdir()):
        dest = lake / "bronze" / f.stem / f"ingest_date={run_date}" / f.name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        manifest.append({"dataset": f.stem, "file": f.name, "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                         "bytes": f.stat().st_size, "ingested_at": datetime.now(timezone.utc).isoformat(timespec="seconds")})
    (lake / "bronze" / "_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return {"files": len(manifest)}


# ---------------------------------------------------------------- silver

def silver_usage(raw_rows: list[dict], known_users: set[str], run_date: str) -> tuple[list[dict], list[dict], dict]:
    good, bad, seen = [], [], set()
    checks = defaultdict(int)
    end = date.fromisoformat(run_date)
    for r in raw_rows:
        h = row_hash(r)
        reason = None
        if h in seen:
            reason = "duplicate row"
        elif not r["user_id"] or r["user_id"] not in known_users:
            reason = "missing or unknown user_id"
        elif r["tool"] not in TOOLS:
            reason = "unknown tool"
        else:
            try:
                d = date.fromisoformat(r["event_date"])
                if d > end or d < START:
                    reason = "event_date outside pilot window"
            except ValueError:
                reason = "invalid event_date"
            if not reason and r["quality_rating"] not in ("", "1", "2", "3", "4", "5"):
                reason = "quality_rating not in 1-5"
        seen.add(h)
        if reason:
            checks[reason] += 1
            bad.append({**r, "_reason": reason})
            continue
        comment, n = EMAIL.subn("[EMAIL]", r["comment"])
        if n:
            checks["personal data masked in comment"] += n
        good.append({**r, "comment": comment, "minutes_saved": int(r["minutes_saved"]),
                     "cost_eur": float(r["cost_eur"]), "_row_hash": h})
    return good, bad, dict(checks)


def silver_news(lines: list[str]) -> tuple[list[dict], list[dict], dict]:
    good, bad, seen = [], [], set()
    checks = defaultdict(int)
    for line in lines:
        r = json.loads(line)
        key = (r.get("title"), r.get("published"), r.get("market"))
        reason = None
        if key in seen:
            reason = "duplicate item"
        elif not r.get("market"):
            reason = "missing market"
        elif r.get("severity") not in ("low", "medium", "high"):
            reason = "invalid severity"
        seen.add(key)
        if reason:
            checks[reason] += 1
            bad.append({**r, "_reason": reason})
        else:
            good.append(r)
    return good, bad, dict(checks)


# ---------------------------------------------------------------- gold

def week_of(d: str) -> int:
    return (date.fromisoformat(d) - START).days // 7 + 1


def gold(usage: list[dict], users: list[dict]) -> dict[str, list[dict]]:
    by_user = {u["user_id"]: u for u in users}
    licensed_by_region = defaultdict(int)
    for u in users:
        licensed_by_region[u["region"]] += 1

    weekly = []
    for wk in range(1, WEEKS + 1):
        ev = [e for e in usage if week_of(e["event_date"]) == wk]
        active = {e["user_id"] for e in ev}
        weekly.append({"week": wk, "active_users": len(active), "events": len(ev),
                       "hours_saved": round(sum(e["minutes_saved"] for e in ev) / 60, 1),
                       "cost_eur": round(sum(e["cost_eur"] for e in ev), 2)})

    last4 = [e for e in usage if week_of(e["event_date"]) > WEEKS - 4]
    region_rows = []
    for region, licensed in sorted(licensed_by_region.items()):
        active = {e["user_id"] for e in last4 if by_user[e["user_id"]]["region"] == region}
        region_rows.append({"region": region, "licensed_users": licensed, "active_users_last_4_weeks": len(active),
                            "adoption_rate": round(len(active) / licensed, 3)})

    tool_rows = []
    for tool in TOOLS:
        ev = [e for e in usage if e["tool"] == tool]
        rated = [int(e["quality_rating"]) for e in ev if e["quality_rating"]]
        hours = sum(e["minutes_saved"] for e in ev) / 60
        cost = sum(e["cost_eur"] for e in ev)
        tool_rows.append({"tool": tool, "events": len(ev), "hours_saved": round(hours, 1),
                          "avg_quality": round(sum(rated) / len(rated), 2) if rated else None,
                          "rated_share": round(len(rated) / len(ev), 2) if ev else 0,
                          "cost_eur": round(cost, 2),
                          "cost_per_hour_saved_eur": round(cost / hours, 3) if hours else None})

    # star schema for Power BI
    fact = [{"event_id": e["event_id"], "date_key": e["event_date"].replace("-", ""), "user_id": e["user_id"],
             "tool": e["tool"], "task": e["task"], "minutes_saved": e["minutes_saved"],
             "quality_rating": e["quality_rating"], "cost_eur": e["cost_eur"]} for e in usage]
    dim_user = [{k: u[k] for k in ("user_id", "function", "region", "market", "licensed")} for u in users]
    dim_tool = [{"tool": t, "type": "assistant" if t == "M365 Copilot" else ("flow" if "Automate" in t else "agent")}
                for t in TOOLS]
    dates = sorted({e["event_date"] for e in usage})
    dim_date = [{"date_key": d.replace("-", ""), "date": d, "week": week_of(d),
                 "weekday": date.fromisoformat(d).strftime("%A")} for d in dates]
    return {"kpi_weekly": weekly, "kpi_adoption_by_region": region_rows, "kpi_by_tool": tool_rows,
            "fact_usage": fact, "dim_user": dim_user, "dim_tool": dim_tool, "dim_date": dim_date}


CATALOG = [
    {"dataset": "bronze/ai_usage_events", "layer": "bronze", "owner": "Data curator, CA Digital",
     "classification": "Internal, may contain personal data", "description": "Raw usage export, unchanged"},
    {"dataset": "bronze/policy_news", "layer": "bronze", "owner": "Data curator, Policy",
     "classification": "Internal", "description": "Raw policy news feed, unchanged"},
    {"dataset": "silver/ai_usage_events", "layer": "silver", "owner": "Data curator, CA Digital",
     "classification": "Internal, pseudonymous ids, comments masked", "description": "Validated, deduplicated usage events"},
    {"dataset": "silver/policy_news", "layer": "silver", "owner": "Data curator, Policy",
     "classification": "Internal", "description": "Validated, deduplicated news items"},
    {"dataset": "gold/kpi_*", "layer": "gold", "owner": "CA AI team",
     "classification": "Internal, aggregated", "description": "Adoption, productivity, quality and cost KPIs"},
    {"dataset": "gold/fact_usage + dim_*", "layer": "gold", "owner": "CA AI team",
     "classification": "Internal, pseudonymous", "description": "Star schema loaded by Power BI"},
]


def run(raw: Path, lake: Path, run_date: str) -> dict:
    if lake.exists():
        shutil.rmtree(lake)
    bronze(raw, lake, run_date)
    users = _read_csv(raw / "users.csv")
    usage, bad_u, checks_u = silver_usage(_read_csv(raw / "ai_usage_events.csv"), {u["user_id"] for u in users}, run_date)
    news, bad_n, checks_n = silver_news((raw / "policy_news.jsonl").read_text(encoding="utf-8").splitlines())
    _write_csv(lake / "silver" / "ai_usage_events.csv", usage)
    _write_csv(lake / "silver" / "quarantine" / "ai_usage_events.csv", bad_u)
    (lake / "silver" / "policy_news.jsonl").write_text("\n".join(json.dumps(n) for n in news) + "\n", encoding="utf-8")
    (lake / "silver" / "quarantine" / "policy_news.jsonl").write_text(
        "\n".join(json.dumps(n) for n in bad_n) + "\n", encoding="utf-8")
    g = gold(usage, users)
    for name, rows in g.items():
        _write_csv(lake / "gold" / f"{name}.csv", rows)
    (lake / "catalog.json").write_text(json.dumps(CATALOG, indent=2), encoding="utf-8")
    quality = {"ai_usage_events": {"raw_rows": len(usage) + len(bad_u), "accepted": len(usage),
                                   "quarantined": len(bad_u), "checks": checks_u},
               "policy_news": {"raw_rows": len(news) + len(bad_n), "accepted": len(news),
                               "quarantined": len(bad_n), "checks": checks_n}}
    (lake / "quality_report.json").write_text(json.dumps(quality, indent=2), encoding="utf-8")
    return {"quality": quality, "gold": g, "news": news, "users": users, "usage": usage}
