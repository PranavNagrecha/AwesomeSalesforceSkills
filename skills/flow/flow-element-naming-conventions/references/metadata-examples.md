# Metadata Examples — Flow Element Naming Conventions

One complete, deployable record-triggered before-save flow that conforms to
every naming rule this skill documents, end to end — Flow-level name, every
element name, every outcome name — plus a deliberately mis-named twin
(described in prose, not as a second file) and the checker's actual output
against both.

The object model is new to this skill package: **Contract renewal**, not
Case/Acme (used elsewhere in this library) and not the Opportunity model
`flow/record-triggered-flow-patterns` just shipped in its own
`references/metadata-examples.md` (`Opportunity_BeforeSave_Normalize`,
`Opportunity_AfterSave_ClosedWon`). This file does not re-derive that skill's
before-save save-order mechanics or its fault-path skeleton — it borrows the
same before-save shape (decisions + assignments only, no DML) and spends its
own space on names.

Field grounding: `apiVersion` (`api_meta.txt` — see the `Flow` type entry),
`triggerType` enum value `RecordBeforeSave` (`api_meta.txt` L72539–72542),
`recordTriggerType` enum and its "available only when `triggerType` is
`RecordBeforeSave` or `DataCloudDataChange`" caveat (`api_meta.txt`
L72450–72460), `filterFormula` (`api_meta.txt` L72390–72392, API 55.0+),
`triggerOrder` (`api_meta.txt` L68438–68441, API 54.0+, "1 to 2,000"),
`status` enum (`api_meta.txt` L68416–68424). `FlowAssignment` and
`FlowDecision` are both documented as extending `FlowNode` with no
`faultConnector` field of their own (`api_meta.txt` — `FlowAssignment` entry
lists only `assignmentItems` and `connector`; `FlowDecision` lists only
`attributes`, `defaultConnector`, `defaultConnectorLabel`, `rules`) — which is
why neither element below carries one; only DML and callout elements declare
`faultConnector`, and this flow has none by design.

---

## Assumed org model

| Component | Type | Used by |
|---|---|---|
| `Contract.Auto_Renew_Requested__c` | Checkbox | Start's implicit input; read by the Decision |
| `Contract.Renewal_Track__c` | Picklist (`Auto`, `Manual`) | Set by both Assignment branches |
| `Contract.Renewal_Owner_Required__c` | Checkbox | Set by both Assignment branches; read downstream by a renewal-ownership assignment flow (out of scope here) |

`Contract` is the standard object — `EndDate` (standard field) gates entry so
the flow only classifies contracts that have a renewal date to classify
against.

---

## 1. Before-save — `Contract_BeforeSave_ClassifyRenewalTrack.flow-meta.xml`

Flow-level name follows `<Object>_<TriggerContext>_<PurposeVerbPhrase>` —
the same shape `flow/record-triggered-flow-patterns` uses for its own
examples — with `Object` = `Contract`, not `Opportunity`. Every element name
inside follows this skill's own Decision Guidance table:
`Decision_IsAutoRenewRequested` (`Decision_` verb prefix, yes/no-framed
question — Concept 1, Pattern 3), `Assignment_SetAutoRenewTrack` /
`Assignment_SetManualRenewTrack` (`Assignment_<Verb><Object>` — Decision
Guidance row), the matched outcome `AutoRenewRequested` (affirmative
business condition — Pattern 3) and the default outcome
`ManualRenewal_Default` (explicit, not blank, not bare `No` — Pattern 3).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <assignments>
        <name>Assignment_SetAutoRenewTrack</name>
        <label>Set Auto Renew Track</label>
        <locationX>50</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Track__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Auto</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Owner_Required__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>false</booleanValue>
            </value>
        </assignmentItems>
    </assignments>
    <assignments>
        <name>Assignment_SetManualRenewTrack</name>
        <label>Set Manual Renew Track</label>
        <locationX>300</locationX>
        <locationY>350</locationY>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Track__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Manual</stringValue>
            </value>
        </assignmentItems>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Owner_Required__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <booleanValue>true</booleanValue>
            </value>
        </assignmentItems>
    </assignments>
    <decisions>
        <name>Decision_IsAutoRenewRequested</name>
        <label>Is Auto-Renew Requested?</label>
        <locationX>176</locationX>
        <locationY>220</locationY>
        <defaultConnector>
            <targetReference>Assignment_SetManualRenewTrack</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>ManualRenewal_Default</defaultConnectorLabel>
        <rules>
            <name>AutoRenewRequested</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Auto_Renew_Requested__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Assignment_SetAutoRenewTrack</targetReference>
            </connector>
            <label>Auto-Renew Requested</label>
        </rules>
    </decisions>
    <description>Before-save. Classifies the triggering Contract's renewal track (Auto vs Manual) from Auto_Renew_Requested__c and sets Renewal_Owner_Required__c accordingly. No recordCreates/recordUpdates/actionCalls/subflows by design -- see flow/record-triggered-flow-patterns for the before-save save-order rule this follows (assignments to $Record persist without a second DML). triggerOrder 10 on Contract.</description>
    <environments>Default</environments>
    <interviewLabel>Contract BeforeSave ClassifyRenewalTrack {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Contract BeforeSave ClassifyRenewalTrack</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>DefaultMode</runInMode>
    <start>
        <locationX>176</locationX>
        <locationY>50</locationY>
        <connector>
            <targetReference>Decision_IsAutoRenewRequested</targetReference>
        </connector>
        <filterFormula>NOT(ISBLANK({!$Record.EndDate}))</filterFormula>
        <object>Contract</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>
    <status>Draft</status>
    <triggerOrder>10</triggerOrder>
</Flow>
```

### Why each name is shaped this way

- **Flow name** `Contract_BeforeSave_ClassifyRenewalTrack` — object first so a
  metadata diff or a Flow list sorts every Contract flow together;
  `ClassifyRenewalTrack` is a verb phrase, not a noun, so the intent survives
  being read out of context in a deploy log.
- **`Decision_IsAutoRenewRequested`** — `Decision_` verb prefix
  (`check_flow_element_naming_conventions.py` `ELEMENT_VERB_PREFIX["decisions"]`),
  and the remainder is framed as the yes/no question the rule actually tests
  (Concept 1). Compare the negative fixture below, where this becomes
  `Decision_2`.
- **`AutoRenewRequested`** (the matched outcome) and
  **`ManualRenewal_Default`** (the default outcome) — both are affirmative,
  business-readable, and neither matches the checker's `WEAK_OUTCOME` pattern
  (`^(yes|no|y|n|match\d*|outcome\d*|rule\d*|default_?\d+)$`, case-insensitive).
  Pattern 3 forbids bare `Yes`/`No` for exactly this reason: outcomes surface
  in fault diagnostics detached from their parent Decision.
- **`Assignment_SetAutoRenewTrack` / `Assignment_SetManualRenewTrack`** —
  `Assignment_<Verb><Object>` per the Decision Guidance table. Neither
  Assignment nor Decision declares a `faultConnector` in the Metadata API
  (see the field grounding above), so Pattern 5 / `W-FAULT-TARGET` does not
  apply to this flow — there is nothing here that can fault.
- **No resource variables.** The flow reads and writes `$Record` fields
  directly; there is no `variables`/`formulas`/`constants`/`choices` block,
  so Concept 2's prefix table (`var`/`coll`/`map`/…) has nothing to apply to
  in this particular example. `references/examples.md` Example 2 and
  `templates/flow-element-naming-conventions-template.md` § 3 cover the
  resource-prefix case for a flow that does declare variables.

---

## 2. The negative fixture (described, not shipped as a second file)

Same flow, same object model, three renames — each one taken straight from a
rule this skill's checker enforces:

1. **`Decision_IsAutoRenewRequested` → `Decision_2`.** Ends `_\d+`, so it
   matches the checker's `AUTO_NAME` pattern → **`E-AUTONAME`**. The Label is
   also changed from "Is Auto-Renew Requested?" to the Flow Builder default
   **"Decision"** → **`E-LABEL-DEFAULT`** (matches `DEFAULT_LABEL`).
2. **`ManualRenewal_Default` → `No`.** A bare `No` default outcome — exactly
   what Pattern 3 forbids → **`E-OUTCOME-WEAK`**.
3. **`Assignment_SetAutoRenewTrack` → `SetAutoRenewTrack`.** Drops the
   `Assignment_` verb prefix the Decision Guidance table requires for this
   element type → **`W-VERB-PREFIX`** (WARN, not ERROR — this is house style,
   per the checker's own module docstring, not a platform constraint).

Nothing else changes: same fields, same object, same `triggerOrder`, same
absence of DML. The point is that these four renames are independently
detectable — each maps to exactly one rule code, so the fixture doubles as a
worked answer key for what each code means in practice.

---

## 3. `package.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Contract_BeforeSave_ClassifyRenewalTrack</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Contract.Auto_Renew_Requested__c</members>
        <members>Contract.Renewal_Track__c</members>
        <members>Contract.Renewal_Owner_Required__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

---

## 4. Deploy order

```bash
# 0. lint the flow before anything reaches an org
python3 skills/flow/flow-element-naming-conventions/scripts/check_flow_element_naming_conventions.py \
  --manifest-dir force-app/main/default

# 1. check-only validation of the whole manifest
sf project deploy validate \
  --manifest manifest/package.xml \
  --target-org my-sandbox \
  --test-level RunLocalTests

# 2. the three custom fields first: the flow's Start filterFormula and both
#    Assignment branches reference them, and a flow referencing a field that
#    does not exist yet fails at deploy, not at runtime
sf project deploy start \
  --metadata "CustomField:Contract.Auto_Renew_Requested__c" \
  --metadata "CustomField:Contract.Renewal_Track__c" \
  --metadata "CustomField:Contract.Renewal_Owner_Required__c" \
  --target-org my-sandbox

# 3. the flow itself, as Draft
sf project deploy start --metadata "Flow:Contract_BeforeSave_ClassifyRenewalTrack" --target-org my-sandbox

# 4. activate deliberately: flip <status> to Active, redeploy, and confirm
#    triggerOrder in Flow Trigger Explorer before anyone saves a Contract
sf project deploy start --metadata "Flow:Contract_BeforeSave_ClassifyRenewalTrack" --target-org my-sandbox
```

Step 0 is the naming gate; step 1 is the only place a bad `<object>` or a
`<targetReference>` pointing at a nonexistent element surfaces before a user
hits it. Run both on every change, not only the first.

---

## 5. Verification

Run the checker with its documented argument form
(`--manifest-dir <path>`; see `scripts/check_flow_element_naming_conventions.py`
module docstring) against the extracted positive example, then against the
negative fixture from § 2. Both runs below are the checker's real output —
not paraphrased — captured against exactly the two files described above,
each as the only `*.flow-meta.xml` in its manifest directory.

**Positive example — clean, exit 0:**

```text
$ python3 skills/flow/flow-element-naming-conventions/scripts/check_flow_element_naming_conventions.py \
    --manifest-dir <dir containing only Contract_BeforeSave_ClassifyRenewalTrack.flow-meta.xml>
No issues found.
$ echo $?
0
```

`No issues found.` is the checker's zero-finding message — printed instead of
an `N error(s)` line only when there is nothing at all to report (no ERROR,
no WARN, no INFO). Zero ERROR is what makes the exit code 0.

**Negative fixture — 3 ERROR, 1 WARN, exit 1:**

```text
$ python3 skills/flow/flow-element-naming-conventions/scripts/check_flow_element_naming_conventions.py \
    --manifest-dir <dir containing only the mis-named twin from § 2>
ERROR [E-AUTONAME] <path>/Contract_BeforeSave_ClassifyRenewalTrack.flow-meta.xml: <decisions> API Name `Decision_2` is a Flow Builder / Process Builder auto-name. It carries no information in a fault email (well-architected.md Anti-Pattern 1) and this skill treats the rename pass as required, not deferred (gotchas.md Gotcha 5).
ERROR [E-LABEL-DEFAULT] <path>/Contract_BeforeSave_ClassifyRenewalTrack.flow-meta.xml: <decisions> `Decision_2` keeps the Flow Builder default Label "Decision". examples.md Example 1 lists this as the BAD column: the label must say what the element does, not what type it is.
ERROR [E-OUTCOME-WEAK] <path>/Contract_BeforeSave_ClassifyRenewalTrack.flow-meta.xml: Decision `Decision_2` names its default outcome "No". SKILL.md Pattern 3 prefers `<NegativeCondition>_Default` so the next reader does not have to inspect every other outcome to learn what it catches.
WARN  [W-VERB-PREFIX] <path>/Contract_BeforeSave_ClassifyRenewalTrack.flow-meta.xml: <assignments> element `SetAutoRenewTrack` does not start with `Assignment_`. SKILL.md's Decision Guidance table maps this element type to `Assignment_<Object>[_<Qualifier>]` so a fault email names the verb and the noun without opening Flow Builder.

3 error(s), 1 warning(s), 0 info.
$ echo $?
1
```

(`<path>` above stands for the scratch manifest directory the fixture was linted from — every message after the file path is the checker's unedited output.)

Each line maps to exactly one of the three renames in § 2 — one auto-name,
one default label, one weak outcome, and one house-style verb prefix WARN
that would only fail the build under `--strict`.

**Bad input, for completeness** (not tied to either fixture — this is the
checker's `--manifest-dir` handling on its own):

```text
$ python3 .../check_flow_element_naming_conventions.py --manifest-dir /nonexistent
ERROR [E-NO-DIR] /nonexistent: manifest directory not found.
$ echo $?
2

$ python3 .../check_flow_element_naming_conventions.py --manifest-dir <empty dir>
WARN  [W-EMPTY] <empty dir>: no *.flow-meta.xml files found; nothing to lint. ...

0 error(s), 1 warning(s), 0 info.
$ echo $?
0
```

An empty directory is a WARN (nothing to lint is not itself a naming defect),
not an ERROR — only a missing/non-directory `--manifest-dir` forces exit 2.
