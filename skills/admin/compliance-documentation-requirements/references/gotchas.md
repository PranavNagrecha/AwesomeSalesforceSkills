# Gotchas — Compliance Documentation Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Field Audit Trail Is a Shield Add-On, Not a Base FSC Feature

**What happens:** Admins enable standard field history tracking on KYC objects and configure the 20-field maximum, believing this satisfies multi-year regulatory retention requirements. Without Field Audit Trail, field history is kept up to 18 months, and up to 24 months via the API (secguide 262 L4632-4633). Years later, during a regulatory audit with a 5-year lookback, the historical field values are gone and cannot be recovered.

**When it occurs:** Any FSC org where Field Audit Trail has not been explicitly licensed and configured as part of the compliance architecture. This is especially common when the Salesforce implementation team and the compliance team are not aligned on retention obligations at implementation time.

**How to avoid:** At project start, identify the regulatory retention period for each data type (field-level changes, document metadata, screening results, risk decisions). If any obligation exceeds 18 months for field-level data, confirm that Shield (which includes Field Audit Trail, secguide 262 L297-298) is licensed and a `HistoryRetentionPolicy` is deployed through Metadata API before go-live (secguide 262 L4833-4835). Document the Shield dependency explicitly so it is not cut from scope during cost reviews.

---

## Gotcha 2: FSC Has No Native AML Engine — PartyScreeningSummary Does Not Self-Populate

UNVERIFIED (2026-10-20): FSC's lack of a screening engine — no corpus line describes `PartyScreeningSummary` behaviour.

**What happens:** Admins enable the FSC KYC feature and see `PartyScreeningSummary` on the object list and assume FSC will populate it during onboarding. No screening occurs. `PartyScreeningSummary` records remain empty unless an explicit third-party integration writes to them. The org appears KYC-compliant (the objects exist) but no actual screening is happening.

**When it occurs:** Any FSC deployment where the AML screening integration was deferred, descoped, or assumed to be native. This is especially dangerous in go-live scenarios where the KYC data model is visible but the integration is not yet live.

**How to avoid:** Treat `PartyScreeningSummary` as a write target, not a source of truth. It holds only what the integration puts there. Before go-live, verify that every onboarded individual has at least one `PartyScreeningSummary` record with a vendor-supplied case reference and a non-null screening result. Add a validation check to the onboarding workflow that blocks account opening if no screening record exists.

---

## Gotcha 3: Setup Audit Trail Retains Only 180 Days Without External Archival

**What happens:** Admins point to the Setup Audit Trail as evidence that no unauthorized configuration changes occurred during an audit period. If the audit period extends beyond 180 days (which most annual regulatory audits do), the earliest entries have already been deleted — after 180 days setup entity records are deleted (secguide 262 L4974-4975). The trail appears shorter than the audit window.

**When it occurs:** Any org that has not established a periodic Setup Audit Trail export and archive process. The 180-day limit applies to all Salesforce orgs (UNVERIFIED (2026-10-20): regardless of Shield licensing — the corpus is silent on Shield and Setup Audit Trail).

**How to avoid:** Schedule a recurring Apex job or Data Export Service task that queries `SetupAuditTrail` (object_reference 264 L264576) via SOQL and writes the results to an external archive (e.g., S3, SharePoint) monthly. Set the schedule interval to less than 180 days to ensure no entries roll off before being captured. Document the archival process and retention location as part of the compliance documentation package.

---

## Gotcha 4: Per-User Named Credential Authentication Fails in Batch and Scheduled Contexts

UNVERIFIED (2026-10-20): this gotcha's failure mode — the corpus defines PerUserPrincipal ("access control at the individual user level", api_meta 264 L66350) but documents no failure in batch, scheduled or event contexts, nor the `CalloutException`.

**What happens:** The AML screening integration is built using a Named Credential configured with Per-User OAuth authentication. The integration works perfectly when triggered interactively by an agent (who has an active session). When the same integration is invoked from a batch re-screening job, a scheduled Apex class, or a Platform Event trigger, the callout throws a `CalloutException` because there is no user session to resolve the OAuth token. Re-screening jobs fail silently or produce error logs that are not reviewed.

**When it occurs:** Any Named Credential-backed integration that runs in headless execution contexts (batch, scheduled, future, Platform Event subscribers, Apex triggers on bulk DML).

**How to avoid:** Use Named Principal (org-level) authentication on Named Credentials that back automated compliance workflows. Named Principal authentication stores a service account credential at the org level and resolves it without a user session. Per-User authentication is only appropriate for integrations that are exclusively interactive and user-initiated.

---

## Gotcha 5: PartyIdentityVerification and IdentityDocument Require an Individual Record Parent

UNVERIFIED (2026-10-20): that these objects look up `Individual` — the corpus documents `Individual` as the data privacy record (object_reference 264 L158005-158006) and `Contact.IndividualId` as available when Data Protection and Privacy is enabled (L71890-71891).

**What happens:** KYC objects are configured and the onboarding flow creates Contact records, but `PartyIdentityVerification` and `IdentityDocument` records cannot be created because there is no linked `Individual` record. The error message references the lookup field but the root cause — missing Individual record — is not immediately obvious. In some legacy orgs, bulk-imported contacts were created without Data Protection and Privacy linking, leaving thousands of contacts orphaned from the Individual object.

**When it occurs:** Orgs where contacts were created before FSC was enabled, or where the bulk data migration did not include Individual record creation and linking. Also occurs when the onboarding flow creates Contact records but does not include a step to verify or create the linked Individual.

**How to avoid:** At the start of the onboarding flow, check whether the Contact has a non-null `IndividualId` field. If not, create the `Individual` record first and populate `Contact.IndividualId` before attempting to create any KYC child records. For existing data migration scenarios, run a pre-migration audit query to count contacts with null `IndividualId` and create Individual records in bulk before enabling the KYC workflow.
