# Requirement — Northwind sales process for the Enterprise team

Northwind's Enterprise sales team (12 reps, 2 managers, 1 sales ops admin) needs a proper opportunity process in
Salesforce. Today every deal sits in one generic pipeline. We want:

1. A dedicated Enterprise sales process with these stages, in order: Qualify, Discover, Propose, Negotiate,
   Closed Won, Closed Lost. Each stage should have a probability and an exit checklist reps see on the record
   (what must be done before moving on). Renewals use a separate, shorter process: Renewal Review, Renewal Proposed,
   Closed Won, Closed Lost.
2. Products: reps add products from our price book to every Enterprise opportunity; an opportunity cannot move to
   Propose without at least one product line, and cannot close won with a discount above 20% unless a manager
   approves it.
3. That manager approval must be a formal approval: the rep submits, the manager approves or rejects, the outcome and
   comments stay on the record, and the opportunity is locked while pending.
4. On the record page, reps should see the stage path with the checklist and key fields per stage, plus a small
   component that shows the discount, the approval status and a "Submit for approval" button that is only enabled
   when the discount rule requires it.
5. Managers need a report of open Enterprise opportunities by stage with amount and discount, and a dashboard tile of
   the pipeline by close month.
6. Nothing should break the existing generic process for the SMB team. No integrations, no data migration.

Asked by: VP Sales Operations (Pranav), 2026-09-12. We have a production org with Sales Cloud Enterprise; the SMB
process exists; this build is designed standalone and may assume the standard Opportunity object, Product2 and a
"Standard Price Book".
