"""Value stream metrics (lead time, touch time, flow efficiency, value at stake) and Mermaid maps."""
from __future__ import annotations

import json
from pathlib import Path


def metrics(steps: list[dict], future: bool = False) -> dict:
    touch = sum((s["future"] if future else s)["touch_h"] for s in steps)
    wait = sum((s["future"] if future else s)["wait_h"] for s in steps)
    lead = touch + wait
    return {"touch_h": round(touch, 2), "wait_h": round(wait, 2), "lead_h": round(lead, 2),
            "flow_efficiency": round(touch / lead, 3) if lead else 0.0}


def value_at_stake(stream: dict, cost_per_hour: float) -> dict:
    now, fut = metrics(stream["steps"]), metrics(stream["steps"], future=True)
    saved_per_run = now["touch_h"] - fut["touch_h"]
    hours = saved_per_run * stream["occurrences_per_year"]
    return {"touch_hours_saved_per_run": round(saved_per_run, 2), "touch_hours_saved_per_year": round(hours),
            "value_eur_per_year": round(hours * cost_per_hour),
            "lead_time_reduction": round(1 - fut["lead_h"] / now["lead_h"], 3)}


def mermaid(stream: dict, future: bool) -> str:
    lines = ["flowchart LR"]
    for i, s in enumerate(stream["steps"]):
        d = s["future"] if future else s
        label = f"{s['step']}<br/>{s['owner']}<br/>touch {d['touch_h']} h, wait {d['wait_h']} h"
        lines.append(f'  S{i}["{label}"]')
        if i:
            lines.append(f"  S{i - 1} --> S{i}")
    return "\n".join(lines)


def report(path: Path) -> tuple[str, list[dict]]:
    cfg = json.loads(path.read_text(encoding="utf-8"))
    cost = cfg["assumptions"]["loaded_cost_eur_per_hour"]
    rows, md = [], ["# Value streams: current and future state", "",
                    f"_{cfg['assumptions']['note']} Loaded cost assumption: EUR {cost} per hour._", ""]
    for s in cfg["streams"]:
        now, fut, val = metrics(s["steps"]), metrics(s["steps"], True), value_at_stake(s, cost)
        neck = max(s["steps"], key=lambda x: x["future"]["wait_h"])
        rows.append({"stream": s["name"], "current": now, "future": fut, "bottleneck": neck["step"], **val})
        md += [f"## {s['name']}", "", f"Trigger: {s['trigger']}. Runs per year: {s['occurrences_per_year']}.", "",
               "| | Current | Future |", "|---|---:|---:|",
               f"| Touch time | {now['touch_h']} h | {fut['touch_h']} h |",
               f"| Waiting time | {now['wait_h']} h | {fut['wait_h']} h |",
               f"| Lead time | {now['lead_h']} h | {fut['lead_h']} h |",
               f"| Flow efficiency | {now['flow_efficiency']:.0%} | {fut['flow_efficiency']:.0%} |", "",
               f"Value at stake: {val['touch_hours_saved_per_year']} hours of work per year, about "
               f"EUR {val['value_eur_per_year']:,}; lead time {val['lead_time_reduction']:.0%} shorter.", "",
               f"Remaining bottleneck in the future state: **{neck['step']}** ({neck['future']['wait_h']} h of waiting). "
               + ("Flow efficiency falls because AI removes working time faster than waiting time, so waiting "
                  "becomes the main target of the next iteration." if fut["flow_efficiency"] < now["flow_efficiency"]
                  else "Flow efficiency improves because waiting time falls as well as working time."), "",
               "| Step | Owner | Pain point | Future change |", "|---|---|---|---|"]
        md += [f"| {x['step']} | {x['owner']} | {x['pain']} | {x['future']['change']} |" for x in s["steps"]]
        md += ["", "Current state:", "", "```mermaid", mermaid(s, False), "```", "",
               "Future state:", "", "```mermaid", mermaid(s, True), "```", ""]
    return "\n".join(md), rows
