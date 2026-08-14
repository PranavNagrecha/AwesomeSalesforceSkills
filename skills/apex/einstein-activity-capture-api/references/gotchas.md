# Gotchas — Einstein Activity Capture API

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The Activity Timeline UI Does Not Reflect SOQL Reality (Legacy EAC)

**What happens:** Developers see EAC-synced emails and calendar events appearing in the Activity Timeline on a Contact or Opportunity record page and assume those records are queryable via SOQL. When they query `Task`, `Event`, or `EmailMessage`, they get zero rows. No error is raised — the SOQL runs cleanly and returns an empty list.

**When it occurs:** Any **legacy** EAC org where synced activities are only stored in the EAC external store. The timeline UI reads from that store through an internal API that bypasses SOQL entirely.

**How to avoid:** Treat the Activity Timeline as a separate display layer with no guaranteed SOQL backing in legacy EAC. Establish the storage architecture before writing code that depends on `Task` or `EmailMessage` containing EAC records. On legacy EAC use `ActivityMetric` for aggregate reads, noting its Spring '27 retirement; on Sync Email as Salesforce Activity, `Task` and `EmailMessage` are the correct surface and the timeline is backed by real records again.

---

## Gotcha 2: ActivityMetric Has No Rows for Users Without a Connected Account

**What happens:** A bulk query against `ActivityMetric` for a large set of contacts returns partial or no data. The developer thinks EAC is broken or the query is wrong. In reality, `ActivityMetric` only contains rows for contacts/leads whose record owner (or related activity participant) has an active EAC-connected Gmail or Outlook account. Contacts owned by users without a connected account have no metrics at all.

**When it occurs:** Organizations that rolled out EAC partially — some reps connected, others did not — or during sandbox testing where no accounts are connected.

**How to avoid:** Write defensive code that initializes all target contact IDs with a default value (e.g., zero score) before the query loop, so unconnected contacts are handled gracefully rather than silently omitted. Document in the codebase that partial data is expected by design.

---

## Gotcha 3: Legacy EAC Records Cannot Trigger Apex; ActivityMetric Never Accepts Production DML

**What happens:** A developer designs a workflow where EAC email sync should trigger an Apex trigger on `Task` or `EmailMessage` to run downstream logic — for example, updating a last-activity date field. On legacy EAC the trigger never fires, because synced records are not written to the standard object store at all. Similarly, any attempt to use `insert`, `update`, or `delete` on `ActivityMetric` rows in production Apex throws a `System.DmlException` at runtime.

**When it occurs:** On **legacy** EAC, when developers treat it as a standard record source and hook normal trigger or DML patterns onto it. On **Sync Email as Salesforce Activity** the trigger half of this gotcha inverts — captured email is a real `Task` / `EmailMessage`, so an ordinary trigger does fire, and a team that inherited the old advice ships a scheduled batch it no longer needs. The `ActivityMetric` DML half stays true on both architectures.

**How to avoid:** On legacy EAC, do not design trigger-driven workflows that depend on EAC sync events. If downstream logic must react to EAC activity, schedule a batch or use a scheduled flow that queries `ActivityMetric` periodically. Never attempt production DML on `ActivityMetric` — it is a read-only object maintained by the EAC sync engine. DML on ActivityMetric is valid only inside `@isTest` contexts for test data seeding.

---

## Gotcha 4: EAC Report Types Cannot Be Joined with Standard Activities (Legacy EAC)

**What happens:** A report builder creates an "Einstein Activity Capture" report type and tries to add cross-object columns from standard Task/Event fields, or tries to combine EAC metrics with Opportunity data in the same report. The standard Activities report type does not include EAC-sourced rows. The two report type families are separate and cannot be combined in a single report.

**When it occurs:** When business users want a unified activity report covering both manually logged Salesforce activities (Tasks, Events) and EAC-synced emails and meetings. This is a common reporting requirement that EAC's architecture cannot satisfy with a single report type.

**How to avoid:** Build two separate reports — one using the EAC report type for synced activity metrics, one using the standard Activities report type for logged activities — and combine them in a dashboard. Better, move the org to **Sync Email as Salesforce Activity**, which stores captured email as standard Activity records — "Auto-captured emails are now included in standard report types and appear as standard Tasks" — and makes the single unified report the business asked for possible via **Activities with Accounts** or **Activities with Opportunities**. This is the direction Salesforce is forcing anyway: the dedicated EAC reporting layer retires in Spring '27 (see Gotcha 6).

---

## Gotcha 5: Sandbox EAC Returns No Data and Cannot Be Reliably Tested

**What happens:** A developer builds Apex code that queries `ActivityMetric` in a full or partial sandbox. The sandbox does not carry over EAC connected account connections from production. All `ActivityMetric` queries return zero rows. The developer cannot verify whether the logic is correct or whether EAC data simply does not exist in the sandbox.

**When it occurs:** Any sandbox environment, including full sandboxes with data copied from production. EAC connected account credentials are not portable to sandboxes. Even if the Activity Timeline shows historical data in sandbox (from a pre-sandbox-refresh snapshot), ActivityMetric may be stale or absent.

**How to avoid:** Write test classes that seed `ActivityMetric` rows in `@isTest` context (ActivityMetric supports DML in test contexts). For end-to-end validation, test in the production org or a Developer Edition org with a live connected account. Document explicitly in the test class that a connected account is required for live validation.

---

## Gotcha 6: Activity Metrics Returns Null Long Before It Is Removed, and Nothing Throws

**What happens:** A working engagement-score class that reads `ActivityMetric.EmailCount` starts scoring every contact zero. Nothing errors. Salesforce Help is explicit that the failure mode is silence, not an exception: "Activity Metrics fields no longer populate. Custom code or reports referencing these fields return null values." The business reads the output as a collapse in customer engagement and acts on it.

**When it occurs:** Ahead of the Spring '27 (February 2027) retirement of **Activity Metrics**, the **Activities Dashboard**, **Recommended Connections** and **A360 Reports** — the last of which takes `UnifiedEmail`, `UnifiedEmailParticipant`, `UnifiedMeeting`, `UnifiedMeetingParticipant`, `UnifiedTask` and `UnifiedTaskParticipant` with it: "Report types and their underlying objects are retired, meaning existing reports using these objects stop returning data."

The trap is that a seeded test suite cannot see this. `@isTest` code inserts its own `ActivityMetric` rows and asserts against them, so every test stays green while production returns null. Test coverage is not evidence here.

**How to avoid:** Audit rather than wait — Help's instruction is to "Search your Apex, flows, and validation rules for references to Activity Metrics fields, for example, the ActivityMetric object"; `scripts/check_einstein_activity_capture_api.py` runs that scan. Migrate reads to standard `Task` / `EmailMessage` aggregation ("Recreate your activity reporting on Task and EmailMessage objects grouped by Account or Opportunity"), and for scores that must stay queryable, "use flows or scheduled jobs to compute and persist engagement scores into custom fields" — a custom field you own has no retirement date. Salesforce's own timeline is audit by June 2026, build replacements June–December 2026, validate in a sandbox January 2027.
