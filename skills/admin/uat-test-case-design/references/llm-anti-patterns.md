# LLM Anti-Patterns — UAT Test Case Design

Common mistakes AI coding assistants make when generating UAT test cases for Salesforce features.
These patterns help the consuming agent self-check its own output before producing a script set.

---

## Anti-Pattern 1: Generating Happy Path Only

**What the LLM generates:** A case set of 4–6 cases, all with `negative_path: false`,
each walking the AC's success path.

**Why it happens:** Happy paths are over-represented in training data, and the
Given/When/Then `Scenario:` blocks for failures are often shorter and easier to
miss when summarizing.

**Correct pattern:**

```yaml
# At least one of the following per story:
case_id: UAT-OPP-002
negative_path: true
expected_result: "Save fails with validation error 'Only Pipeline-Edition reps can advance the stage'"
```

**Detection hint:** If no case in the set has `negative_path: true`, fail the
generation. The check_uat_case.py script enforces this per-story.

---

## Anti-Pattern 2: Hallucinating UI Element Names

**What the LLM generates:** Steps like "click the 'Approve and Convert' button"
or "select 'Quick Submit' from the More menu" — for elements that do not exist
in the org's actual page layout.

**Why it happens:** LLMs interpolate plausible-sounding Salesforce UI labels
from training data. Real org UI is configured per page layout + record type +
profile and may not match the generic pattern.

**Correct pattern:**

```yaml
steps:
  - "Open the 'Acme Q2 Renewal' Opportunity (record id supplied in data_setup)"
  - "Click the Stage path component in the highlights region"
  - "Select 'Closed Won' in the path"
  - "Click 'Mark Stage as Complete'"
# Cite developer names where the case author has confirmed them:
  - "Invoke quick action with developer name `Mark_Complete`"
```

**Detection hint:** Steps that name buttons, quick actions, or list views
without being grounded in the source story or page layout reference are
hallucinations. Flag any UI label not present in the inputs.

---

## Anti-Pattern 3: Omitting Permission Setup

**What the LLM generates:** Cases with empty `permission_setup` arrays or
`permission_setup: ["the right permissions"]`. Sometimes "System Administrator"
as the persona to "save time."

**Why it happens:** LLMs mirror the casual language in test plans where
permissions are assumed to exist. Sys Admin is the most-cited profile in
documentation, so it is the default fallback.

**Correct pattern:**

```yaml
persona: "Sales Rep — Pipeline Edition"
permission_setup:
  - "Assign Sales_Pipeline_PSG to the tester user"
  - "DO NOT assign System Administrator profile"
```

**Detection hint:** Empty `permission_setup`, or persona equal to one of
{"System Administrator", "Admin", "Internal User", "Standard User"} without a
named PSG. The check script flags both.

---

## Anti-Pattern 4: Missing Data Setup

**What the LLM generates:** Cases with `data_setup: []` or steps that reference
records the case never seeded ("open the existing Account").

**Why it happens:** LLMs assume the sandbox has data. Case-style training data
often elides the seed step because authors took it for granted.

**Correct pattern:**

```yaml
data_setup:
  - "Seed Account 'Acme Co' with Industry = Manufacturing"
  - "Seed Opportunity 'Acme Q2 Renewal' on that Account, StageName = 'Negotiation', CloseDate = today + 7"
# For >5 records:
  - "Run anonymous Apex `TestDataFactory.createOpportunityHierarchy(50)` from templates/apex/tests/TestDataFactory.cls"
```

**Detection hint:** `data_setup` empty AND steps reference records by name. If
the steps say "open the X record" and `data_setup` does not seed X, the case
will fail for setup reasons.

---

## Anti-Pattern 5: Conflating UAT With Regression

**What the LLM generates:** A "UAT case set" that includes a wide net of
unrelated regression scenarios — re-testing every Opportunity workflow because
"the change touches Opportunity."

**Why it happens:** UAT and regression both use cases and run in UAT sandboxes.
LLMs collapse them when the user prompt is ambiguous.

**Correct pattern:**

```yaml
# UAT cases are scoped per story_id + ac_id from the change under test.
# Regression cases live elsewhere (admin/uat-and-acceptance-criteria handles
# regression strategy). A UAT case set MUST cite the source story and AC.
case_id: UAT-OPP-001
story_id: STORY-734           # required
ac_id: AC-734-1               # required
```

**Detection hint:** Cases without `story_id` + `ac_id`, or cases that test
behavior unrelated to the inputs supplied. Route regression questions to
`admin/uat-and-acceptance-criteria`.

---

## Anti-Pattern 6: Treating UAT Cases as Apex Test Boilerplate

**What the LLM generates:** A `@isTest` Apex class with insertions and asserts,
labeled as a UAT test case.

**Why it happens:** "Test" pattern-matches strongly to Apex test class generation
in training data. The LLM picks the most-trained shape.

**Correct pattern:**

```yaml
# A UAT case is a YAML/JSON document with click-level steps a HUMAN runs in
# the Salesforce UI. NOT an Apex test method.
case_id: UAT-OPP-001
steps:
  - "Open the Sales app and navigate to the 'Acme Q2 Renewal' Opportunity"
  - "Click the Stage path and select 'Closed Won'"
  - "Mark Stage as Complete and confirm"
```

**Detection hint:** If the generated artifact contains `@isTest`, `Test.startTest()`,
`System.assert(...)`, or `Database.insert(...)`, it is an Apex test, not a UAT
case. Route to `agents/test-generator/AGENT.md` instead.

---

## Anti-Pattern 7: Generating Per-Click Cases Instead of Per-AC Cases

**What the LLM generates:** 30+ cases for a single 6-step wizard, one per
click. Each case has 1 step.

**Why it happens:** LLMs over-decompose when given a list of UI actions. The
correct unit (an AC scenario) is invisible without the source AC block.

**Correct pattern:**

```yaml
# One case per AC scenario per persona. Click sequence lives inside `steps`.
case_id: UAT-OPP-001
ac_id: AC-734-1                # one scenario
steps:                         # six clicks
  - "step 1"
  - "step 2"
  - "step 3"
  - "step 4"
  - "step 5"
  - "step 6"
```

**Detection hint:** Case count >> AC scenario count, OR cases with only one
step in `steps`. Either signal demands re-decomposition by `ac_id`.
