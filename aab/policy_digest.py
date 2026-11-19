"""Policy Digest agent prototype (offline, rule based).

Reads validated news from the silver layer, ranks items per region, routes high-severity items to
the Rapid Response queue and drafts a weekly digest with sources. A person reviews before sending.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import date, timedelta

SEVERITY = {"high": 3, "medium": 2, "low": 1}
PRIORITY_TOPICS = {"AI regulation": 1.5, "taxation": 1.3, "packaging": 1.2}


def score(item: dict) -> float:
    return SEVERITY[item["severity"]] * PRIORITY_TOPICS.get(item["topic"], 1.0)


def digest(news: list[dict], week_end: str) -> tuple[str, list[dict]]:
    end = date.fromisoformat(week_end)
    start = end - timedelta(days=6)
    week = [n for n in news if start <= date.fromisoformat(n["published"]) <= end]
    rapid = sorted([n for n in week if n["severity"] == "high"], key=score, reverse=True)
    by_region = defaultdict(list)
    for n in week:
        by_region[n["region"]].append(n)

    md = [f"# Weekly policy digest, {start.isoformat()} to {end.isoformat()}", "",
          "_Draft prepared by the Policy Digest agent from validated sources. To be reviewed by the Policy team "
          "before distribution._", "",
          f"{len(week)} items this week, {len(rapid)} sent to the Rapid Response queue.", ""]
    for region in sorted(by_region):
        items = sorted(by_region[region], key=score, reverse=True)[:5]
        md += [f"## {region}", ""]
        for n in items:
            first_sentence = n["text"].split(". ")[0].rstrip(".") + "."
            md.append(f"- **{n['title']}** ({n['severity']}, {n['topic']}). {first_sentence} [source]({n['source']})")
        md.append("")
    queue = [{"id": n["id"], "market": n["market"], "topic": n["topic"], "title": n["title"],
              "status": "to assess", "source": n["source"]} for n in rapid]
    return "\n".join(md), queue
