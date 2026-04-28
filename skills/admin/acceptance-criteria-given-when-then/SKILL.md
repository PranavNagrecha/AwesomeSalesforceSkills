---
name: acceptance-criteria-given-when-then
description: "Use this skill when writing test-first, behavior-driven acceptance criteria in Given/When/Then format for a Salesforce user story. Covers happy path, edge cases, negative paths, permission boundaries, and data-state preconditions so the AC block can drive UAT scripts and Apex test design downstream. Trigger keywords: given when then, gherkin, behavior driven AC, test first acceptance criteria, scenario outline, BDD acceptance criteria. NOT for the user-story format itself (use admin/user-story-writing-for-salesforce). NOT for UAT script writing (use admin/uat-test-case-design). NOT for Apex test method generation (use agents/test-generator). NOT for high-level UAT planning (use admin/uat-and-acceptance-criteria)."
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
  - "Handoff notes pointing test-generator agent at the bulk and edge scenarios"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
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

1. **`agents/test-generator/AGENT.md`** uses each Scenario as a test method seed and each Examples row as parameterized data.
2. **`agents/data-loader-pre-flight/AGENT.md`** uses the Given clauses to compute the record shape required to seed UAT and integration tests.
3. **`agents/uat-test-case-designer`** translates each Scenario into a step-by-step UAT script with screenshots and tester instructions.

If the AC is missing a Given (precondition), test-generator will hallucinate the seed; if it is missing the bulk path, the Apex test will pass at one record and break in production.

---

## Common Patterns

### Pattern: One AC = One Behavior, One Outcome

**When to use:** Always. Compound AC like "the user can save the record AND a Task is created AND an email is sent" is three separate scenarios, not one. Splitting them lets the team see exactly which one regresses.

**How it works:** Use a single When and a single primary Then per scenario. Use `And` to chain *related* assertions on the same outcome (multiple field values on the same created record). Use a new Scenario when the outcome is a different system observable (a different record created, a different email sent).

**Why not the alternative:** Compound AC hide which assertion failed in UAT and force test-generator to write tests with multiple oracles in one method, which violates Apex test single-responsibility.

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Read the draft user story and identify every behavior verb ("can", "should", "must", "is created", "is updated", "is notified"). Each verb is a candidate Scenario.
2. Draft a `Background` block with all user identities (named, with PSG and role) and OWD context the scenarios will reference.
3. For each behavior verb, write a happy-path `Scenario` with one Given (precondition), one When (action), one Then (outcome). Use `And` to chain related assertions on the same outcome.
4. For each happy-path Scenario, write a paired negative-path Scenario covering the deny-case (permission denied, validation error, sharing denied, async failure path).
5. For any parameterized behavior, collapse the duplicate Scenarios into a single Scenario Outline with an Examples table.
6. Add at least one bulk Scenario per trigger-or-flow-bound behavior, asserting 200-record success and governor-limit safety.
7. Run `python3 scripts/check_ac_format.py <story.md>` to lint the AC block. Resolve all errors before handing off to test-generator.

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

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems when the AC misses them:

1. **Bulk path missing means a passing CI test that breaks under Data Loader** — Apex governor limits do not bite at 1 record. They bite at 200. AC that says only "the trigger updates the record" without a bulk Scenario produces an Apex test that uses one record, passes, and fails on the first real load. Always pair single-record Scenarios with bulk Scenarios.
2. **Async outcome stated synchronously** — When the behavior is implemented as a Queueable, Platform Event subscriber, or batch job, a synchronous Then ("the field is updated") will be false in the moment the calling transaction commits. Use `Then eventually within N seconds` and let the test generator know it must enqueue / poll.
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

---

## Related Skills

- `admin/user-story-writing-for-salesforce` — produces the As a / I want / So that wrapper that this skill's AC block lives inside
- `admin/uat-test-case-design` — translates each Scenario in this skill's output into a step-by-step UAT script
- `admin/uat-and-acceptance-criteria` — higher-level UAT planning skill that this technique slots into
- `admin/requirements-gathering-for-sf` — produces the upstream user stories whose ACs this skill formats
- `agents/test-generator/AGENT.md` — consumes the AC block and Examples tables to design Apex test classes
- `agents/data-loader-pre-flight/AGENT.md` — uses Given clauses to compute the seed-data shape for UAT loads
