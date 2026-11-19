# Copilot Cowork: two custom skills for the pilots

Copilot Cowork in Microsoft 365 carries out multistep tasks across Word, Outlook, Teams and
SharePoint, and asks for approval before sensitive actions such as sending an e-mail or posting in
Teams. A custom skill is a `SKILL.md` file with a name and a description, stored in OneDrive under
`/Documents/Cowork/skills/<skill-name>/SKILL.md`.

The two skills in this folder are written in that format for the two pilots of the blueprint.
They are prototypes. They were not run in a company tenant as part of this repository.

| Skill | Pilot | How it is started | Approval point |
|---|---|---|---|
| [`weekly-policy-digest`](skills/weekly-policy-digest/SKILL.md) | Policy Intelligence Reporting | Scheduled task every Friday at 10:00 | Before the e-mail to the Policy team is sent |
| [`rapid-response-brief`](skills/rapid-response-brief/SKILL.md) | Rapid Response | Event: a "Rapid Response" e-mail in the shared mailbox, or on request | Before the post in the Rapid Response Teams channel |

## Why Cowork for these two

- Both tasks are a chain of small steps across several apps: read a list, write a Word file, send
  or post. That is what Cowork is built for. Copilot Chat would need a person to copy between apps.
- Both have one clear moment where a person must decide. Cowork's approval prompt covers that
  moment without building a separate flow.
- The heavier, rule-based part (parallel approvals with reminders and an audit trail) stays in
  Power Automate, see [`../power-automate/approvals-flow.md`](../power-automate/approvals-flow.md).

## Controls

| Control | How |
|---|---|
| Permissions | Cowork runs with the signed-in user's permissions, so it only sees what that person can see |
| Sources | The skills read only the validated news list and the approved positions library |
| Human approval | Sending and posting always go through the approval prompt; nothing is published by the skill |
| Custom skills are not checked by Microsoft | Every skill change is reviewed by the process lead and listed in `governance/ai_portfolio.csv` |
| Data location | Check which models are allowed for the tenant and its data boundary before the pilot |
| Cost | Cowork is billed by usage; a spending limit is set per pilot group and usage cost is added to the "cost per hour saved" KPI |

## Test before the pilot

| # | Test | Expected |
|---|---|---|
| 1 | Week with 9 validated items, one high severity | Digest with 4 regions, one item under For Rapid Response, approval asked before sending |
| 2 | Item with no source link in the list | Item left out |
| 3 | Week with 2 items | E-mail says only 2 items were found |
| 4 | Rapid Response request on a topic with no approved position | Brief says no approved position exists, no invented text |
| 5 | Request that is a legal question | Skill stops and points to the legal liaison |
| 6 | News text containing an e-mail address | Address not copied into the brief or digest |

## How it feeds the KPIs

Each run is logged as one usage event (tool, task, minutes saved, quality rating), the same format
as the usage log built by `aab/synth.py`, so the adoption dashboard and the business case include Cowork
next to the other tools.
