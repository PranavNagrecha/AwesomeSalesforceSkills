# Gotchas — Sandbox Refresh Data Strategies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: SandboxPostCopy Runs as Automated Process User — Direct DML Is Governor-Limited

**What happens:** A SandboxPostCopy class performs bulk DML directly in `runApexClass()`. The sandbox refresh completes but the post-copy script produces a governor limit error. The sandbox appears ready but has incomplete reference data, silently breaking subsequent test scenarios.

**Impact:** The failure is reported in the sandbox refresh log as a post-copy script error, not as a sandbox provisioning failure. The sandbox is accessible and appears functional. Tests that depend on the missing reference data fail in non-obvious ways hours later.

**How to avoid:** Never perform large DML directly in the synchronous `runApexClass()` body. Enqueue all substantive data operations as Queueable Apex from within `runApexClass()`. The Queueable chain runs asynchronously with its own governor limits after the refresh completes.

---

## Gotcha 2: Data Seeding Does Not Support Big Objects, Files, or External Objects

**What happens:** A team designs a sandbox data seeding strategy using the native Data Seeding feature, including ContentDocument (Files) as a node in the template. The template creation fails or the seeding job runs but produces no File records.

**Impact:** Any test scenario that requires file attachments cannot rely on native Data Seeding. The team discovers this after building the full template.

**How to avoid:** Review the current Data Seeding exclusion list before including any object in the template design: Big Objects, Files/ContentDocument, Chatter content, external objects, and AgentWork are explicitly not supported. Use a separate SFDMU or Data Loader job for these object types.

---

## Gotcha 3: Sandbox Copy Type Determines What Data Is Available — Not Just Size

**What happens:** A team creates a Developer sandbox expecting it to contain a useful subset of production data. The Developer sandbox contains no records at all (only metadata). The team discovers this after the sandbox refresh, not during planning.

**Impact:** All post-refresh data setup must be done from scratch on a Developer sandbox. If the original plan assumed production data would be present, the entire data preparation timeline must be revised.

**How to avoid:** Know the sandbox copy types: Developer and Developer Pro sandboxes contain only metadata — no production data. Partial sandbox copies include a configurable sample of production data (up to 10,000 records per object). Full sandbox copies include all production data. Choose the sandbox type during the architect/planning phase, not after provisioning.

---

## Gotcha 4: Native Data Seeding Templates Must Be Re-Associated After Sandbox Definition Changes

**What happens:** A team sets up a Data Seeding template and links it to their QA sandbox definition. The sandbox definition is later updated to change the sandbox type or description. The Data Seeding association is silently dropped and post-refresh seeding no longer runs automatically.

**Impact:** The next sandbox refresh completes without data seeding. The QA team notices during smoke testing, not during the refresh cycle. Root cause is non-obvious because the template still exists in Setup.

**How to avoid:** After any change to a sandbox definition, re-verify the Data Seeding template association in Setup > Data Seeding. Treat template-to-sandbox-definition linkage as a post-change checklist item.
