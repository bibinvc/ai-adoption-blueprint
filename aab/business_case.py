"""Business case from pilot KPIs, with the assumptions written out and three scenarios.

Self-reported time savings usually overstate real savings, so only a share of them is counted
("realisation rate"). Two licence models are compared: a licence for every user in scope, or
licences only for users who were active in the last four weeks. Every number comes from
synthetic pilot data and the stated assumptions.
"""
from __future__ import annotations

ASSUMPTIONS = {
    "loaded_cost_eur_per_hour": 65,
    "licence_eur_per_user_month": 28,        # replace with the real contract price
    "users_in_scope": 240,
    "build_and_run_eur_year": 60000,         # agents, flows, data lake, support
    "change_management_eur_year": 25000,     # champions, training, communication
}

SCENARIOS = {"low": 0.25, "base": 0.40, "high": 0.55}   # realisation rate of self-reported savings


def _costs(licences: int, usage_cost_per_week: float) -> float:
    a = ASSUMPTIONS
    return (a["licence_eur_per_user_month"] * 12 * licences + a["build_and_run_eur_year"]
            + a["change_management_eur_year"] + usage_cost_per_week * 52)


def compute(kpi_weekly: list[dict], active_last_4_weeks: int) -> dict:
    last4 = kpi_weekly[-4:]
    hours_per_week = sum(w["hours_saved"] for w in last4) / 4
    usage_cost_per_week = sum(w["cost_eur"] for w in last4) / 4
    a = ASSUMPTIONS
    models = {"all_users": a["users_in_scope"], "active_users_only": active_last_4_weeks}
    out = {"reported_hours_saved_per_week": round(hours_per_week, 1),
           "active_users_last_4_weeks": active_last_4_weeks, "models": {}}
    for model, licences in models.items():
        costs = _costs(licences, usage_cost_per_week)
        rows = {}
        for name, rate in SCENARIOS.items():
            hours = hours_per_week * rate * 52
            benefit = hours * a["loaded_cost_eur_per_hour"]
            rows[name] = {"realisation_rate": rate, "hours_per_year": round(hours), "benefit_eur": round(benefit),
                          "net_eur": round(benefit - costs), "roi": round((benefit - costs) / costs, 2)}
        out["models"][model] = {"licences": licences, "annual_cost_eur": round(costs), "scenarios": rows}
    out["scenarios"] = out["models"]["all_users"]["scenarios"]   # headline: licences for everyone
    return out


def markdown(bc: dict) -> str:
    a = ASSUMPTIONS
    md = ["# Business case (synthetic pilot data)", "",
          f"Pilot run rate over the last 4 weeks: {bc['reported_hours_saved_per_week']} self-reported hours saved "
          f"per week, {bc['active_users_last_4_weeks']} active users out of {a['users_in_scope']}.", "",
          "## Assumptions", "", "| Item | Value |", "|---|---:|"]
    md += [f"| {k.replace('_', ' ')} | {v:,} |" for k, v in a.items()]
    for model, m in bc["models"].items():
        title = "Licences for every user in scope" if model == "all_users" else "Licences for active users only"
        md += ["", f"## {title}: {m['licences']} licences, annual cost EUR {m['annual_cost_eur']:,}", "",
               "| Scenario | Share of reported savings counted | Hours per year | Benefit | Net | ROI |",
               "|---|---:|---:|---:|---:|---:|"]
        for name, s in m["scenarios"].items():
            md.append(f"| {name} | {s['realisation_rate']:.0%} | {s['hours_per_year']:,} | EUR {s['benefit_eur']:,} | "
                      f"EUR {s['net_eur']:,} | {s['roi']:.0%} |")
    all_base = bc["models"]["all_users"]["scenarios"]["base"]["roi"]
    act_base = bc["models"]["active_users_only"]["scenarios"]["base"]["roi"]
    md += ["", "## Reading", "",
           f"With a licence for everyone, the base case returns {all_base:.0%}: licences for people who rarely use "
           f"the tools cost more than the time saved. Licensing active users only moves the base case to "
           f"{act_base:.0%}. The agents (Policy Digest, Rapid Response) save the most hours per euro, so scaling "
           "them before widening generic licences is the better order.", "",
           "Decision rule proposed: scale a use case when the low scenario is at least break-even and quality "
           "ratings stay at 4/5 or above. Re-measure time saved with a sample of timed tasks, not self-reports only."]
    return "\n".join(md) + "\n"
