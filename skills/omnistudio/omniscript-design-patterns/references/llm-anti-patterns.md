# LLM Anti-Patterns: OmniScript Design Patterns

Common mistakes AI coding assistants make when generating or advising on OmniStudio OmniScript design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Creating Too Many Steps in a Single OmniScript

**What the LLM generates:** An OmniScript with 20+ steps for a guided process, making the user experience overwhelming and the OmniScript difficult to maintain and debug.

**Why it happens:** LLMs map each business requirement to a step without considering UX grouping, step consolidation, or sub-OmniScript delegation.

**Correct pattern:**

```text
OmniScript step count guidelines:

Recommended: 3-7 steps per OmniScript
Maximum practical: 10-12 steps before UX and maintenance suffer

Strategies for reducing step count:
1. Group related fields into a single step (use Step elements with sections)
2. Use conditional visibility to show/hide fields within a step
3. Delegate complex sub-journeys to child OmniScripts
4. Move data-entry-heavy sections to embedded LWC components
5. Use Type Ahead and lookup elements to reduce manual entry

Sub-OmniScript pattern:
- Parent OmniScript: 5 steps for the main journey
- Step 3: embedded child OmniScript for address capture (3 steps)
- Step 5: embedded child OmniScript for document upload (2 steps)
```

**Detection hint:** Flag OmniScripts with more than 12 steps. Check whether steps can be consolidated or delegated to child OmniScripts.

---

## Anti-Pattern 2: Not Implementing Save and Resume for Long Processes

**What the LLM generates:** A multi-step OmniScript for a complex application process (insurance, lending, enrollment) without save-and-resume capability, meaning users lose all progress if they navigate away or the session times out.

**Why it happens:** Save and resume is an additional configuration that requires understanding OmniScript's state management. LLMs build the happy-path flow without addressing the user experience of interrupted sessions.

**Correct pattern:**

```text
Save and Resume implementation:

Configure in the OmniScript Setup panel:
- Save Options (Trailhead lists them among the script-wide Setup
  panel settings)
- UNVERIFIED (2026-10-03): the exact property names and whether the
  built-in save uses OmniScriptSavedSession records (an internal-use
  object in the Industries guide) or a custom Data Mapper are documented
  only in Salesforce Help; check before designing storage

Design considerations:
1. Save should capture ALL user inputs up to the current step
2. Resume should restore the user to the last completed step
3. Handle partial data: saved state may have incomplete fields
4. Validate resumed data: field values may have become invalid
   (e.g., expired date, deactivated picklist value)
5. Multiple save points: allow saving at any step, not just specific ones

Storage options:
- Custom object (Application_Draft__c) for structured persistence
- ContentVersion for document-heavy applications
- Platform Cache for short-lived sessions (risky, cache can evict)
```

**Detection hint:** Flag multi-step OmniScripts (5+ steps) for processes that take >5 minutes without save-and-resume configuration. Check for missing save action in OmniScript properties.

---

## Anti-Pattern 3: Embedding All Data Logic in the OmniScript Instead of Integration Procedures

**What the LLM generates:** OmniScript steps with inline DataRaptor calls, direct SOQL, and embedded formulas for data retrieval and processing, instead of delegating data operations to Integration Procedures.

**Why it happens:** OmniScript supports direct DataRaptor calls and data operations. LLMs configure everything inline for simplicity, but this makes the OmniScript harder to test, reuse, and maintain.

**Correct pattern:**

```text
Separation of concerns in OmniStudio:

OmniScript responsibility:
- UI layout and step navigation
- User input collection and validation
- Conditional step visibility and branching
- Launching actions (OmniScript actions, navigation)

Integration Procedure responsibility:
- Data retrieval (DataRaptor Extracts)
- Data transformation (DataRaptor Transforms)
- External API calls (HTTP Actions)
- Data persistence (DataRaptor Loads)
- Orchestration logic

Pattern:
- OmniScript Step 1: prefill via IP call (single action)
- OmniScript Step 2: user enters data
- OmniScript Step 3: validation via IP call
- OmniScript Submit: save via IP call

Benefits: IP is testable without the UI, reusable across OmniScripts,
and debuggable via IP preview.
```

**Detection hint:** Flag OmniScripts with more than 3 direct DataRaptor calls. Check whether the data operations should be consolidated into Integration Procedures.

---

## Anti-Pattern 4: Not Using Conditional Step Navigation (Branching)

**What the LLM generates:** A linear OmniScript where every user goes through every step, including steps that are irrelevant to their scenario (e.g., showing business address fields when the user selected "individual" account type).

**Why it happens:** Linear OmniScripts are simpler to build. LLMs do not apply branching logic unless explicitly prompted, even when the business process clearly has different paths.

**Correct pattern:**

```text
OmniScript branching patterns:

1. Step-level conditional visibility:
   - Show/hide entire steps based on prior input
   - Example: show "Business Details" step only if Type = 'Business'

2. Element-level conditional visibility:
   - Show/hide individual fields within a step
   - Example: show "Tax ID" field only if Country = 'US'

3. Navigate action with conditions:
   - Jump to different steps based on a decision point
   - Example: after "Product Selection," route to "Simple Quote" or
     "Complex Configuration" based on product type

4. Branching best practices:
   - Keep the main path (most common scenario) as the default flow
   - Use decision elements for complex routing
   - Test all branch combinations (combinatorial testing)
   - Document the branching logic for maintainers
```

**Detection hint:** Flag linear OmniScripts (no conditional visibility or branching) with 5+ steps where the business process has multiple user types or scenarios.

---

## Anti-Pattern 5: Hardcoding OmniScript Type and SubType References

**What the LLM generates:** References to OmniScripts using hardcoded Type/SubType strings in actions, FlexCards, or Apex without using a configurable reference pattern.

**Why it happens:** Type/SubType is the primary identifier for OmniScripts. LLMs use literal strings because that is how OmniScripts are referenced in configuration.

**Correct pattern:**

```text
OmniScript reference management:

Problem: hardcoded Type/SubType in multiple locations
  FlexCard action: Type = "LoanApplication", SubType = "NewLoan"
  Apex or LWC launch code that passes the same two strings
  Navigation URLs or Lightning page properties that embed them
(Do not invent an Apex launch API. OmniProcess is an internal-use object
in the Industries guide, not a callable class.)

If you rename the OmniScript, all references break.

Mitigation:
1. Use Custom Metadata to store Type/SubType mappings:
   OmniScript_Config__mdt.getInstance('NewLoan').Type__c

2. Use consistent naming conventions:
   Type = business domain (e.g., "Lending")
   SubType = specific process (e.g., "NewApplication")

3. Document all locations that reference each OmniScript
4. When renaming: create the new OmniScript first, update all
   references, then deactivate the old one
```

**Detection hint:** Flag hardcoded OmniScript Type/SubType strings in Apex, FlexCard actions, or LWC navigation code. Check for centralized reference management.

---

## Anti-Pattern 6: Giving Two Active OmniScripts the Same Type, SubType, and Language

**What the LLM generates:** "Clone the Edit Account OmniScript, keep Type `team` and SubType `editAccount`, and activate both so each team has its own copy."

**Why it happens:** LLMs treat the OmniScript Name as the identifier.

**Correct pattern:**

```text
Identity = Type + SubType + Language (Trailhead).
"Only one active Omniscript may have the same Type, SubType, and Language
at any time." The Name doesn't need to be unique.
Give the copy a different SubType (for example editAccountPartner), or
make it a new version of the same script instead of a second script.
```

**Detection hint:** Two OmniScripts with matching Type, SubType, and Language both marked active.

---

## Anti-Pattern 7: Editing the Active Version in Place

**What the LLM generates:** "Open the active OmniScript, change the step, and save; users get the change immediately."

**Why it happens:** Flow-like mental model of saving a definition.

**Correct pattern:**

```text
Only one version can be active at a time. To change an active
OmniScript, create a new version, test it in Preview, then activate it.
The active version keeps serving users while you work (Trailhead,
"Create a Simple Omniscript"). Record which version is active in each
environment after every deployment.
```

**Detection hint:** Instructions that modify an active OmniScript without "New Version" and "Activate" steps.
