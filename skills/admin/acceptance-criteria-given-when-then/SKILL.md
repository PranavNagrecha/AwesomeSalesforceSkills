---
name: acceptance-criteria-given-when-then
description: "Use this skill when writing test-first, behavior-driven acceptance criteria in Given/When/Then format for a Salesforce user story. Covers happy path, edge cases, negative paths, permission boundaries, and data-state preconditions so the AC block can drive UAT scripts and Apex test design downstream. Trigger keywords: given when then, gherkin, behavior driven AC, test first acceptance criteria, scenario outline, BDD acceptance criteria. NOT for the user-story format itself (use admin/user-story-writing-for-salesforce). NOT for UAT script writing (use admin/uat-test-case-design). NOT for Apex test method generation (use agents/test-class-generator). NOT for high-level UAT planning (use admin/uat-and-acceptance-criteria). More triggers: acceptance criteria record, ac_id, req_id on a criterion, artefact under test, negative case for a rule-type requirement, no-match fall-through criterion, oracle for a Then clause, test type apex flow manual, criteria linter, check_ac_format.py, --manifest-dir."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - User Experience
  - Operational Excellence
triggers:
  - "given when then for salesforce stories"
  - "behavior driven AC for salesforce"
  - "test first acceptance criteria for a user story"
  - "how to write gherkin scenarios for a salesforce feature"
  - "scenario outline with examples table for parameterized salesforce AC"
  - "how to capture permission and data-state preconditions in AC"
  - "negative path acceptance criteria for salesforce flows and validation rules"
  - "we're having issues with acceptance criteria"
  - "write acceptance criteria for a case assignment rule"
  - "acceptance criteria for a validation rule that blocks a save"
  - "acceptance criteria for a permission set that grants edit"
  - "how do I prove an SLA escalation criterion in a sandbox"
  - "which acceptance criteria can be automated as apex tests and which stay manual"
  - "our acceptance criteria passed UAT but the rule did nothing when no entry matched"
  - "acceptance criteria keep describing the flow instead of the behaviour"
  - "lint a given when then acceptance criteria file"
tags:
  - acceptance-criteria
  - given-when-then
  - bdd
  - gherkin
  - test-first
  - user-stories
inputs:
  - "Draft user story (As a / I want / So that) with persona, object, and intended behavior"
  - "Target object and field-level requirements (FLS, required, picklist values)"
  - "Sharing context: OWD, role hierarchy position, permission set group assignments"
  - "Data-state preconditions: record ownership, related-record existence, lifecycle stage"
  - "Known constraints: governor limits, bulk volume, integration touchpoints"
outputs:
  - "Given/When/Then acceptance criteria block ready to paste into the user story"
  - "Scenario outline (Examples table) for parameterized cases"
  - "Negative-path AC list paired one-to-one with each happy-path AC"
  - "Permission and data-state precondition block with explicit user/PSG references"
  - "Handoff notes pointing test-class-generator agent at the bulk and edge scenarios"
  - "Lintable acceptance-criteria record (YAML or markdown table) carrying req_id, persona, sandbox, seed data, artefact, proof and test type per criterion"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Acceptance Criteria — Given/When/Then for Salesforce

This skill activates when an author needs to convert a user story's intent into a precise, testable Given/When/Then (Gherkin-style) acceptance criteria block. The output drives three downstream artifacts: UAT scripts, the Apex test design plan, and the data-loader pre-flight shape. The discipline of this skill is forcing every "should" to have a paired "should not" and every behavior to declare its data-state and permission preconditions explicitly.

---

## Before Starting

Gather this context before drafting AC:

- **Which persona, profile, and permission set group?** A criterion that says "the user can edit Stage" is meaningless without naming the user's profile or PSG. AC for Salesforce always names the actor in permission terms, not job titles.
- **What is the data-state precondition?** Most Salesforce behavior is conditional on record ownership, lifecycle stage, related-record existence, or sharing scope. AC must capture that state in the Given clause — not assume it.
- **Is this a bulk or single-record scenario?** Salesforce executes triggers, flows, and validation rules in batches of up to 200 records. A criterion that only describes one-record behavior leaves the bulk path untested and is the most common cause of governor-limit defects in production.
- **Is there an integration or async boundary?** If the behavior depends on a callout, Platform Event, or Queueable, the Then clause must say *what is observable when* — synchronously, after a poll, or after a job completes.

---

## Questions to Ask Before Configuring

Ask these before a single Scenario is written. Each traces to a gotcha in `references/gotchas.md`; skipping one produces criteria that read well and prove nothing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which requirement id does this belong to, and does that requirement already have criteria somewhere else?" | Ids are the join key the RTM, the workbook and the UAT script all read; two authors writing the same `When` is a backlog problem that only surfaces at sign-off (gotcha 6) | A `req_id` on every criterion, and a merge-or-scope decision taken before duplicate criteria ship |
| "Who runs it — named user, profile, permission set — and do they hold *record* access as well as *object* access?" | `allowEdit` on a permission set is an object-level capability; only `modifyAllRecords` / `viewAllRecords` bypass sharing, so "the PSG grants edit" is half a requirement (gotcha 5) | A persona per criterion, plus the paired deny-case naming the user who must fail and how |
| "What happens when the rule matches nothing?" | Every rule engine defines an order and a fall-through; the AC is the only place the fall-through owner gets named, and the first unmatched record in production is where it is discovered otherwise (gotcha 10) | A criterion marked `negative` whose Given is "matches no entry" and whose Then names the fall-through |
| "Which clock measures every elapsed time here — wall clock, or a business-hours calendar with holidays?" | Escalation and milestone targets run on the calendar attached to the record, and holidays suspend it; a Then written in clock hours will be reported as a defect against working metadata (gotcha 12) | The calendar named in the Given, a holiday criterion per calendar, and the sign on any warning trigger |
| "How will we observe the Then — a field value, a query, an error string, or a mailbox?" | A Then with no named observable is untestable, and a query against an untracked field cannot fail (gotchas 4 and 13) | A `proof` on every criterion, and the automatable-vs-manual verdict that falls out of it |
| "Which sandbox proves this, and what must be seeded there first?" | Personas, seed records and field-history tracking are preconditions of the oracle, not of the behaviour, so they belong in the Background rather than in a tester's head (gotcha 13) | `sandbox` and `seed_data` on every criterion, and the tracking the oracle depends on declared once |
| "Will this behaviour ever meet 200 records at once, and through which tool?" | Governor limits bite at the batch, not the record, and Data Loader, Bulk API 2.0 and REST disagree about whether rules run at all when nothing is specified (gotchas 7 and 11) | A bulk criterion with the entry path pinned, and an honest manual verdict for the paths Apex cannot exercise |

What a proper criteria set adds over just writing "the user can do X": every criterion names the actor, the record state, the artefact under test and the thing that proves it, so a pass is evidence and a failure points at one component instead of a feature.

---

## Core Concepts

### The Given/When/Then Anatomy

Given/When/Then (also called Gherkin, after the Cucumber syntax) splits each acceptance criterion into three clauses:

- **Given** — the precondition. State of the org, user identity, record ownership, related-record existence, sharing scope, picklist value of a field, status of a parent record. Givens are facts true *before* the action.
- **When** — the action. Exactly one event: a record is created, a field is updated to a value, a button is invoked, a Platform Event is published, a batch job runs. One AC = one When.
- **Then** — the observable, deterministic outcome. A field has a specific value, a record exists with specific fields, a validation error fires with a specific message, a callout is sent with a specific payload, a Task is created on a specific record.

A criterion is testable only if all three are present. Drop the Given and the test cannot be set up reproducibly. Drop the When and the test has no trigger. Drop the Then and the test has no oracle. The Salesforce Trailhead BA curriculum aligns with this format and recommends "if/then" phrasing as a simpler equivalent — Given/When/Then is the more rigorous extension that explicitly carves out the precondition from the trigger.

### Scenario Outlines and Examples Tables

When the same Given/When/Then shape applies to multiple data points (different stages, different record types, different user profiles), do not write n nearly-identical scenarios. Instead, parameterize with a Scenario Outline and an Examples table:

```
Scenario Outline: Stage transitions allowed by Sales Process

  Given an Opportunity owned by a user in the "Sales_Rep_PSG" permission set group
    And the Opportunity StageName is "<from_stage>"
   When the user updates StageName to "<to_stage>"
   Then the save <result>
    And StageName is "<final_stage>"

  Examples:
    | from_stage      | to_stage          | result                                | final_stage     |
    | Prospecting     | Qualification     | succeeds                              | Qualification   |
    | Qualification   | Closed Won        | fails with "Skip-stage not allowed"   | Qualification   |
    | Negotiation     | Closed Lost       | succeeds                              | Closed Lost     |
    | Closed Won      | Prospecting       | fails with "Cannot reopen Closed Won" | Closed Won      |
```

This is the cleanest way to drive a parameterized Apex test or UAT matrix. The test generator skill consumes the Examples rows directly as test-method seeds.

### Negative-Path Discipline (Every "Should" Pairs With a "Should Not")

The single highest-value rule in this skill: every happy-path AC must have a paired negative-path AC. If the story says "a Sales Rep should be able to set Stage to Closed Won when Probability is 100", the AC block must also include "a Sales Rep should NOT be able to set Stage to Closed Won when Probability is below 100, and the validation message is X." The vast majority of UAT regressions come from missing negative paths, not missing happy paths.

The same discipline applies to permission boundaries: for every "user with PSG-A can do X" there must be a "user without PSG-A cannot do X, and the system response is Y" (CRUD denial, FLS hidden, sharing access denied, validation error).

### Permission and Sharing Preconditions

Salesforce behavior is conditional on the running user's permissions and sharing context. AC that says "the user can see the Credit Limit field" is wrong; AC that says "Given a user in the Finance_Reader PSG, when they open the Account record page, then the Credit Limit field is visible read-only" is correct. Always name:

- The profile or permission set group
- The role / role hierarchy position when sharing matters
- Whether the user is the record owner, a member of an Opportunity Team, in a queue, or accessing via a sharing rule
- Any field-level security override

### Data-State Preconditions

Most Salesforce defects trace back to an unstated data assumption. AC must explicitly state:

- Record ownership ("Given an Opportunity owned by user A")
- Lifecycle stage / status of parent and child records
- Picklist values that gate behavior
- Whether related records exist and how many
- Whether the org is sandbox, scratch, or production-like (for sandbox-sensitive features such as email deliverability)

### Avoid UI-Coupled Language

Do not write AC against the chrome of the UI: button labels, page tab names, toast positions, color, the exact path through the App Launcher. UI changes between releases; behavior does not. Replace "click the Save button" with "the record is saved", "navigate to the Opportunities tab" with "view a list of Opportunities the user has access to". The AC is a behavior contract, not a click script — that comes later in the UAT script (a separate skill).

### Handoff to Test Design

Well-formed Given/When/Then AC is consumed by three downstream agents:

1. **`agents/test-class-generator/AGENT.md`** uses each Scenario as a test method seed and each Examples row as parameterized data.
2. **`agents/data-loader-pre-flight/AGENT.md`** uses the Given clauses to compute the record shape required to seed UAT and integration tests.
3. **`admin/uat-test-case-design`** translates each Scenario into a step-by-step UAT script with screenshots and tester instructions.

If the AC is missing a Given (precondition), test-class-generator will hallucinate the seed; if it is missing the bulk path, the Apex test will pass at one record and break in production.

### Requirement Ids on Every Criterion

A criterion with no requirement id is untraceable the moment it leaves the story. Use the RTM
convention — `REQ-nnn`, assigned during elicitation, immutable, never reused
(`admin/requirements-traceability-matrix` § ID Conventions) — and carry it on every row.
Criterion ids are scoped to the requirement: `AC-001.2` is the second criterion of `REQ-001`, and it
is the `ac_id` the UAT script joins on (`admin/uat-and-acceptance-criteria` § The UAT Script).

**`FG-XXX` ids in the configuration workbook map 1:1 to `REQ-XXX` ids.**
`admin/configuration-workbook-authoring` § Per-Row Schema documents `source_req_id` as "the RTM
`req_id`", while the worked rows in that skill's `references/examples.md` carry `FG-014`, `FG-031`,
`FG-051` — fit-gap row ids. The two spaces are one-to-one and the pairing is recorded upstream, on
each requirements-catalogue row as `downstream.fit_gap_row`
(`admin/requirements-gathering-for-sf` § The Requirements Catalogue). Write `req_id` in acceptance
criteria; translate to `FG-` only when writing into a workbook that already uses it, and never
renumber either space to make them line up.


---

## Common Patterns

### Pattern: One AC = One Behavior, One Outcome

**When to use:** Always. Compound AC like "the user can save the record AND a Task is created AND an email is sent" is three separate scenarios, not one. Splitting them lets the team see exactly which one regresses.

**How it works:** Use a single When and a single primary Then per scenario. Use `And` to chain *related* assertions on the same outcome (multiple field values on the same created record). Use a new Scenario when the outcome is a different system observable (a different record created, a different email sent).

**Why not the alternative:** Compound AC hide which assertion failed in UAT and force test-class-generator to write tests with multiple oracles in one method, which violates Apex test single-responsibility.

### Pattern: Permission-Precondition Block at the Top of Each Scenario Set

**When to use:** Whenever the story involves more than one user role or an explicit permission boundary.

**How it works:** Open the AC block with a "Background" section that lists the user identities and PSGs that subsequent scenarios reference. Each Scenario then says "Given a user in `<role>`" without re-introducing the role.

```
Background:
  Given a user "Alice" in the "Sales_Rep_PSG" permission set group with role "EMEA Sales"
    And a user "Bob"   in the "Sales_Manager_PSG" permission set group with role "EMEA Sales Manager"
    And the Opportunity OWD is "Private"

Scenario: Owner can edit Stage
  Given an Opportunity owned by Alice
   When Alice updates StageName to "Qualification"
   Then the save succeeds
```

This forces the author to declare the sharing model up front (OWD private, role hierarchy in play) and prevents repetition.

### Pattern: Bulk Path Scenario Per Behavior

**When to use:** Any AC that describes Apex trigger, record-triggered flow, validation rule, or integration behavior.

**How it works:** For every single-record happy-path scenario, add a corresponding bulk scenario with explicit volumes:

```
Scenario: Bulk Stage update across 200 Opportunities
  Given 200 Opportunities owned by users in "Sales_Rep_PSG" with StageName "Prospecting"
   When a Data Loader update sets StageName to "Qualification" on all 200
   Then all 200 saves succeed without governor-limit errors
    And LastModifiedDate is set on each record
```

200 is the trigger batch size. The bulk scenario is what protects the design from a single-record-only Apex test that passes in CI and fails on a Data Loader run.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Story straddles two object lifecycles (e.g. Opportunity → Order conversion) | Split into two AC blocks, one per object, with cross-references | Each block is independently testable and matches a single Apex test class scope |
| Behavior depends on async (Queueable, Platform Event) | Use "Then eventually" with a polling clause and a max-wait time | Synchronous Then on async behavior produces flaky tests |
| Behavior is FLS- or sharing-conditional | Add a permission-precondition Background block | Prevents per-Scenario repetition and surfaces the sharing model explicitly |
| Same shape applies to many picklist values or record types | Scenario Outline with Examples table | Drives parameterized Apex tests and matrix UAT |
| AC has more than one When | Split into multiple Scenarios | One AC = one behavior; compound When hides which step failed |
| Story is a "look and feel" change (color, spacing) | Reject for AC; redirect to UX review | Given/When/Then is for behavior, not aesthetics |
| Behavior involves a callout to an external system | Use "the system sends a request to <named credential>" not "the system calls API" | Names the named credential the integration tests can stub |
| Volume exceeds 10,000 records per transaction | Add a bulk-failure Scenario that asserts partial-success behavior | Forces design of `Database.SaveResult` handling, not "all-or-nothing" assumption |

---

## Recommended Workflow

1. **Pull the requirement and its id.** Take the `REQ-nnn` from the RTM or the requirements
   catalogue and carry it unchanged onto every criterion you write. If the workbook row you are
   testing shows an `FG-` id in `source_req_id`, translate it rather than renumbering — see
   § Requirement Ids on Every Criterion and `references/worked-examples.md` § 1.
2. **Answer the seven questions above, then write the Background once.** Sandbox, named users with
   their permission sets, seed records, and any field-history tracking an oracle will depend on.
   `references/worked-examples.md` § 3 is the filled-in shape; the persona roster comes from
   `admin/uat-and-acceptance-criteria`, not from this skill.
3. **Write the happy path, then its deny-case, for each behaviour verb.** One Given, one When, one
   Then, `And` only for related assertions on the same outcome. For a rule-type requirement
   (assignment, auto-response, escalation, duplicate, validation) the deny-case that names the
   **no-match fall-through** is mandatory — `references/gotchas.md` gotcha 10.
4. **Give every Then an oracle, then decide automatable.** Name a field value, a queryable row, or
   an exact error string. The oracle decides the verdict, not the technology: if the only way to
   observe it is to wait for a clock or read a mailbox, the criterion is manual.
   `references/worked-examples.md` § 6 records the verdict and the platform fact behind it.
5. **Compress and cover volume.** Collapse near-duplicate Scenarios into a Scenario Outline with an
   Examples table; add a bulk Scenario per trigger / flow / validation behaviour with the **entry
   path pinned** (the Data Loader Assignment rule setting, the Bulk API `assignmentRuleId`, or the
   REST default) — `references/gotchas.md` gotcha 11.
6. **Emit the record and lint it.** Use the YAML shape in `references/worked-examples.md` § 5, or
   the markdown table in § 7 for story tools that cannot hold YAML, then run
   `python3 scripts/check_ac_format.py --file acceptance-criteria.yaml` (or `--manifest-dir
   ./docs/stories/` for a folder). The same script still lints a Gherkin story markdown. Fix every
   ERROR before handing off.
7. **Hand off.** `admin/uat-and-acceptance-criteria` turns the `ac_id`s into a UAT programme;
   `agents/test-class-generator/AGENT.md` takes the criteria marked `test_type: apex`;
   `agents/data-loader-pre-flight/AGENT.md` reads the Given clauses for the seed shape.

---

## Review Checklist

Run through these before marking the AC block complete:

- [ ] Every Scenario has exactly one Given, one When, one Then (with optional `And` chains)
- [ ] Every happy-path Scenario has a paired negative-path Scenario
- [ ] Every Scenario names the running user by PSG / profile, not by job title
- [ ] Every Scenario states the record ownership / lifecycle precondition explicitly
- [ ] No Scenario uses UI-chrome language (button labels, click verbs, tab names, toast position)
- [ ] Each behavior has at least one bulk Scenario with explicit volume (200, 10k, etc.)
- [ ] Any async behavior uses "eventually" with a max-wait time, not synchronous Then
- [ ] Any Examples-table parameterization compresses what would otherwise be near-duplicate Scenarios
- [ ] Validation-rule expectations name the exact error message text
- [ ] Integration expectations name the named credential, not "the API"
- [ ] Every criterion carries a `req_id`, a persona, a sandbox, the artefact under test, and a `proof`
- [ ] Every rule-type requirement (assignment, auto-response, escalation, duplicate, validation) has a criterion for the no-match fall-through
- [ ] Every elapsed-time Then names the number, the unit, and the calendar that measures it
- [ ] `python3 scripts/check_ac_format.py --file <record>` reports 0 errors

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems when the AC misses them:

1. **Bulk path missing means a passing CI test that breaks under Data Loader** — Apex governor limits do not bite at 1 record. They bite at 200. AC that says only "the trigger updates the record" without a bulk Scenario produces an Apex test that uses one record, passes, and fails on the first real load. Always pair single-record Scenarios with bulk Scenarios.
2. **Async outcome stated synchronously** — When the behavior is implemented as a Queueable, Platform Event subscriber, or batch job, a synchronous Then ("the field is updated") will be false in the moment the calling transaction commits. Use `Then eventually within N seconds` and let test-class-generator know it must enqueue / poll.
3. **Shared/owned ambiguity** — AC that says "a Sales user can edit the Opportunity" without naming whether the user is the *owner*, in the *Account team*, or accessing via *role hierarchy* leaves the sharing model unstated. The build team will pick a default that may not match the business intent — and UAT will not catch it because the testing user is also unclear.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| AC block | Given/When/Then scenarios pasted into the user story body, with Background and Examples tables |
| Scenario Outline | Parameterized table for any AC that varies by picklist value, record type, or user role |
| Negative-path list | One-to-one paired deny-case scenarios for every happy-path scenario |
| Permission precondition block | Named users, PSGs, roles, and OWD context referenced by all Scenarios in the story |
| Bulk path scenarios | Per-behavior 200-record (or higher) Scenarios that protect the trigger / flow design from governor-limit regressions |
| Criteria record | The same criteria as a lintable YAML file or markdown table — `ac_id`, `req_id`, persona, sandbox, seed data, artefact, `test_type`, `negative`, Given/When/Then, `proof` — the shape `scripts/check_ac_format.py` reads and `admin/uat-and-acceptance-criteria` consumes |
| Automatability verdict | Per criterion: Apex test, Flow test, or manual, with the platform fact that decided it |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You need six requirements from one real build worked into criteria — Background, Given/When/Then per requirement, sandbox / persona / seed data / artefact / proof per criterion, the automatable verdict with the platform fact behind it, and the same set as a lintable YAML record and as a markdown table |
| `references/gotchas.md` | Before writing a Then, and before calling a criterion automatable — 13 failure modes with what happens / when it occurs / how to avoid, the platform ones grounded in the guides |
| `references/examples.md` | You want three complete AC blocks (Probability gate, sharing visibility, bulk duplicate load) plus the compound-AC anti-pattern and how to turn a visibility Then into a query oracle |
| `references/well-architected.md` | You are justifying the criteria depth to a delivery lead, or you need the source behind a platform claim (`## Official Sources Used`) |
| `references/llm-anti-patterns.md` | You are reviewing AI-generated acceptance criteria before they reach a build team or a tester |
| `templates/ac-template.md` | Starting a new AC block — copy, fill the placeholders, then lint |
| `templates/acceptance-criteria-given-when-then-template.md` | Starting a working session on an existing story — records the context gathered and the patterns chosen |
| `scripts/check_ac_format.py` | Before every handoff — lints a criteria record (YAML or markdown table) or a Gherkin story file; `--file` for one, `--manifest-dir` for a folder |

---

## Related Skills

- `admin/user-story-writing-for-salesforce` — produces the As a / I want / So that wrapper that this skill's AC block lives inside
- `admin/uat-test-case-design` — translates each Scenario in this skill's output into a step-by-step UAT script
- `admin/uat-and-acceptance-criteria` — higher-level UAT planning skill that this technique slots into
- `admin/requirements-gathering-for-sf` — produces the upstream user stories whose ACs this skill formats
- `agents/test-class-generator/AGENT.md` — consumes the AC block and Examples tables to design Apex test classes
- `agents/data-loader-pre-flight/AGENT.md` — uses Given clauses to compute the seed-data shape for UAT loads
- `admin/requirements-traceability-matrix` — owns the `REQ-nnn` convention every criterion carries, and the forward/backward traceability the `ac_id` closes
- `admin/configuration-workbook-authoring` — consumes criteria through `source_req_id`; its worked rows are where the `FG-XXX` ids come from
- `admin/case-management-setup` — supplies the case-intake build that `references/worked-examples.md` writes criteria against
