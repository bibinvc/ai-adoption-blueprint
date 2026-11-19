"""Summarises the AI use-case portfolio and flags what is not ready to scale."""
from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


def summary(path: Path) -> tuple[str, list[dict]]:
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    stages = Counter(r["stage"] for r in rows)
    blocked = [r for r in rows if r["stage"] in ("pilot", "scaled")
               and (r["responsible_ai_review"] != "done" or r["privacy_review"] not in ("done", "not needed"))]
    md = ["# AI portfolio", "", "| Stage | Use cases |", "|---|---:|"]
    md += [f"| {s} | {stages.get(s, 0)} |" for s in ("idea", "pilot", "scaled")]
    md += ["", "| Use case | Stage | Owner | Risk | Responsible AI | Privacy | Next step |", "|---|---|---|---|---|---|---|"]
    md += [f"| {r['use_case']} | {r['stage']} | {r['owner']} | {r['risk_level']} | {r['responsible_ai_review']} | "
           f"{r['privacy_review']} | {r['next_step']} |" for r in rows]
    md += ["", f"Use cases in pilot or scaled without completed reviews: {len(blocked)}."]
    return "\n".join(md) + "\n", blocked
