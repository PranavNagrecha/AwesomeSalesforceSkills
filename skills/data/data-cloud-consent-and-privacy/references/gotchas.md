# Gotchas — Data Cloud Consent and Privacy

## Gotcha 1: Consent Is Not Automatically Enforced at Query Time

**What happens:** Opted-out customers appear in Data Cloud segments and activation exports despite having `ssot__ContactPointConsent__dlm` records with `Status = 'OptOut'`.

**When it occurs:** When segment builders create population segments without explicitly joining to the ContactPointConsent DMO and filtering on `Status = 'OptIn'`.

**How to avoid:** Treat consent as an explicit filter requirement for every marketing or activation segment. Document this as a standard segment review step. Add a consent filter audit to segment QA checklists.

---

## Gotcha 2: Deletion Does Not Cascade to Downstream Systems

**What happens:** An org processes a GDPR Right to Be Forgotten request via Privacy Center. The customer's unified profile is erased from Data Cloud within 90 days. However, the customer's email address, order history, and personal data still appear in Marketing Cloud, ad platform custom audiences, and the external data warehouse — because deletion does not automatically cascade downstream.

**When it occurs:** Every time a deletion request is processed without a coordinated downstream deletion strategy.

**How to avoid:** Maintain an inventory of all systems seeded with Data Cloud activation data. For each deletion request, trigger parallel deletion processes in all downstream systems: Marketing Cloud subscriber deletion, ad platform audience suppression list updates, data warehouse purge jobs.

---

## Gotcha 3: Retention Policy Applied After Ingestion Cannot Retroactively Purge

**What happens:** An organization realizes it has been retaining Data Lake Object data for 3 years but the legal requirement is 1 year. Setting a retention policy to 365 days does not immediately purge the excess 2 years of data — the policy applies to records written after the policy is configured.

**When it occurs:** When retention policies are configured after significant data has been ingested.

**How to avoid:** Configure retention policies before data ingestion begins. For orgs that need to retroactively purge existing data, use the Data Deletion API to submit deletion requests for records outside the required retention window.

---

## Gotcha 4: CCPA Do Not Sell Has No Default Data Use Purpose

**What happens:** An organization wants to honor California CCPA "Do Not Sell My Personal Information" requests via Data Cloud consent management. There is no built-in "Do Not Sell" Data Use Purpose — consent records created without the correct custom purpose do not prevent sale of data in downstream activations.

**When it occurs:** When CCPA opt-outs are recorded in Data Cloud without a purpose-specific consent configuration.

**How to avoid:** Create a custom Data Use Purpose named "Do Not Sell" or equivalent. Map all CCPA opt-out signals to this custom purpose. Ensure all data sale-related activation targets filter on this consent purpose.

---

## Gotcha 5: Consent Write Propagation Is Not Instantaneous

**What happens:** A customer opts out via a web form at 9:00 AM. At 9:05 AM, a batch activation job runs and includes the customer in a Marketing Cloud send — because the consent record has not yet propagated through the Data Cloud pipeline.

**When it occurs:** When consent records are written to `ssot__ContactPointConsent__dlm` via Ingestion API (streaming, ~3-minute batch window) and activation runs immediately after.

**How to avoid:** Design a buffer period between consent record ingestion and activation job execution. For real-time consent enforcement, consider implementing consent checks directly in the activation system rather than relying solely on Data Cloud segment filters.
