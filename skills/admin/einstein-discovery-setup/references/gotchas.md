# Gotchas — Einstein Discovery Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Refreshed Model Is NOT Automatically Activated — Scoring Silently Runs Against Old Model

**What happens:** After a model refresh job completes successfully, the new model version sits in "Ready" status in the Model Manager. The prediction definition continues using the previous model version for all bulk scoring jobs and API calls. There is no error, no warning, and no notification in the UI or via email that indicates scoring is now against a stale model.

**When it occurs:** Every time a model refresh job completes, whether triggered manually or on a schedule. The activation step is always manual. Admins who set up scheduled refreshes and assume scoring automatically uses the latest model will silently accumulate model drift over weeks or months.

**How to avoid:** After every refresh job completes, navigate to Analytics Studio > story > Model Manager, review the new model's accuracy metrics, and explicitly click "Activate" on the new version. Then trigger a new bulk scoring job. Document this as a required operational step in the admin runbook and set a calendar reminder or notification to perform it after each scheduled refresh window.

---

## Gotcha 2: Writeback Field Is Read-Only — Not Updated on Record Save or Field Change

**What happens:** The Einstein Discovery writeback field is system-managed and read-only. It cannot be updated by users, Flow, triggers, Process Builder, or direct DML. Editing the source record (changing Stage, updating Amount, modifying related fields) does not cause the writeback field to refresh. The score shown on the record page is the value from the last bulk scoring job or API call — which may be hours, days, or weeks old.

**When it occurs:** Anytime a user edits a record and expects to see an updated prediction score, or when a Flow or automation is designed to trigger re-scoring by updating source fields. This also catches admins who add validation rules or triggers that check the writeback field value expecting it to be current.

**How to avoid:** Treat the writeback field as a snapshot that is updated by scheduled bulk jobs, not a live calculated field. Design workflows with the assumption that scores are as old as the last scoring job. If fresher scores are needed, configure more frequent bulk scoring jobs or use the developer API to trigger explicit scoring at known points in the business process.

---

## Gotcha 3: Maximum Three Writeback Fields Per Salesforce Entity

**What happens:** Each Salesforce object can have at most three Einstein Discovery writeback fields across all deployed prediction definitions. If an object already has three writeback fields and a new prediction is deployed with writeback enabled on the same object, the deployment fails with a limit error. The story trains successfully but the writeback field creation step fails.

**When it occurs:** Most commonly on high-value objects like Opportunity or Contact, where multiple teams independently configure Einstein Discovery predictions — for example, one for win probability, one for churn risk, and one for expansion potential. The fourth deployment attempt fails even if the existing fields are from inactive or rarely used predictions.

**How to avoid:** Before deploying a new prediction on any object, audit the existing writeback fields in Setup > Object Manager > [Object] > Fields & Relationships and filter by field label or type for Einstein-managed fields. If the object already has three, identify which existing writeback field is the least valuable and remove it (via the Deploy tab of the relevant story) before creating a new one.

---

## Gotcha 4: Field-Level Security on Writeback Field Is Not Granted Automatically

**What happens:** Einstein Discovery creates the writeback field and populates it via scoring jobs, but does not assign field-level security to any profile, role, or permission set. The field exists in the database and holds prediction scores, but no user — including system administrators — can see it in reports, list views, or record page layouts until FLS is manually assigned.

**When it occurs:** Immediately after writeback field creation. The bulk scoring job runs and writes values to the field, but the ops team opens a report expecting to see scores and finds the column empty or the field unavailable in the field picker.

**How to avoid:** As part of every new prediction deployment, immediately navigate to Setup > Object Manager > [Object] > Fields & Relationships, locate the new writeback field, open Field-Level Security, and grant Read access to all relevant profiles and permission sets. This is a mandatory post-deployment step that is easy to forget because the scoring job completes without any FLS-related warning.
