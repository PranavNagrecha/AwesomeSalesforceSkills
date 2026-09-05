# Acceptance Criteria Template — Given/When/Then for a Salesforce User Story

Copy this template into the body of a user story. Fill the bracketed
placeholders. Run `python3 scripts/check_ac_format.py <story.md>` from the
skill folder to lint the result before handing off.

---

## User Story

> **As a** [persona with profile / PSG context]
> **I want** [feature involving named object and field]
> **So that** [business outcome]

**Target object(s):** `[Object__c]`
**Sharing-relevant?** [Yes / No — if Yes, fill the OWD line in Background]
**Trigger / flow / validation involved?** [Yes / No — if Yes, include a bulk Scenario]
**Async / callout involved?** [Yes / No — if Yes, use `Then eventually within N seconds`]

---

## Acceptance Criteria

### Background — Permission and Sharing Preconditions

```gherkin
Background:
  Given a user "[Name1]" in the "[PSG_Name_1]" permission set group with role "[Role1]"
    And a user "[Name2]" in the "[PSG_Name_2]" permission set group with role "[Role2]"
    And the [Object__c] OWD is "[Private | Public Read Only | Public Read/Write | Controlled by Parent]"
    And [optional: hierarchy / queue / team membership details]
```

> **Rule:** every named user must have a PSG. Every story tagged to a
> sharing-relevant object must declare OWD here.

---

### Happy-Path Scenario(s)

```gherkin
Scenario: [Short imperative phrase: actor + behavior]
  Given [data-state precondition — record ownership, lifecycle stage, related-record state]
    And [additional precondition if needed]
   When [exactly one action — record created/updated/deleted, button invoked, batch run]
   Then [exactly one observable outcome — field value, record state, "TBD" error message, callout, Task]
    And [optional: related assertions on the same outcome]
```

> **Rule:** one Given (with optional `And` chain), one When, one Then
> (with optional `And` chain). If you need two Whens, split into two
> Scenarios.

---

### Negative-Path Scenario(s) — Pair Each Happy Path

```gherkin
Scenario: [Actor without permission / wrong data state] cannot [action]
  Given [the deny precondition: missing PSG, wrong owner, wrong stage, wrong probability]
   When [same action as the paired happy-path Scenario]
   Then the [save | access | callout] fails
    And the [validation message | response | error] is exactly "[message text or # TBD]"
    And [optional: the original record state is unchanged]
```

> **Rule:** every Scenario whose Then includes "succeeds / is visible / is
> created" must have a paired Scenario whose Then includes
> "fails / is denied / is hidden / is not created".

---

### Scenario Outline — Parameterized Cases

Use when the same Given/When/Then shape applies to 3+ data points
(picklist values, record types, user roles).

```gherkin
Scenario Outline: [Behavior name] across [varying dimension]
  Given [precondition referencing <param1>]
   When [action referencing <param2>]
   Then [outcome referencing <param3>]

  Examples:
    | param1 | param2 | param3 |
    | ...    | ...    | ...    |
    | ...    | ...    | ...    |
```

---

### Bulk Scenario — Required for Trigger / Flow / Validation Behavior

```gherkin
Scenario: Bulk [behavior] across [N] records
  Given [N] [Object] records [matching the precondition]
   When [the bulk action — Data Loader update, Bulk API job, batch trigger]
   Then [bulk-aware outcome: success count, error count, no governor-limit error]
    And no "Apex CPU time limit", "Too many SOQL queries", or "Too many DML statements" is raised
```

> **Rule:** N >= 200 (one trigger batch) for any single-org behavior; >= 10000
> for integration / Bulk API behavior.

---

### Async / Callout Scenario — Use `Then eventually`

```gherkin
Scenario: [External system] is updated on [event]
  Given [precondition]
   When [the triggering action]
   Then eventually within [N] seconds a [POST | GET | event publish] to named credential "[NamedCredential]"
        is sent with [field A], [field B]
    And [optional: the source record has its [Result__c | LastSyncDate__c] populated]
```

---

---

## Criteria Record — The Lintable Shape

Once the Scenarios above are settled, transcribe them into this record. It is what
`scripts/check_ac_format.py` lints, what `admin/uat-and-acceptance-criteria` joins to by `ac_id`,
and what `agents/test-class-generator` filters by `test_type`. A filled example is in
`references/worked-examples.md` § 5.

```yaml
project: "[Project — Release]"
acceptance_criteria:
  - ac_id: AC-[nnn].[n]              # scoped to its requirement: AC-001.2 is REQ-001's second
    req_id: REQ-[nnn]                # RTM id, immutable; translate an FG- id, never store it
    story_id: US-[nnn]
    persona: "[named user — profile and permission set / PSG, not a job title]"
    sandbox: "[sandbox name and type]"
    artefact: "[the metadata file or repo path under test]"
    seed_data: "[the records that must exist before the When]"
    test_type: apex | flow | manual  # decided by the oracle, not by the build
    negative: false                  # true for deny-case and no-match criteria
    given: "[precondition — ownership, lifecycle state, calendar, rule state]"
    when: "[exactly one action]"
    then: "[one observable outcome — field value, queryable row, or exact error string]"
    proof: "[the query, checker command, or observation that makes the Then falsifiable]"
```

> **Rule:** every rule-type requirement (assignment, auto-response, escalation, duplicate,
> matching, validation, entitlement) needs at least one row with `negative: true` naming what
> happens when nothing matches. The checker fails the file otherwise.

Lint it:

```bash
python3 scripts/check_ac_format.py --file acceptance-criteria.yaml
python3 scripts/check_ac_format.py --manifest-dir ./docs/stories/
```

## Handoff Notes for `agents/test-class-generator`

- Use the Background block as the test-class `setup` data shape.
- Each Examples row becomes one parameterized test method.
- Each bulk Scenario becomes one `@isTest` method using
  `templates/apex/tests/BulkTestPattern.cls`.
- Each `Then eventually` Scenario implies enqueue + `Test.startTest /
  stopTest` boundary in the test class.
