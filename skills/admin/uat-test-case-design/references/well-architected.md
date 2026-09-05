# Well-Architected Notes — UAT Test Case Design

## Relevant Pillars

UAT test case design touches three pillars. The case schema is the operational
artifact that converts AC into evidence the platform behaves the way the team
contracted.

- **Reliability** — A UAT case proves a specific Salesforce behavior under a
  specific persona + data state. Without persona-grounded cases (especially
  negative-path cases), reliability claims are unverifiable. The discipline
  of "≥1 negative case per story" is what distinguishes UAT from a demo.
- **Operational Excellence** — UAT cases are the input to RTM closure, defect
  triage, and release sign-off. Cases that lack `story_id`, `ac_id`, or
  evidence URLs break the operational workflow downstream. The canonical schema
  enforced by this skill is what makes the run auditable.
- **User Experience** — Cases are authored from a persona's seat. A case that
  runs as System Administrator proves the platform works for the wrong user.
  Persona-grounded cases catch FLS, page-layout, and quick-action gaps that
  affect the actual humans who will use the feature.

## Architectural Tradeoffs

- **Manual UI cases vs Apex test methods.** Manual UAT cases prove the UI
  composition (page layout, quick action, related list) works for a persona;
  Apex tests prove the data-tier and automation logic. They are complements,
  not substitutes. UAT cases that try to assert business-logic invariants the
  Apex layer already covers add cost without proving anything new. Keep
  per-AC manual cases for UI behavior, sharing visibility, and the click-level
  user journey; defer logic invariants to Apex tests.
- **Per-persona case multiplication vs run cost.** Splitting cases per persona
  catches FLS and CRUD gaps but multiplies run time. Tradeoff: split per
  persona only when the AC's `then` clause differs by persona OR the persona
  is the subject of the test (deny case). Do not split when expected outcome
  is identical across personas — one case is enough.
- **Manual data seed vs `TestDataFactory`.** Manual seed is fast for ≤5
  records and one-off shapes; the factory is correct for relationship-heavy
  seeds and bulk runs. Cases that hand-seed 30 records via the UI are slow
  and error-prone. Cases that invoke the factory need the seeding user to be
  able to run anonymous Apex — **UNVERIFIED (2026-09-05):** the permission's
  exact name is documented only in Salesforce Help, which cannot be fetched
  here, so confirm it in the org rather than naming it in a case. Seed under a
  separate setup identity where possible, so the *tester's* grant stays the
  minimal one the case is meant to prove.

## Anti-Patterns

1. **System Administrator persona** — Tests prove nothing about the actual
   users. FLS, sharing, custom-permission gates all bypass. Replace with
   the named profile + PSG even when "Sys Admin is faster."
2. **Empty `data_setup`** — Cases that assume records exist generate
   setup-reason failures the team logs as feature defects. Always enumerate
   the records and imports the steps depend on.
3. **Happy-path-only case sets** — Case sets without negative-path cases
   produce green runs that ship P1 security and validation defects. Every
   story needs ≥1 case with `negative_path: true`.
4. **Inline evidence ("Pass — looks good")** — `pass_fail` without an
   `evidence_url` is unverifiable after the sandbox refreshes. Require
   screenshot or recording link before setting Pass or Fail.

## Official Sources Used

Each bullet is a source actually used in this package, with the claim it carries. Line numbers refer
to the plain-text extraction of each PDF; the PDF itself is the citable artefact.

- **Metadata API Developer Guide** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  — `PermissionSetGroup.status` enumeration `Updated` / `Outdated` / `Updating` / `Failed`
  (L95345–95352, gotcha 9); "You can use permission sets to grant access but not to deny access"
  (L94703–94705, gotcha 10); `modifyAllRecords` / `viewAllRecords` granting access "regardless of the
  sharing settings for the object" (L95085–95092, L95109–95116, gotcha 10 and § Permission Setup
  Discipline); `Profile.layoutAssignments` with an optional `recordType`, and the absence of any
  layout assignment on `PermissionSet` (L97720, L98060–98066, L94766–94870, § Salesforce-Specific
  Gotchas 1); `RestrictionRule` `Restrict` versus `Scoping` (L106018–106020, gotcha 12);
  `formFactor` `Large` / `Small` / null (L39827–39835, gotcha 3); `EscalationAction` fields
  (L59483–59517, gotcha 15); `EntitlementProcessMilestoneTimeTrigger.timeLength` sign
  (L59213–59218, worked example TC-CI-008); `ValidationRule.errorMessage` and `errorDisplayField`
  (L45402–45403, L45388–45391, TC-CI-012); `CaseSettings.defaultCaseOwner` / `defaultCaseUser`
  (L111700–111710, TC-CI-001 and TC-CI-003); `FlowTest` scope (L73961–73962, § 8 automation verdict).
- **Apex Developer Guide** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
  — Triggers and Order of Execution: the UI-only step-2 checks versus the API path (L15419–15421,
  L15436–15437), custom validation rules at step 5 for every source (L15442–15443), and "No other
  validation occurs on the client side" (L15404–15406) — all of gotcha 11 and § Salesforce-Specific
  Gotchas 2. `System.runAs` enforcing "that user's sharing rules and object-level and field-level
  permissions" (L41325–41328) — the `apex` automation verdict.
- **Object Reference for the Salesforce Platform** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
  — `UserRecordAccess` fields and its restriction-rule blind spot (L303129–303131, L303174–303210,
  L303228–303231, gotcha 12); `PermissionSetGroup.Status` as a queryable picklist (L217708–217712,
  gotcha 9); `Case.OwnerId` "Refers To Group, User" and `Group.Type` value `Queue`
  (L62575–62587, L154307–154312, L154341–154342, TC-CI-001); `CaseHistory` available "for tracked
  fields of the object" (L62818–62819, gotcha 15); `CronTrigger.NextFireTime` / `PreviousFireTime`
  (L86765–86771, L86780–86786, gotcha 13); `BusinessHours` — "Escalation rules are run only during
  these hours" (L53105, § 8 automation verdict).
- **Data Loader Guide** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_data_loader.pdf
  — import batch size 200 for SOAP API / 10000 for Bulk API, and neither used under Bulk API 2.0
  (L351–359); the **Assignment rule** setting overriding CSV owner values (L379–383); the `success`
  and `error` output CSVs and what each column carries (L1135–1137, L1153–1155). All three pin
  worked examples TC-CI-004 and TC-CI-013.
- **REST API Developer Guide** — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_rest.pdf
  — the `DUPLICATES_DETECTED` status code and its platform message "Use one of these records?"
  (L6932, L22757), which is why `references/examples.md` asserts the code and treats the alert text
  as org-specific.
- **`standards/build-orchestration.md`** § 5 Acceptance tests — the five runner types
  (`checker`, `xml`, `manifest`, `command`, `manual`) and the rule that a manual test is "a checklist
  line the human ticks at the milestone gate". This is what a UAT case set is, from the build layer's
  side, and it is why `scripts/check_uat_case.py` takes `--manifest-dir`.
- **`admin/acceptance-criteria-given-when-then`** § 1 (`REQ-nnn` / `AC-nnn.n` id conventions) and § 4
  (the six criteria the worked example turns into scripts) — this package consumes those ids and
  never restates the Given/When/Then form.
- **`admin/uat-and-acceptance-criteria`** §§ 2.1–2.3 (environment rationale, deliverability, the
  persona roster and its "no row says System Administrator" rule) and § 4 (the defect taxonomy the
  triage table extends) — inherited, not re-derived.
- **`admin/sandbox-strategy`** § Type Capacities and Refresh Windows (the Full sandbox's 29-day
  refresh floor) and **`devops/sandbox-data-isolation-gotchas`** § Gotcha 3 (CronTriggers copied in
  `WAITING` and firing on their own schedule) — jointly the grounding for gotcha 13.
- **Salesforce Well-Architected** — https://architect.salesforce.com/well-architected/trusted/resilient/testing
  — the Resilient framing behind § Relevant Pillars and the manual-versus-automated tradeoff above.
