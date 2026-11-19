# Responsible AI, privacy and security rules for the programme

| Area | Rule | Where it is applied |
|---|---|---|
| Human oversight | AI prepares, a person approves anything that leaves the team | Agent designs, approvals flow |
| Transparency | AI-generated drafts and answers are labelled | Agent designs, digest header |
| Sources | Positions and summaries link to their source; no source, no claim | Rapid Response agent, Policy Digest |
| Privacy | Usage logs keep pseudonymous user ids; free-text comments are masked | `aab/lake.py` silver layer |
| Data quality | Bad rows are quarantined with a reason, not dropped silently | `aab/lake.py`, `quality_report.json` |
| Ownership | Every dataset has a named data curator role | `out/lake/catalog.json` |
| Portfolio | No use case moves to pilot or scale without responsible AI and privacy reviews | `governance/ai_portfolio.csv`, `aab/portfolio.py` |
| Security | Agents use the signed-in user's permissions; flows use an owned service account | Agent and flow designs |
| Regulation | Use cases are screened against the EU AI Act and data protection law before pilots | Portfolio review step |
