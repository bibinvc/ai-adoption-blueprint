"""Synthetic raw data for a fictional Corporate Affairs function ("Example Group").

Two raw feeds land in data/raw:
- ai_usage_events.csv : one row per use of an AI tool, with self-reported minutes saved,
  an optional 1-5 quality rating and an allocated cost.
- policy_news.jsonl    : policy and regulatory news items collected per market.

Known defects are injected on purpose (duplicates, missing ids, out-of-range ratings, future
dates, personal data in free text) so the data lake quality checks have something to catch.
"""
from __future__ import annotations

import csv
import json
import random
from datetime import date, timedelta
from pathlib import Path

FUNCTIONS = ["Communications", "Policy", "Sustainability", "Stakeholder Engagement", "Research & Insights"]
REGIONS = {
    "Europe": ["France", "Germany", "Italy", "Poland", "Switzerland"],
    "Americas": ["Brazil", "Canada", "Mexico"],
    "Asia-Pacific": ["Japan", "Indonesia", "Australia"],
    "Middle East & Africa": ["Egypt", "South Africa"],
}
TOOLS = ["M365 Copilot", "Rapid Response agent", "Policy Digest agent", "Power Automate flow"]
TASKS = {
    "M365 Copilot": ["summarise document", "draft email", "meeting recap"],
    "Rapid Response agent": ["draft holding statement", "find past positions"],
    "Policy Digest agent": ["weekly policy digest", "market briefing"],
    "Power Automate flow": ["route request", "collect approvals"],
}
MINUTES = {"summarise document": 20, "draft email": 10, "meeting recap": 15, "draft holding statement": 45,
           "find past positions": 30, "weekly policy digest": 90, "market briefing": 60,
           "route request": 8, "collect approvals": 25}
TOPICS = ["taxation", "packaging", "sustainability reporting", "AI regulation", "trade", "advertising rules"]

START = date(2026, 9, 7)   # Monday, week 1 of the pilot
WEEKS = 12
# rollout waves: region -> first week it gets access
WAVES = {"Europe": 1, "Americas": 4, "Asia-Pacific": 7, "Middle East & Africa": 9}


def users(rng: random.Random, n: int = 240) -> list[dict]:
    out = []
    regions = list(REGIONS)
    for i in range(1, n + 1):
        region = regions[i % len(regions)] if i % 5 else "Europe"
        out.append({"user_id": f"U{i:04d}", "function": FUNCTIONS[i % len(FUNCTIONS)], "region": region,
                    "market": REGIONS[region][i % len(REGIONS[region])], "licensed": "yes"})
    return out


def usage_events(rng: random.Random, people: list[dict]) -> list[dict]:
    rows = []
    eid = 0
    # not everyone adopts: a third of users stay occasional, some become regular users
    ceiling = {}
    for u in people:
        r = rng.random()
        ceiling[u["user_id"]] = 0.06 if r < 0.30 else (0.40 if r < 0.65 else 0.80)
    for week in range(1, WEEKS + 1):
        for u in people:
            if week < WAVES[u["region"]]:
                continue
            weeks_live = week - WAVES[u["region"]] + 1
            p_active = min(ceiling[u["user_id"]], 0.10 + 0.06 * weeks_live)   # adoption grows after rollout
            if rng.random() > p_active:
                continue
            for _ in range(rng.randint(1, 5)):
                tool = rng.choices(TOOLS, weights=[55, 15, 15, 15])[0]
                task = rng.choice(TASKS[tool])
                day = START + timedelta(weeks=week - 1, days=rng.randint(0, 4))
                eid += 1
                rating = rng.choice(["", "", 3, 4, 4, 5, 5, 2])
                rows.append({
                    "event_id": f"E{eid:06d}", "event_date": day.isoformat(), "user_id": u["user_id"],
                    "tool": tool, "task": task,
                    "minutes_saved": max(0, int(rng.gauss(MINUTES[task], MINUTES[task] * 0.3))),
                    "quality_rating": rating, "cost_eur": round(rng.uniform(0.02, 0.40), 2), "comment": "",
                })
    # injected defects
    rows.append(dict(rows[10]))                                        # exact duplicate
    rows.append({**rows[20], "event_id": "E999001", "user_id": ""})     # missing user
    rows.append({**rows[30], "event_id": "E999002", "quality_rating": 9})   # out of range
    rows.append({**rows[40], "event_id": "E999003", "event_date": "2027-03-01"})  # future date
    rows.append({**rows[50], "event_id": "E999004",
                 "comment": "Great draft, ask jane.doe@example.com for the final quote"})  # personal data
    rows.append({**rows[60], "event_id": "E999005", "tool": "Unknown bot"})  # unknown tool
    return rows


def news(rng: random.Random, n: int = 160) -> list[dict]:
    items = []
    markets = [(r, m) for r, ms in REGIONS.items() for m in ms]
    for i in range(1, n + 1):
        region, market = markets[i % len(markets)]
        topic = TOPICS[i % len(TOPICS)]
        severity = rng.choices(["low", "medium", "high"], weights=[55, 33, 12])[0]
        day = START + timedelta(days=rng.randint(0, WEEKS * 7 - 3))
        verb = {"low": "opens a consultation on", "medium": "publishes draft rules on",
                "high": "announces an urgent decree on"}[severity]
        items.append({
            "id": f"N{i:04d}", "published": day.isoformat(), "region": region, "market": market,
            "topic": topic, "severity": severity,
            "title": f"{market} {verb} {topic}",
            "text": (f"The {market} authorities {verb} {topic}. Stakeholders have until the end of the "
                     f"quarter to respond. The measure would apply to all companies operating in {market}."),
            "source": f"https://news.example.invalid/{market.lower().replace(' ', '-')}/{i}",
        })
    items.append(dict(items[5]))                          # duplicate
    items.append({**items[7], "id": "N9001", "market": ""})  # missing market
    return items


def write_all(raw: Path, seed: int = 7) -> dict:
    rng = random.Random(seed)
    raw.mkdir(parents=True, exist_ok=True)
    people = users(rng)
    with (raw / "users.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(people[0]))
        w.writeheader()
        w.writerows(people)
    events = usage_events(rng, people)
    with (raw / "ai_usage_events.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(events[0]))
        w.writeheader()
        w.writerows(events)
    items = news(rng)
    with (raw / "policy_news.jsonl").open("w", encoding="utf-8") as f:
        for it in items:
            f.write(json.dumps(it) + "\n")
    return {"users": len(people), "events": len(events), "news": len(items)}
