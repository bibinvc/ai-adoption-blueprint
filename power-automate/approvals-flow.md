# Power Automate flow design: parallel approvals for a statement

Design document. Not deployed in a tenant.

**Trigger:** "Start approvals" action from the Rapid Response agent, or a new item in the
SharePoint list `Statements` with status `Ready for approval`.

| Step | Action | Notes |
|---|---|---|
| 1 | Get the draft and the reviewer list from the item | Reviewers: legal liaison, regional head, communications lead |
| 2 | Start an approval with "Everyone must approve", in parallel | Replaces the sequential email chain |
| 3 | Post an adaptive card in the Rapid Response Teams channel | Shows who has approved and who has not |
| 4 | After 2 hours without full approval, send a reminder | Reminder to pending reviewers only |
| 5 | If approved: set status `Approved`, store approvers and timestamps | Audit trail for governance |
| 6 | If rejected: set status `Changes requested`, send comments back to the author | No publication |
| 7 | Write one row to the usage log (tool, minutes, outcome) | Feeds the adoption dashboard |

**Controls:** the flow never publishes; the statement owner publishes after approval. Connection
references use a service account owned by the CA AI team. Flow run history is kept for audit.

**Measures:** waiting time from request to full approval, number of reminders, share approved first time.
