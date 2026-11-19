# Power BI report design

Data: the CSV files in `out/lake/gold/` after `python -m aab.run` (or `evidence/gold/`).

| Table | Grain | Key | Relationship |
|---|---|---|---|
| fact_usage | one use of an AI tool | event_id | many-to-one to the three dimensions |
| dim_user | one licensed user | user_id | function, region, market |
| dim_tool | one tool | tool | assistant, agent or flow |
| dim_date | one day | date_key | week number of the pilot |

Measures are in `measures.dax`: adoption rate, active users, reported and counted hours saved,
average quality and rated share, cost per hour saved, uses per active user.

Report pages:

1. **Adoption**: adoption rate card, weekly active users line, adoption by region and function,
   slicers on region, market and function.
2. **Impact**: hours saved by tool and task, quality by tool, cost per hour saved.
3. **Data quality**: rows accepted and quarantined per check, from `quality_report.json`.

`out/adoption_dashboard.html` is a static preview of pages 1 and 2 built from the same gold tables.
The report itself was not built in Power BI for this repository.
