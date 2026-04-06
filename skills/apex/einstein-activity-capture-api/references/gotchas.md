# Gotchas — Einstein Activity Capture API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Activity Timeline UI Does Not Reflect SOQL Reality

**What happens:** Developers see EAC-synced emails and calendar events appearing in the Activity Timeline on a Contact or Opportunity record page and assume those records are queryable via SOQL. When they query `Task`, `Event`, or `EmailMessage`, they get zero rows. No error is raised — the SOQL runs cleanly and returns an empty list.

**When it occurs:** Any standard EAC org (without Write-Back enabled) where synced activities are only stored in the EAC external store. The timeline UI reads from that store through an internal API that bypasses SOQL entirely.

**How to avoid:** Treat the Activity Timeline as a separate display layer with no guaranteed SOQL backing in standard EAC. Use `ActivityMetric` for any aggregate reads and verify Write-Back status before writing code that depends on `Task` or `EmailMessage` containing EAC records.

---

## Gotcha 2: ActivityMetric Has No Rows for Users Without a Connected Account

**What happens:** A bulk query against `ActivityMetric` for a large set of contacts returns partial or no data. The developer thinks EAC is broken or the query is wrong. In reality, `ActivityMetric` only contains rows for contacts/leads whose record owner (or related activity participant) has an active EAC-connected Gmail or Outlook account. Contacts owned by users without a connected account have no metrics at all.

**When it occurs:** Organizations that rolled out EAC partially — some reps connected, others did not — or during sandbox testing where no accounts are connected.

**How to avoid:** Write defensive code that initializes all target contact IDs with a default value (e.g., zero score) before the query loop, so unconnected contacts are handled gracefully rather than silently omitted. Document in the codebase that partial data is expected by design.

---

## Gotcha 3: EAC Records Cannot Trigger Apex and Cannot Be Targeted by Production DML

**What happens:** A developer designs a workflow where EAC email sync should trigger an Apex trigger on `Task` or `EmailMessage` to run downstream logic — for example, updating a last-activity date field. The trigger never fires for EAC-synced records because they are not written to the standard object store. Similarly, any attempt to use `insert`, `update`, or `delete` on `ActivityMetric` rows in production Apex throws a `System.DmlException` at runtime.

**When it occurs:** When developers treat EAC as a standard record source and try to hook normal trigger or DML patterns onto it.

**How to avoid:** Do not design trigger-driven workflows that depend on EAC sync events. If downstream logic must react to EAC activity, schedule a batch or use a scheduled flow that queries `ActivityMetric` periodically. Never attempt production DML on `ActivityMetric` — it is a read-only object maintained by the EAC sync engine. DML on ActivityMetric is valid only inside `@isTest` contexts for test data seeding.

---

## Gotcha 4: EAC Report Types Cannot Be Joined with Standard Activities

**What happens:** A report builder creates an "Einstein Activity Capture" report type and tries to add cross-object columns from standard Task/Event fields, or tries to combine EAC metrics with Opportunity data in the same report. The standard Activities report type does not include EAC-sourced rows. The two report type families are separate and cannot be combined in a single report.

**When it occurs:** When business users want a unified activity report covering both manually logged Salesforce activities (Tasks, Events) and EAC-synced emails and meetings. This is a common reporting requirement that EAC's architecture cannot satisfy with a single report type.

**How to avoid:** Build two separate reports — one using the EAC report type for synced activity metrics, one using the standard Activities report type for logged activities — and combine them in a dashboard. Alternatively, use a Write-Back-enabled EAC configuration (Summer '25+) which copies synced records into standard storage and makes them available in standard report types.

---

## Gotcha 5: Sandbox EAC Returns No Data and Cannot Be Reliably Tested

**What happens:** A developer builds Apex code that queries `ActivityMetric` in a full or partial sandbox. The sandbox does not carry over EAC connected account connections from production. All `ActivityMetric` queries return zero rows. The developer cannot verify whether the logic is correct or whether EAC data simply does not exist in the sandbox.

**When it occurs:** Any sandbox environment, including full sandboxes with data copied from production. EAC connected account credentials are not portable to sandboxes. Even if the Activity Timeline shows historical data in sandbox (from a pre-sandbox-refresh snapshot), ActivityMetric may be stale or absent.

**How to avoid:** Write test classes that seed `ActivityMetric` rows in `@isTest` context (ActivityMetric supports DML in test contexts). For end-to-end validation, test in the production org or a Developer Edition org with a live connected account. Document explicitly in the test class that a connected account is required for live validation.
