# LLM Anti-Patterns — Path and Guidance

Common mistakes AI coding assistants make when generating or advising on Salesforce Path configuration.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Treating Path as a Required-Field Enforcement Mechanism

**What the LLM generates:** Advice such as "add the field as a key field in Path so reps are required to fill it in before advancing" — or a workflow design that assumes Path will block stage progression if the key field is empty.

**Why it happens:** LLMs conflate "surfacing a field" with "requiring a field." The training data contains many questions like "how do I make fields required at each stage" and the Path key fields concept appears alongside those discussions. The LLM pattern-matches and assumes Path enforces.

**Correct pattern:**

```
Path surfaces fields for visibility and inline editing.
Enforcement requires a Validation Rule:
  ISPICKVAL(StageName, "Proposal/Price Quote") && ISBLANK(Economic_Buyer__c)
  → Error: "Economic Buyer must be set before advancing to Proposal."

Path and the validation rule complement each other.
Path = guidance. Validation Rule = enforcement.
```

**Detection hint:** Look for phrases like "Path will require", "Path enforces", "the user cannot advance until", or "Path makes fields mandatory."

---

## Anti-Pattern 2: Claiming Confetti Fires on Automation-Driven Stage Changes

**What the LLM generates:** Advice that confetti will fire whenever the Stage reaches Closed Won, including when changed by a Flow, Process Builder, Apex trigger, or API call.

**Why it happens:** The LLM treats confetti as an event-driven trigger (like a Flow trigger condition) rather than a UI interaction reward. The distinction between UI-driven and automation-driven state changes is subtle and often omitted from training examples.

**Correct pattern:**

```
Confetti fires ONLY when the user manually advances the stage
through the Path component's "Mark Stage as Complete" button.

Stage changes made by:
  - Flow / Process Builder
  - Apex trigger
  - REST API / Bulk API
  - Quick Action edit
  - Standard picklist edit on the detail page

...do NOT trigger confetti. This is expected platform behavior.
```

**Detection hint:** Look for "confetti fires when", "confetti triggers automatically", "whenever the stage reaches", or any suggestion that confetti is automation-compatible.

---

## Anti-Pattern 3: Suggesting Long Text Area or Rich Text Fields as Key Fields

**What the LLM generates:** A key fields list that includes Description, a custom rich text area (e.g., `Proposal_Notes__c`), or a long text area field as an inline editable key field.

**Why it happens:** LLMs do not consistently know the field type restrictions for Path key fields. When asked for "important fields at this stage," they suggest semantically relevant fields without checking supportability.

**Correct pattern:**

```
Supported key field types for Path:
  Text (short), Number, Currency, Percent, Date, DateTime,
  Checkbox, Email, Phone, URL, Lookup (read-only display)

Unsupported:
  Long Text Area, Rich Text Area, Encrypted fields

If a long text area is important context for a stage,
put it in the Guidance Text block instead.
```

UNVERIFIED (2026-09-05): this supported-type list is not stated in the Metadata API guide (`fieldNames` is described only as "All the fields in entityName that will display in this step", api_meta.txt L94545) nor in the limits cheat sheet, which has no Path entry. What *is* checkable statically, and what `scripts/check_path_and_guidance.py` enforces, is that every custom field named in `fieldNames` exists on `entityName` in the manifest — a cross-object reference like `Contact.Phone` fails that check outright.

**Detection hint:** Review any generated key field list for field API names ending in `__c` that correspond to long text or rich text types, or any standard fields like `Description`.

---

## Anti-Pattern 4: Conflating Sales Process with Path Configuration

**What the LLM generates:** Instructions to "add the stage to the Path" when the real problem is that the stage is missing from the Sales Process. Or, conversely, instructions to edit the Sales Process when the admin only needs to adjust Path guidance for an existing stage.

**Why it happens:** Sales Process and Path both deal with Opportunity stages and are both configured in Setup. LLMs frequently blur the boundary between them, especially in responses about missing stages.

**Correct pattern:**

```
Sales Process (Setup > Sales Processes):
  Controls WHICH Stage picklist values are available
  for a given Opportunity Record Type.
  If a stage is missing from the Path, check here first.

Path Settings (Setup > Path Settings):
  Controls GUIDANCE and KEY FIELDS on stages
  that already exist for the record type.
  Adding a new stage to Path does not make it appear
  if it is not in the Sales Process.

Workflow: Add stage to Sales Process first → then configure in Path.
```

**Detection hint:** Look for responses that say "add the stage in Path Settings" when the actual symptom is a missing chevron, or responses that say "edit the Sales Process" when the admin only wants to change guidance text.

---

## Anti-Pattern 5: Advising Profile-Based Path Variation

**What the LLM generates:** A suggestion to create multiple paths for the same object and record type to show different guidance or key fields to users with different profiles (e.g., Sales Reps vs. Sales Managers).

**Why it happens:** LLMs know that many Salesforce features are profile-driven and pattern-match that framework onto Path. In reality, Path does not filter by profile — only by record type.

**Correct pattern:**

```
Path differentiation is by Record Type only.
Two paths can be active for the same object if they target different record types.

Profile-based variation is NOT supported natively in Path.

Workarounds (with tradeoffs):
  - Create separate record types for each user segment (if business data model supports it).
  - Use In-App Guidance (Walkthroughs) for profile-targeted contextual help — this IS profile-aware.
  - Accept that Path guidance is universal for the record type and write for the broadest audience.
```

**Detection hint:** Look for advice like "create one path for Sales Reps and another for Sales Managers on the same record type", or any suggestion that Path respects profile or permission set membership.

---

## Anti-Pattern 6: Skipping the org-level Enable Path Toggle in Setup Instructions

**What the LLM generates:** Step-by-step Path setup instructions that jump straight to "Create a new Path" without mentioning that the org-level Path Settings toggle must be enabled first.

**Why it happens:** LLMs often model "feature setup" as a single-layer operation (configure the thing, it appears). The two-layer requirement — org toggle on + individual path active — is a detail that gets omitted.

**Correct pattern:**

```
Step 1: Setup > Path Settings > Enable the "Path" toggle (org-level)
Step 2: Create and configure individual path records
Step 3: Set each path record to Active

All three must be true for a path to render:
  - Org toggle = ON
  - Individual path = Active
  - Path component present on the Lightning page
```

**Detection hint:** Review any Path setup instructions that do not mention the org-level toggle as a distinct step.

---

## Anti-Pattern 7: Assuming a Retrieved Path Is the Whole Configuration

**What the LLM generates:** A promotion plan that retrieves `PathAssistant`, deploys it, and declares the path migrated — often phrased as "the path metadata carries the steps, key fields, guidance, and celebration settings."

**Why it happens:** LLMs generalize from metadata types that *are* complete records of their feature. Path is not one of them, and the omission is invisible in a diff: nothing in the retrieved file hints that something is missing.

**Correct pattern:**

```
PathAssistant carries EXACTLY:
  active, entityName, fieldName, masterLabel,
  pathAssistantSteps[], recordTypeName
PathAssistantStep carries EXACTLY:
  fieldNames[], info, picklistValueName
                                    (api_meta.txt L94510-94529, L94545-94549)

NOT carried by the file, and therefore NOT deployed:
  - celebration / confetti configuration  (no element exists)
  - the org preference                    (PathAssistantSettings, separate type)
  - the record page that renders it       (FlexiPage, separate type)
  - the stage values themselves           (RecordType / BusinessProcess / StandardValueSet)
  - guidance translations                 ("cannot be retrieved or deployed from or
                                            to translation workbench", L94497)

A path promotion is a FIVE-type package plus one manual step.
```

**Detection hint:** Any migration or deploy plan whose manifest names `PathAssistant` and nothing else. Also flag "the confetti setting will come across with the path" and any CI assertion written against celebration state — there is no field to assert on.

---

## Anti-Pattern 8: Inventing Element and Component Names for Path Metadata

**What the LLM generates:** XML using plausible-sounding names that do not exist — `<steps>` or `<pathSteps>` instead of `<pathAssistantSteps>`, `<guidance>` instead of `<info>`, `<picklistValue>` instead of `<picklistValueName>`, a comma-separated `<fieldNames>Amount,CloseDate</fieldNames>` instead of repeated elements, `<celebrationEnabled>true</celebrationEnabled>`, `<recordType>` instead of `<recordTypeName>`, an org setting called `enablePathAssistant` in `Sales.settings`, or a Lightning page component named `flexipage:path` / `lightning:path`.

**Why it happens:** The real names are irregular — a step's guidance field is called `info`, the value field is `picklistValueName` while the object field is `entityName`, and the settings flag is `pathAssistantEnabled` inside a file named `PathAssistant.settings`. LLMs smooth irregularity into consistency, and the invented names are plausible enough to survive review.

**Correct pattern:**

```
File:      pathAssistants/<Name>.pathAssistant-meta.xml
Root:      <PathAssistant xmlns="http://soap.sforce.com/2006/04/metadata">
Elements:  active | entityName | fieldName | masterLabel
           pathAssistantSteps { fieldNames* | info | picklistValueName }
           recordTypeName

File:      settings/PathAssistant.settings-meta.xml
Root:      <PathAssistantSettings>
Elements:  pathAssistantEnabled | canOverrideAutoPathCollapseWithUserPref
Manifest:  <members>PathAssistant</members><name>Settings</name>

FlexiPage: <componentName>runtime_sales_pathassistant:pathAssistant</componentName>
           in <name>subheader</name>, template
           flexipage:recordHomeWithSubheaderTemplateDesktop

<fieldNames> REPEATS. It is never comma-separated.
```

**Detection hint:** Diff any generated Path XML element-by-element against the list above, or run `scripts/check_path_and_guidance.py` — an invented element name shows up as a missing Required field rather than as a parse error, because the XML is still well-formed.
