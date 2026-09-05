# Well-Architected Notes — Standard Object Quirks

## Relevant Pillars

- **Reliability** — Standard object quirks are a primary source of silent data loss and broken automation. Lead conversion filling only empty fields on existing targets, merge letting the master's nulls supersede good values, and CaseComment isolation all cause production incidents when platform behaviour diverges from developer expectations. Building systems that account for these quirks eliminates entire categories of runtime surprise.

- **Security** — Person accounts and CaseComment both have direct access consequences. Person account fields are the subset carried on the child person contact record, and they are null and unmodifiable when `IsPersonAccount` is false (object_reference.txt L13677–L13683), so code that reads them without checking the flag is reading nothing rather than reading too much. The sharper security decision is CaseComment: making a comment editable after insertion requires **Modify All Records** on Cases or **Modify All Data** (object_reference.txt L63045–L63049), and both grant far more than comment editing. An append-only comment design is a security choice, not a UX compromise.

  UNVERIFIED (2026-09-05): the earlier claim in this file that sharing rules on the Account side of a person account do not propagate to the Contact side is not stated in the Object Reference or Apex Developer Guide — none of the person-account passages in either guide discusses sharing propagation. It has been removed rather than restated; see `admin/sharing-and-visibility` and verify against org behaviour before designing around it.

- **Operational Excellence** — The behaviours in this skill fail *quietly*: a trigger that never fires, a status filter that undercounts, a field that always reads null. None produce an error to triage. The operational answer is the probe set in `references/metadata-examples.md` § 7 and the checker in `scripts/`, which turn "we believe this org is fine" into evidence. Documenting the org-specific answers — which statuses are flagged closed, whether conversion triggers are enabled — matters more than documenting the platform rules, because the org answers change and the platform rules do not.

- **Performance** — Polymorphic queries using `TYPEOF` avoid running separate queries per target type and merging in Apex. CaseComment triggers that touch parent Cases add DML that must be bulkified. Merge is the opposite shape: it fires one delete event for all losing records and one update for the winner (apexdev.txt L15354–L15366), so per-record work inside those handlers is cheap while per-record *expectations* are wrong.

- **Scalability** — Lead conversion and merge both amplify under volume. The three-record merge cap (salesforce_app_limits_cheatsheet.txt L977–L982) turns a large dedupe into a successive-merge program with its own throughput characteristics, not a single call. Person-account orgs that grow past their initial design routinely find Contact-focused automation was never exercised, because person-account DML never entered it.

## Architectural Tradeoffs

1. **Explicit handling vs. simplicity**: Accounting for every standard object quirk adds code complexity (TYPEOF clauses, person/business branches, CaseComment triggers, successive merges). The tradeoff is worth it because the alternative is silent data loss or automation that never runs.

2. **Trigger-based field preservation vs. declarative mapping**: Lead field mapping is simpler to maintain but requires manual updates for every new field. Capture-before-convert plus write-after is self-maintaining but adds Apex and test coverage. The tie-breaker is grounded rather than aesthetic: conversion-time before triggers only fire when the org setting is enabled (apexdev.txt L15548–L15551), so a trigger-based design that assumes otherwise is not simpler — it is broken.

3. **Append-only comments vs. an edit path**: Editing a saved CaseComment requires a permission that also grants read and edit on every case in the org. Append-only costs a slightly worse UX and buys a much smaller permission surface.

4. **Reading closed status from metadata vs. hard-coding it**: querying the `TaskStatus` value set (or filtering on `CompletedDateTime != null`) survives an admin adding `Closed - No Action`; a string literal does not. The cost is one indirection; the benefit is that the report stops silently undercounting.

5. **Compensating job vs. trigger for record-type conversion**: No update account trigger fires when a record type changes between business and person account (apexdev.txt L15545–L15546). A scheduled comparison is more machinery than a trigger, and it is the only option that runs at all.

## Anti-Patterns

1. **Treating standard objects like custom objects** — Assuming standard object relationships follow the same cascade-delete, trigger-firing, and field-access rules as custom objects. Verify against the Object Reference and the Apex Developer Guide's "Operations That Don't Invoke Triggers" list before building automation.

2. **Ignoring polymorphic lookup resolution** — Writing SOQL that uses dot-notation on `WhoId` / `WhatId` without `TYPEOF`, then dropping the offending fields instead of fixing the pattern. This produces automation that lacks the data it was built for.

3. **Building person-account logic on the Contact side** — The single most expensive anti-pattern in this domain, because it produces code that reviews well, tests green, and never executes. Person-account DML fires Account triggers, not Contact triggers (apexdev.txt L15521).

4. **Encoding folklore as a comment** — `// EndDateTime is required by the API` and `// PersonAccounts fire both triggers` are how an incorrect belief survives a rewrite. Both are contradicted by the guides cited below. A comment asserting platform behaviour should carry the source, or it should not be written.

5. **Choosing the winner of a merge by recency** — The main record's values, including nulls and empty strings, always supersede (apexdev.txt L8203–L8207). The most recently touched duplicate is frequently the least complete one, and merging into it discards data the platform will not restore after fifteen days.

## Official Sources Used

- **Apex Developer Guide** (Summer '26 / v62 PDF), "Operations That Don't Invoke Triggers" — person-account DML fires Account triggers not Contact triggers (L15521), business↔person record-type conversion fires no update account trigger (L15545–L15546), lead-conversion before triggers are opt-in (L15548–L15551). Sources Gotchas 1, 4 and 6, the Core Concepts person-account table, and the § 1 handler. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Apex Developer Guide**, "Merge Considerations" and "Triggers and Merge Statements" — mergeable objects and the main-plus-two cap (L8201–L8202), main record's values including nulls supersede (L8203–L8207), single delete plus single update event and `MasterRecordId` only in after delete (L15354–L15366). Sources Gotcha 10 and metadata-examples § 3.
- **Apex Developer Guide**, "Convert Leads Considerations" and DML special cases — standard vs custom lead field mapping (L8353–L8355), only empty target fields overwritten (L8356–L8360), person-account `Name` not modifiable by DML (L9029), field tokens unavailable for person accounts (L10866–L10867), cascading delete and the deletable-child rule (L8236–L8240), Recycle Bin retention (L8212, L8260). Sources Gotchas 5, 7 and 12.
- **Object Reference** (Summer '26 / v62 PDF) — Event `DurationInMinutes` / `EndDateTime` either-or rule (L111593–L111597, L111637–L111641) and the API-version split in error reporting (L111642–L111646); Task `CompletedDateTime` Closed-status semantics (L277989–L278013) and `ActivityDate` as due date (L277934); `WhoId` / `WhatId` polymorphism (L278390–L278393, L278448). Sources Gotchas 2 and 3 and the Core Concepts date-contract section. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Object Reference**, Account / Contact / Case / CaseComment entries — `IsPersonAccount` read-only (L13116–L13122), `IsPersonAccount Fields` subset note (L13677–L13683), `PersonEmail` labelled "Email" (L13770), the merge Supported-Calls discrepancy between Case (L62206–L62207) and Account / Contact / Lead (L12740–L12741, L71309–L71310, L163052–L163053), CaseComment post-insert write lock (L63045–L63049) and `IsNotificationSelected` always null on query (L62994–L63004). Sources Gotchas 8, 9 and 11.
- **Metadata API Developer Guide** (Summer '26 / v62 PDF) — `StandardValue.closed` semantics and version note (L47542–L47545), `StandardValueSet` requiring at least one value and rejecting the `*` wildcard (L130769–L130775, L130826–L130828), `TaskStatus` as the standard value set name for `Task.Status` (L143095), and the standard-object retrieve/deploy exclusion of system and autonumber fields (L2163–L2167). Sources metadata-examples § 5 and the "How to read this file" retrieval warning. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Salesforce App Limits Cheat Sheet** (Summer '26 / v62) — `merge()` limits: 200 merge requests per SOAP call, three records per request including the master, successive merge beyond that, and no external Id fields (L977–L982). Sources Gotcha 10 and the successive-merge loop in metadata-examples § 3.
- **Salesforce Well-Architected** — the Reliability and Operational Excellence framing above. https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
