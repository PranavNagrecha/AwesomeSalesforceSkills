# Gotchas — AML/KYC Process Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Synchronous Callouts Are Blocked in Record-Triggered Flow Bulk Context

**What happens:** A record-triggered Flow that calls an Integration Procedure or Apex action making an HTTP callout will run successfully for single-record saves in a UI context, but will throw a `System.CalloutException: You have uncommitted work pending` error when the same Flow is triggered by a bulk data load (Data Loader, mass import, batch Apex DML on more than one record). This silently fails for some records and produces a misleading error that appears to be a transaction conflict, not a callout restriction.

**When it occurs:** Any time AML screening is triggered by a record-triggered Flow and more than one record is saved in the same transaction — including API imports, sandbox refresh seeding, or even a "Select All + Edit" from a list view if the records meet the trigger criteria.

**How to avoid:** Never put the AML screening callout inside the synchronous record-triggered Flow path. Use one of these patterns instead: (1) have the record-triggered Flow publish a Platform Event and let a separate subscriber make the callout, (2) have the record-triggered Flow enqueue a Queueable Apex job that makes the callout asynchronously, or (3) use OmniStudio Integration Procedures triggered by user action in an OmniScript rather than by record save.

---

## Gotcha 2: Per-User Named Credentials Fail in Batch and Scheduled Apex

**What happens:** A Named Credential configured with `Per-User` authentication requires an active user session to resolve the OAuth token. When the AML screening batch job runs at 2 AM in a scheduled Apex context, there is no user session. The callout throws `System.CalloutException: Named credential authentication failed` without a clear explanation of why it works for interactive users but fails for the batch.

**When it occurs:** Any Apex executing outside an interactive user session: `Database.Batchable`, `Schedulable`, `@future` methods, Platform Event triggers, and Queueable Apex spawned from non-interactive contexts.

**How to avoid:** Use `Named Principal` (org-wide) authentication for any Named Credential that backs an AML screening integration running in batch or async context. The credential authenticates as the integration's service account rather than as the individual user. Store the client ID/secret or API key as an External Credential with a Named Principal policy. Document this explicitly in the integration design because auditors will ask how screening-vendor credentials are managed.

---

## Gotcha 3: PartyProfileRisk Is a Child of Individual, Not Account or Contact

**What happens:** The `PartyProfileRisk` object is a child of `Individual` in the FSC data model. Attempting to create a `PartyProfileRisk` record with only an `AccountId` or `ContactId` — without the corresponding `IndividualId` — results in a required-field validation error. In orgs where FSC was enabled on top of an existing Sales Cloud deployment, many pre-existing Contacts do not have `Individual` records or the `IndividualId` lookup on the Contact is null. The screening workflow creates the `PartyProfileRisk` but cannot associate it with the customer, making the record orphaned and invisible from the Account page layout.

**When it occurs:** First encountered during the initial bulk migration of existing accounts into the AML screening workflow; also triggered when new Contacts are created via API integration that does not go through an FSC-aware onboarding process.

**How to avoid:** Add a pre-screening validation step to the orchestration layer that checks whether `Contact.IndividualId` is populated. If it is null, the step must create an `Individual` record and stamp the `IndividualId` on the Contact before proceeding. This logic belongs in the Integration Procedure or the Apex pre-flight check, not in the screening callout itself. Include an `Individual` record count in the architecture's data quality baseline.

---

## Gotcha 4: Platform Event Delivery Is At-Least-Once, Not Exactly-Once

**What happens:** In the asynchronous screening pattern, the batch job publishes a `ScreeningResult__e` Platform Event and a trigger updates `PartyProfileRisk`. Platform Events are guaranteed to be delivered at least once but may be delivered multiple times if the subscriber transaction fails and retries. They are also not guaranteed to be processed in the order they were published. For AML workflows this means a result from a re-screening triggered by a data change could be overwritten by a delayed delivery of the original nightly screening result, causing the risk rating to silently regress to a stale value.

**When it occurs:** High-throughput screening batches, periods of org instability causing subscriber transaction rollbacks, or when two screening triggers fire for the same customer in rapid succession (e.g., an annual review and a change-triggered re-screen on the same day).

**How to avoid:** Include a `ScreeningTimestamp__c` field on the Platform Event. In the subscriber trigger, compare the event's timestamp against the `LastModifiedDate` of the existing `PartyProfileRisk` record. Only apply the update if the event timestamp is later than the existing record's last modification. This idempotency check costs one SOQL query per event but prevents silent risk-rating regression.

---

## Gotcha 5: FSC Identity Verification Has No AML/Sanctions Screening Capability

**What happens:** The FSC Identity Verification feature (configurable in Setup > Identity Verification) is sometimes presented to compliance teams as the Salesforce KYC check. The feature passes UI acceptance testing because it correctly validates identity questions against stored data. However, it contains no connection to any sanctions list, PEP database, or adverse media source. An implementation that relies on it for AML compliance will pass functional UAT and fail regulatory examination.

**When it occurs:** Most commonly in projects where a Salesforce admin configures Identity Verification without involving a compliance officer or reviewing the AML program requirements; also common when a pre-sales demo of FSC emphasizes Identity Verification and the customer interprets it as covering all KYC requirements.

**How to avoid:** Explicitly document in the architecture decision record that FSC Identity Verification serves contact-center caller authentication only, and that AML/KYC sanctions screening requires a separate integration to a third-party screening vendor. Include this distinction in the solution design sign-off checklist. The compliance officer must confirm in writing that the screening vendor integration — not Identity Verification — satisfies the institution's AML program screening requirement.
