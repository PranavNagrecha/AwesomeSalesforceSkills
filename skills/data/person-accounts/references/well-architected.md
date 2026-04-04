# Well-Architected Notes — Person Accounts

## Relevant Pillars

- **Scalability** — Person Account orgs with large consumer volumes (millions of records) face specific SOQL and reporting scaling concerns. Contact queries that inadvertently include PersonContact records double the effective result set. Report filters must be designed early to avoid full-table scans across both Account types. Index strategy for Person Account-specific fields (PersonEmail, PersonPhone) should be planned before volume grows.
- **User Experience** — Person Accounts directly impact the Lightning page layout, record home configuration, and search result presentation. Separate page layouts and compact layouts for Person Account vs Business Account record types are required for a coherent UI. Agents and service reps working in a mixed B2B+B2C org need clear visual differentiation between person and business records to avoid confusion and data entry errors.
- **Security** — Sharing rules, OWD, and record-level security apply to Person Accounts via the Account object. Orgs that previously scoped sharing configurations only to Contact may have gaps — Person Accounts are visible to users with Account read access, not Contact read access. Field-level security for Person-prefixed fields (PersonEmail, PersonSSN if customized) must be reviewed separately from standard Account fields.
- **Reliability** — The irreversibility of Person Account enablement is the primary reliability concern. A misconfigured enablement in production cannot be rolled back. Trigger and automation reliability depends on correct `IsPersonAccount` branching — missing checks cause logic to apply incorrectly to the wrong account type, producing silent data integrity failures.
- **Operational Excellence** — Mixed B2B+B2C orgs require clear documentation of data model decisions, record type conventions, and code branching patterns so that future developers understand the constraints. Without this, new code routinely fails to handle Person Accounts correctly and requires rework.

---

## Architectural Tradeoffs

**B2C-only vs Mixed B2B+B2C:** Pure B2C orgs can use Person Accounts uniformly — every Account is a person. This is the simplest model. Mixed orgs gain flexibility but require explicit branching everywhere: in Apex, in SOQL, in reports, and in integrations. The operational overhead of a mixed model is significant and should be justified by clear business need (e.g., an FSC org with both individual clients and institutional accounts).

**Person Account vs Account+Contact for B2C:** The alternative to Person Accounts in a B2C context is a standard Account (often a dummy "household" or person-named account) with a single Contact child. This avoids the irreversibility of Person Account enablement, but creates a two-record model for one person — complicating deduplication, API payloads, and UI. Person Accounts are the platform-endorsed model for B2C and are required by Health Cloud and FSC.

**Enablement timing:** Enabling Person Accounts after significant data and code already exists in an org is harder than enabling at org inception. The later the enablement, the more Contact queries, Apex classes, and integrations must be retrofitted. If B2C is part of the long-term roadmap, enabling Person Accounts early (even before first B2C records) is architecturally preferable.

---

## Anti-Patterns

1. **Enabling Person Accounts in production without a prior sandbox test cycle** — Person Account enablement permanently alters Contact query behavior, unlocks new page layout requirements, and may break existing Apex and installed packages. Organizations that skip sandbox validation and enable directly in production frequently encounter broken Apex tests, integration failures, and AppExchange package errors that cannot be rolled back.

2. **Treating PersonContact as a regular Contact** — Writing Apex or SOQL that queries Contact and processes PersonContact records as if they were regular B2B contacts. This produces incorrect automation results (e.g., sending B2B email templates to B2C consumers), data corruption (e.g., deleting PersonContact records through a Contact cleanup job, which orphans the Person Account), and integration sync errors. All Contact queries in Person Account-enabled orgs must be reviewed for PersonContact awareness.

3. **Using a single Duplicate Rule for both Person Accounts and Business Accounts** — Applying the same duplicate matching logic to records with fundamentally different identity fields (company name vs personal name + email + birthdate) produces both false positives (business accounts flagged as duplicates of person accounts) and false negatives (true person duplicates not detected because business-account matching fields are blank on person accounts). Separate rules for each account model are required.

---

## Official Sources Used

- Salesforce Object Reference — Person Account sObject, IsPersonAccount field, PersonContact behavior
  URL: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_account.htm
- Salesforce Help: Enable Person Accounts — prerequisites, enablement steps, record type requirements
  URL: https://help.salesforce.com/s/articleView?id=sf.account_person.htm&type=5
- Salesforce Well-Architected Overview — architecture quality framing, scalability and reliability pillars
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Architects: Data Model Design — B2C data model patterns, Person Account architectural guidance
  URL: https://architect.salesforce.com/decision-guides/data-model
