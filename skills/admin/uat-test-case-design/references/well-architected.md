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
  and error-prone. Cases that invoke the factory require anonymous Apex
  permission for the seeding user.

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

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help — Permission Set Groups — https://help.salesforce.com/s/articleView?id=sf.perm_set_groups.htm
- Salesforce Help — Sandbox Types — https://help.salesforce.com/s/articleView?id=sf.data_sandbox_environments.htm
- Salesforce Help — Data Loader Guide — https://developer.salesforce.com/docs/atlas.en-us.dataLoader.meta/dataLoader/data_loader.htm
- Salesforce Architects — Testing & Release Management — https://architect.salesforce.com/well-architected/trusted/resilient/testing
