# LLM Anti-Patterns — Acceptance Criteria Given/When/Then

Common mistakes AI coding assistants make when generating Given/When/Then AC
for Salesforce features. These patterns help the consuming agent self-check
its own output before handing off to UAT or `agents/test-generator`.

---

## Anti-Pattern 1: Imperative-Voice AC ("The system should send an email")

**What the LLM generates:**

```
Acceptance Criteria:
- The system should send an email when the Opportunity is closed.
- The user should be able to update the Stage.
- The validation rule should fire if Probability is below 100.
```

**Why it happens:** LLMs default to imperative product-spec voice from
generic SaaS training data. Generic agile checklists use "should" without
the Given/When structure, and the model copies that shape.

**Correct pattern:**

```gherkin
Scenario: Email is sent on Opportunity close
  Given an Opportunity owned by a user in "Sales_Rep_PSG"
    And StageName is "Negotiation"
   When the user updates StageName to "Closed Won"
   Then eventually within 60 seconds an email is sent to the Account's PrimaryContact
    And the email body contains the Opportunity Name and Amount
```

**Detection hint:** If a line starts with "The system should" or "The user
should" without an enclosing `Scenario:` / `Given` / `When` / `Then`
structure, it is imperative-voice AC, not Given/When/Then.

---

## Anti-Pattern 2: Inventing Data States Not Present in the Target Org

**What the LLM generates:**

```
Given an Opportunity with a "Premium Tier" record type
  And a custom field "Strategic_Account__c" set to true
 When the user updates Stage
 Then ...
```

…even though the org has no "Premium Tier" record type and no
`Strategic_Account__c` field.

**Why it happens:** LLMs hallucinate Salesforce-shaped object/field names
when the prompt is underspecified. The names sound plausible because they
match common org patterns the model has seen.

**Correct pattern:** Only reference record types, fields, profiles, PSGs,
sharing rules, and named credentials that the prompt explicitly provides
or that the author confirms exist in the target org. When in doubt, mark
the unknown as a question to the user, not a fabricated Given.

```
Given an Opportunity with a record type that maps to the "Direct Sales" sales process
  # NOTE: confirm exact record type API name in target org before publishing
```

**Detection hint:** Every API name in a Given clause must be traceable to
either the input prompt or a confirmed metadata source. Unconfirmed names
should appear as `# NOTE: confirm` comments, not assertions.

---

## Anti-Pattern 3: Omitting the Permission Precondition

**What the LLM generates:**

```
Scenario: Edit Opportunity Stage
  Given an Opportunity in stage "Negotiation"
   When the user updates Stage to "Closed Won"
   Then the save succeeds
```

…with no mention of which user, which profile, which PSG, or whether the
user is the owner.

**Why it happens:** LLMs treat "the user" as a singular generic actor
because most non-Salesforce BDD examples do. Salesforce's permission and
sharing model has no equivalent in generic web-app BDD literature.

**Correct pattern:**

```
Scenario: Owner Sales Rep can edit Stage
  Given an Opportunity owned by Alice
    And Alice is in the "Sales_Rep_PSG" permission set group
    And the Opportunity OWD is "Private"
   When Alice updates Stage to "Closed Won"
   Then the save succeeds
```

Always name the actor by identity and PSG, especially when the target
object has private OWD or FLS-controlled fields.

**Detection hint:** Search the AC block for the words "user", "actor",
"someone". Each occurrence must be a *named* user (Alice, Bob, Loader)
introduced in a Background block with a PSG or profile.

---

## Anti-Pattern 4: Happy-Path-Only AC

**What the LLM generates:** Three Scenarios, all of which describe
successful outcomes. No deny-case. No validation-error Scenario. No
permission-denied Scenario.

**Why it happens:** LLMs optimize for the requested behavior in the prompt
("make this work") and skip writing the inverse ("ensure this does not
work for the wrong user / wrong data"). The user story rarely spells out
the deny-case explicitly, so the model omits it.

**Correct pattern:** For every happy-path Scenario, generate a paired
deny-case Scenario. The pairing rule:

- "User in PSG-A can do X" → "User without PSG-A cannot do X, response is Y"
- "Save succeeds when field is V" → "Save fails when field is V', error is E"
- "Async job fires" → "Async job's failure path produces error log entry"

**Detection hint:** Count Scenarios. If `count(Then succeeds | Then is
visible | Then is created)` is greater than `count(Then fails | Then is
denied | Then is hidden)`, the block is happy-path-biased. The lint script
enforces parity for permission-tagged stories.

---

## Anti-Pattern 5: Conflating AC With Implementation Steps

**What the LLM generates:**

```
Scenario: Stage update
  Given a Process Builder named "Opportunity_Stage_Update_PB" exists
    And it fires on update of Opportunity
   When ...
```

Or:

```
Scenario: Trigger fires
  Given an Apex trigger OpportunityTrigger on after-update
   When ...
```

**Why it happens:** LLMs that have seen code in the prompt context default
to writing the AC in the same vocabulary as the implementation. The line
between "what" and "how" gets blurred.

**Correct pattern:** Drop all tool / class / metadata-name references from
the Given. Describe only observable state and observable actions. The
implementation choice is made later — and the same AC should still be
valid if Process Builder is replaced by Flow or Apex.

```
Scenario: Stage update on owned Opportunity
  Given an Opportunity owned by Alice with StageName "Negotiation"
   When Alice updates StageName to "Closed Won"
   Then StageName is "Closed Won"
    And the related Account's LastModifiedDate is updated
```

**Detection hint:** Search the AC for the words "Process Builder",
"Trigger", "Flow", "Apex class", "Validation Rule named". These are
implementation tells. They belong in the design doc, not the AC.

---

## Anti-Pattern 6: Missing the Bulk Path

**What the LLM generates:** All Scenarios use 1 record. No Scenario
mentions 200, 1000, 10000, or any Data Loader / Bulk API context.

**Why it happens:** Generic BDD examples are 1-record. The Salesforce
governor-limit-driven need for a 200-record Scenario is platform-specific
and absent from the LLM's BDD training data.

**Correct pattern:** For every story where the implementation will be a
trigger, record-triggered flow, validation rule, batch, or integration,
add at least one Scenario with explicit volume:

```
Scenario: Bulk Stage update across 200 Opportunities
  Given 200 Opportunities owned by users in "Sales_Rep_PSG"
   When a Data Loader update sets StageName to "Qualification" on all 200
   Then all 200 saves succeed
    And no governor-limit error is raised
```

**Detection hint:** If the AC mentions "trigger", "flow", "validation
rule", "Bulk API", or "Data Loader" anywhere, but no Scenario contains
a number >= 200, the bulk path is missing.

---

## Anti-Pattern 7: Synchronous Then on Async Behavior

**What the LLM generates:**

```
Scenario: External billing system updated on Opportunity close
   When Alice updates Stage to "Closed Won"
   Then the external billing system has received the update
```

…with no eventual / polling clause, even though the implementation is a
Queueable callout that runs post-commit.

**Why it happens:** LLMs default to immediate Then because that is how
generic BDD examples are written. The async-callout idiom requires
platform-specific knowledge of what happens after the transaction commits.

**Correct pattern:**

```
Scenario: External billing system updated on Opportunity close
   When Alice updates Stage to "Closed Won"
   Then eventually within 60 seconds a POST to named credential "Billing_API"
        is sent with the Opportunity Id and Amount
    And the Opportunity has Billing_System_Id__c populated
```

**Detection hint:** Any Then clause that mentions an external system, a
callout, a Platform Event, a CDC subscriber, or a batch must use
"eventually within N <seconds|minutes>" — not bare "Then".

---

## Anti-Pattern 8: Vague Validation-Error Assertions

**What the LLM generates:**

```
Then the save fails with a validation error
```

**Why it happens:** The model knows a validation error happens but does
not have the exact message text from the validation rule definition.
Rather than asking, it elides.

**Correct pattern:** Validation-rule expectations must include the exact
message text the rule will display. This is what the UAT tester verifies
character-for-character and what the Apex test asserts via
`DmlException.getMessage().contains(...)`.

```
Then the save fails
  And the validation error message is exactly "Stage cannot be Closed Won until Probability is 100"
```

If the message text is not yet decided, mark it `# TBD` rather than
hand-waving — that flags the open decision to the build team.

**Detection hint:** Every Then clause that includes "fails" or "error"
must be followed by an `And` line containing the exact error string in
quotes (or a `# TBD` marker).
