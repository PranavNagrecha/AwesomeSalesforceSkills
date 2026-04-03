# Examples - Salesforce Connect External Objects

## Example 1: ERP Order Status Without Replication

**Context:** Sales users need current order shipment status from ERP while working in Salesforce.

**Problem:** A nightly ETL copy would already be stale.

**Solution:** Expose the ERP order table through Salesforce Connect as an External Object and place the relevant fields on order-related record pages for lookup and decision support.

**Why it works:** The source system remains authoritative and users see current data without a full replication pipeline.

---

## Example 2: Hybrid Model For Hot Subset Data

**Context:** A support team needs live contract details from an external billing system, but also needs native reporting on renewal risk.

**Problem:** Pure virtualization cannot satisfy every reporting and automation need.

**Solution:** Keep the full contract catalog external, but replicate only the narrow summary fields needed for internal workflow and reporting.

**Why it works:** The design avoids copying everything while still meeting native-platform needs where they are real.

---

## Anti-Pattern: Treating `__x` Like Native `__c`

**What practitioners do:** They design pages, triggers, and reports as if external objects have the same behavior and latency profile as local data.

**What goes wrong:** Performance, reporting, and automation expectations all break late in the project.

**Correct approach:** Validate which features truly work for the use case before committing to virtualization.
