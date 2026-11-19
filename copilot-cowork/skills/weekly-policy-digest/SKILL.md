---
name: weekly-policy-digest
description: Prepare the weekly Corporate Affairs policy digest from the validated news list in SharePoint, grouped by region, with a source link for every item, and send it to the Policy team only after approval.
---

# Weekly policy digest

Use this skill every Friday, or when someone asks for the weekly policy digest.

## Inputs

- SharePoint list **Policy news (validated)**, filled from the silver layer of the data lake.
  Use only items published in the last 7 days. Ignore any item without a market or a source link.
- Word template **Policy digest template.docx** in the Corporate Affairs AI library.

## Steps

1. Read the validated news items for the last 7 days.
2. Group them by region: Europe, Americas, Asia-Pacific, Middle East & Africa.
3. In each region keep the 5 most important items. High severity first, then AI regulation,
   taxation and packaging topics.
4. For each item write one line: title, severity, topic, one sentence of summary, source link.
   Use only what the source says. Do not add figures, quotes or opinions.
5. List every high severity item in a separate section called **For Rapid Response**.
6. Fill the Word template and save it as `Policy digest YYYY-MM-DD.docx` in the same library.
7. Write the e-mail to the Policy team distribution list with the file attached.
   Mark it as an AI-prepared draft. Ask for approval before sending.

## Rules

- No source link, no line in the digest.
- Never send, post or share without approval.
- Do not copy personal data (names of private persons, e-mail addresses, phone numbers) from the
  news text.
- If fewer than 3 items were found, say so in the e-mail instead of filling space.
