"""Static HTML adoption dashboard (inline SVG, no external libraries)."""
from __future__ import annotations

from html import escape


def _line(points: list[tuple[str, float]], w: int = 560, h: int = 180, color: str = "var(--accent)") -> str:
    if not points:
        return ""
    mx = max(v for _, v in points) or 1
    step = (w - 40) / max(1, len(points) - 1)
    xy = [(30 + i * step, h - 25 - v / mx * (h - 45)) for i, (_, v) in enumerate(points)]
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}" for i, (x, y) in enumerate(xy))
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3"><title>{escape(l)}: {v:g}</title></circle>'
                   for (x, y), (l, v) in zip(xy, points))
    labels = "".join(f'<text x="{x:.1f}" y="{h - 6}" text-anchor="middle">{escape(l)}</text>'
                     for (x, _), (l, _) in zip(xy, points))
    axis = (f'<line x1="30" y1="{h - 25}" x2="{w - 10}" y2="{h - 25}" class="ax"/>'
            f'<line x1="30" y1="20" x2="{w - 10}" y2="20" class="grid"/>'
            f'<text x="26" y="24" text-anchor="end">{mx:,.0f}</text><text x="26" y="{h - 22}" text-anchor="end">0</text>')
    return (f'<svg viewBox="0 0 {w} {h}" role="img">{axis}<path d="{path}" fill="none" stroke="{color}" '
            f'stroke-width="2.5"/>{dots}{labels}</svg>')


def _bars(rows: list[tuple[str, float]], fmt: str = "{:g}", w: int = 560) -> str:
    mx = max((v for _, v in rows), default=1) or 1
    bar_h, gap = 22, 10
    h = len(rows) * (bar_h + gap) + 10
    out = []
    for i, (label, v) in enumerate(rows):
        y = 5 + i * (bar_h + gap)
        bw = (w - 230) * v / mx
        out.append(f'<text x="0" y="{y + 15}">{escape(label)}</text>'
                   f'<rect x="170" y="{y}" width="{bw:.1f}" height="{bar_h}" rx="3"/>'
                   f'<text x="{176 + bw:.1f}" y="{y + 15}">{escape(fmt.format(v))}</text>')
    return f'<svg viewBox="0 0 {w} {h}" role="img">{"".join(out)}</svg>'


def render(gold: dict, quality: dict, bc: dict) -> str:
    weekly, regions, tools = gold["kpi_weekly"], gold["kpi_adoption_by_region"], gold["kpi_by_tool"]
    licensed = sum(r["licensed_users"] for r in regions)
    active = sum(r["active_users_last_4_weeks"] for r in regions)
    hours_total = sum(w["hours_saved"] for w in weekly)
    rated = [t for t in tools if t["avg_quality"]]
    avg_q = sum(t["avg_quality"] * t["events"] for t in rated) / sum(t["events"] for t in rated)
    cost_total = sum(t["cost_eur"] for t in tools)
    q = quality["ai_usage_events"]
    cards = [("Adoption, last 4 weeks", f"{active / licensed:.0%}", f"{active} of {licensed} licensed users"),
             ("Hours saved, reported", f"{hours_total:,.0f}", "12-week pilot, self-reported"),
             ("Average quality", f"{avg_q:.2f} / 5", "user ratings"),
             ("Usage cost per hour saved", f"EUR {cost_total / hours_total:.2f}", "allocated compute cost"),
             ("Base-case ROI", f"{bc['models']['all_users']['scenarios']['base']['roi']:.0%} / {bc['models']['active_users_only']['scenarios']['base']['roi']:.0%}", "licences for all / for active users"),
             ("Rows quarantined", f"{q['quarantined']}", f"of {q['raw_rows']} raw usage rows")]
    card_html = "".join(f'<div class="card"><div class="k">{escape(a)}</div><div class="v">{escape(b)}</div>'
                        f'<div class="s">{escape(c)}</div></div>' for a, b, c in cards)
    tool_rows = "".join(
        f"<tr><td>{escape(t['tool'])}</td><td class=n>{t['events']:,}</td><td class=n>{t['hours_saved']:,.0f}</td>"
        f"<td class=n>{t['avg_quality'] if t['avg_quality'] else '-'}</td>"
        f"<td class=n>{t['cost_per_hour_saved_eur'] if t['cost_per_hour_saved_eur'] else '-'}</td></tr>"
        for t in tools)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>AI adoption dashboard</title>
<style>
:root{{--bg:#f6f6f3;--card:#fff;--fg:#1c1c1a;--muted:#6a6a64;--line:#deded8;--accent:#2f6f9f}}
@media (prefers-color-scheme: dark){{:root{{--bg:#151514;--card:#1e1e1c;--fg:#ecece8;--muted:#a3a39c;--line:#34342f;--accent:#7fb3d9}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:24px 16px}} h1{{font-size:21px;margin:0}} h2{{font-size:15px;margin:26px 0 8px}}
.m{{color:var(--muted)}} .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:16px}}
.card,.panel{{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px}}
.k{{color:var(--muted);font-size:12px}} .v{{font-size:26px;font-weight:700;margin:4px 0}} .s{{color:var(--muted);font-size:12px}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}}
svg{{width:100%;height:auto}} svg text{{fill:var(--muted);font-size:11px}} svg .ax{{stroke:var(--line)}} svg .grid{{stroke:var(--line);stroke-dasharray:3 3}} svg rect{{fill:var(--accent)}} svg circle{{fill:var(--accent)}}
table{{border-collapse:collapse;width:100%}} th,td{{padding:6px 8px;border-bottom:1px solid var(--line);text-align:left}}
th{{color:var(--muted);font-weight:600}} .n{{text-align:right;font-variant-numeric:tabular-nums}} .panel{{overflow-x:auto}}
</style></head><body><main>
<h1>AI adoption dashboard, Corporate Affairs pilot</h1>
<p class="m">Synthetic data for a fictional company. Source: gold layer of the data lake proof of concept.</p>
<div class="grid">{card_html}</div>
<div class="two">
<div><h2>Weekly active users</h2><div class="panel">{_line([(f"W{w['week']}", w['active_users']) for w in weekly])}</div></div>
<div><h2>Hours saved per week, reported</h2><div class="panel">{_line([(f"W{w['week']}", w['hours_saved']) for w in weekly])}</div></div>
</div>
<div class="two">
<div><h2>Adoption by region, last 4 weeks</h2><div class="panel">{_bars([(r['region'], r['adoption_rate'] * 100) for r in regions], "{:.0f} %")}</div></div>
<div><h2>Hours saved by tool</h2><div class="panel">{_bars([(t['tool'], t['hours_saved']) for t in tools], "{:,.0f} h")}</div></div>
</div>
<h2>Tools</h2><div class="panel"><table><thead><tr><th>Tool</th><th class=n>Uses</th><th class=n>Hours saved</th>
<th class=n>Avg quality</th><th class=n>EUR per hour saved</th></tr></thead><tbody>{tool_rows}</tbody></table></div>
</main></body></html>
"""
