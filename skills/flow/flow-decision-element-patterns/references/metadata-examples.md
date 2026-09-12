# Metadata Examples — Opportunity Renewal Routing

One complete, deployable artefact rather than the condition-level fragments in
`references/examples.md`. Every structural claim below cites the Metadata API
Developer Guide (v62) by line in the extracted text used to author this file,
shown as `api_meta.txt L<n>`.

## The Business Problem

Renewal Opportunities need an owning desk stamped on save. Three populations
exist and they are not variations of one rule:

1. Enterprise renewals that are **at risk** — high risk score, or auto-renew
   switched off. These go to a named desk with a human on it.
2. Enterprise renewals that are **fine**. Same desk, different queue, no alert.
3. Everything else — the standard renewal pool.

Plus a fourth population nobody asks about and which exists in every org: records
whose segment field is empty. That is not "everything else." It is a data
problem wearing the costume of a business decision, and it is the reason this
example has a null-guard outcome.

## Object Model

Four custom fields on the standard `Opportunity` object. No custom object is
needed; encoding the route as a field on the record is what makes the decision
auditable after the fact.

| API name | Type | Role in the Decision |
|---|---|---|
| `Renewal_Owner_Segment__c` | Picklist (`Enterprise`, `Mid_Market`, `SMB`) | Left-hand side of the segment conditions, and the field the null guard tests. |
| `Renewal_Risk_Score__c` | Number(3, 0) | Numeric threshold in the advanced condition logic. |
| `Auto_Renew__c` | Checkbox | Boolean condition compared against `booleanValue`, never a string. |
| `Renewal_Route__c` | Text(40) | Written by each outcome; this is what makes "why did this record go there?" answerable. |

Picklist conditions compare the **API value** (`Mid_Market`), not the label
(`Mid Market`). Take it from the field's value set, not from a record page.

## The Flow

A before-save record-triggered flow: `triggerType` `RecordBeforeSave` and
`recordTriggerType` `CreateAndUpdate` (`api_meta.txt` L72448–L72453,
L72539–L72542). Before-save is the right shape here because every outcome only
stamps a field on the triggering record — Assignment elements, no DML.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <description>Stamps Renewal_Route__c on save so renewal ownership is decided once, in one place.</description>
    <environments>Default</environments>
    <interviewLabel>Opportunity Renewal Routing {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Opportunity Renewal Routing</label>
    <processType>AutoLaunchedFlow</processType>
    <status>Draft</status>

    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Route_Renewal</targetReference>
        </connector>
        <object>Opportunity</object>
        <recordTriggerType>CreateAndUpdate</recordTriggerType>
        <triggerType>RecordBeforeSave</triggerType>
    </start>

    <decisions>
        <name>Route_Renewal</name>
        <label>Route Renewal</label>
        <locationX>50</locationX>
        <locationY>134</locationY>
        <defaultConnector>
            <targetReference>Assign_Standard_Renewal</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Standard Renewal (segment set, not Enterprise)</defaultConnectorLabel>

        <rules>
            <name>At_Risk_Enterprise</name>
            <label>At Risk Enterprise</label>
            <conditionLogic>1 AND (2 OR 3)</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Renewal_Owner_Segment__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Enterprise</stringValue>
                </rightValue>
            </conditions>
            <conditions>
                <leftValueReference>$Record.Renewal_Risk_Score__c</leftValueReference>
                <operator>GreaterThanOrEqualTo</operator>
                <rightValue>
                    <numberValue>70.0</numberValue>
                </rightValue>
            </conditions>
            <conditions>
                <leftValueReference>$Record.Auto_Renew__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>false</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Assign_At_Risk_Enterprise</targetReference>
            </connector>
        </rules>

        <rules>
            <name>Enterprise_Standard</name>
            <label>Enterprise Standard</label>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Renewal_Owner_Segment__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Enterprise</stringValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Assign_Enterprise_Standard</targetReference>
            </connector>
        </rules>

        <rules>
            <name>Segment_Missing</name>
            <label>Segment Missing</label>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>$Record.Renewal_Owner_Segment__c</leftValueReference>
                <operator>IsNull</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Assign_Needs_Segment</targetReference>
            </connector>
        </rules>
    </decisions>

    <assignments>
        <name>Assign_At_Risk_Enterprise</name>
        <label>Assign At Risk Enterprise</label>
        <locationX>-138</locationX>
        <locationY>278</locationY>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Route__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Enterprise Renewal Desk - At Risk</stringValue>
            </value>
        </assignmentItems>
    </assignments>

    <assignments>
        <name>Assign_Enterprise_Standard</name>
        <label>Assign Enterprise Standard</label>
        <locationX>50</locationX>
        <locationY>278</locationY>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Route__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Enterprise Renewal Desk</stringValue>
            </value>
        </assignmentItems>
    </assignments>

    <assignments>
        <name>Assign_Needs_Segment</name>
        <label>Assign Needs Segment</label>
        <locationX>238</locationX>
        <locationY>278</locationY>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Route__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Needs Segment - Data Quality Queue</stringValue>
            </value>
        </assignmentItems>
    </assignments>

    <assignments>
        <name>Assign_Standard_Renewal</name>
        <label>Assign Standard Renewal</label>
        <locationX>426</locationX>
        <locationY>278</locationY>
        <assignmentItems>
            <assignToReference>$Record.Renewal_Route__c</assignToReference>
            <operator>Assign</operator>
            <value>
                <stringValue>Standard Renewal Pool</stringValue>
            </value>
        </assignmentItems>
    </assignments>
</Flow>
```

### Why It Is Built That Way

**Outcome order is evaluation order.** `FlowDecision.rules` are "evaluated in
the order that they're listed, and the connector of the first true rule is used.
If no rules are true, then the default connector is used. In Flow Builder, rules
are referred to as decision outcomes" (`api_meta.txt` L70247–L70250). So
`At_Risk_Enterprise` must precede `Enterprise_Standard`: the second is a strict
superset of the first, and reversing them would make the at-risk branch dead code
that Flow Builder never warns about. The review question for every adjacent pair
is "which record reaches this outcome and not the one above it?"

**The advanced `conditionLogic` says exactly what the requirement says.**
`FlowRule.conditionLogic` takes `and`, `or`, or advanced logic such as
`1 AND (2 OR 3)`, capped at 1,000 characters when advanced logic is used
(`api_meta.txt` L71306–L71313). `1 AND (2 OR 3)` reads as "Enterprise, and
either high risk or auto-renew off." Written as `1 AND 2 OR 3` it would be a bet
on precedence placed at review time, for no gain.

**The null guard is an outcome, not a comment.** `Segment_Missing` uses `IsNull`
against `<booleanValue>true</booleanValue>` — the shape the guide's own Decision
example uses (`api_meta.txt` L73342–L73344). `rightValue` is a
`FlowElementReferenceOrValue`, and the guide is explicit that you "specify only
one of the fields" (`api_meta.txt` L70411–L70412), so `booleanValue` here and
nothing else. On a text field where whitespace is plausible, `IsBlank` is the
stricter test — "a text value with zero characters or with only whitespace" —
but it requires API version 61.0 or later (`api_meta.txt` L70090–L70094).

**The default is named after its case.** `defaultConnectorLabel` is "Standard
Renewal (segment set, not Enterprise)" rather than "Default Outcome". The default
connector is what runs when no rule is true (`api_meta.txt` L70233–L70234), which
means it carries both the intended fallback and every case nobody considered.
Naming it is the only thing that separates the two in triage afterwards.

**Nothing is nested.** Four outcomes in one flat element, each landing on its own
Assignment. A second Decision beneath this one would add another default that
absorbs cases silently.

## `package.xml`

API version 62.0, fields and flow in one manifest:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Opportunity.Auto_Renew__c</members>
        <members>Opportunity.Renewal_Owner_Segment__c</members>
        <members>Opportunity.Renewal_Risk_Score__c</members>
        <members>Opportunity.Renewal_Route__c</members>
        <name>CustomField</name>
    </types>
    <types>
        <members>Opportunity_Renewal_Routing</members>
        <name>Flow</name>
    </types>
    <version>62.0</version>
</Package>
```

## Deploy Order

1. **Custom fields first.** The flow references `Renewal_Owner_Segment__c`,
   `Renewal_Risk_Score__c`, `Auto_Renew__c`, and `Renewal_Route__c` by API name.
   A flow deployed ahead of its fields fails on an unresolved reference. One
   manifest containing both types is fine — the platform resolves the ordering
   within a deployment — but a *field rename* split across two releases is not,
   and that is the version of this mistake that reaches production.
2. **The flow as `Draft` first.** `Flow.status` accepts `Active`, `Draft`,
   `Obsolete`, `InvalidDraft`, and `UnderReview` (`api_meta.txt` L68416–L68423).
   Deploying changes to an *active* flow works in a scratch org or sandbox
   without ceremony; in production it requires the **Deploy processes and flows
   as active** preference to be enabled first (`api_meta.txt` L68038–L68040).
   Decide that before the release, not during it.
3. **Activate, then verify the route field on a sample of each population.**
   Four outcomes means four records, one of which must have an empty segment.
4. **Only then retire whatever this replaced.** A flow version can be deleted
   only when it is not active and has no paused interviews; if paused interviews
   exist, wait for them to finish or delete them (`api_meta.txt` L68041–L68042).

Two file-level traps worth knowing before the first deploy. In Metadata API
format flows live in the `Flow` directory of the package with the extension
`.flow`, the file name matching the flow's unique full name
(`api_meta.txt` L68049–L68051); the source-format `Opportunity_Renewal_Routing.flow-meta.xml`
shown above is the same component under the SFDX project layout.
`UNVERIFIED (2026-09-12):` the `-meta.xml` source-format suffix is a project-format
convention and is not stated in the Metadata API guide section used here. And
spaces in a flow file name "can lead to errors when you deploy the flow"; leading
or trailing spaces are stripped on deploy (`api_meta.txt` L68036–L68037) — so
name the file after the API name, never after the label.

## Verification

Run the package's checker against the retrieved metadata directory. It reads
`*.flow-meta.xml` and `*.flow`, and enforces the `FlowDecision` / `FlowRule` /
`FlowCondition` contract cited above.

```bash
python3 skills/flow/flow-decision-element-patterns/scripts/check_flow_decision_element_patterns.py \
    --manifest-dir force-app/main/default/flows
```

On the flow above:

```text
-- 0 ERROR, 0 WARN, 0 INFO
```

Exit code 0. The checker blocks on ERROR findings only; pass `--strict` to make
WARN findings blocking too, which is the right setting in CI once a team has
cleared its existing warnings.

What it will stop, with the guide fact behind each:

| Finding | Level | Grounded in |
|---|---|---|
| `operator` is `None` | ERROR | `None` exists to "save a flow with an incomplete condition" (`api_meta.txt` L70104–L70106) — a work-in-progress marker that deploys happily. |
| `rightValue` sets more than one typed child | ERROR | "Make sure that you specify only one of the fields" (`api_meta.txt` L70411–L70412). |
| `FlowRule.label` missing | ERROR | `label` is Required on `FlowRule` (`api_meta.txt` L71325). |
| `leftValueReference` or `operator` missing | ERROR | Both Required on `FlowCondition` (`api_meta.txt` L70067, L70070). |
| Advanced `conditionLogic` over 1,000 characters, unbalanced parentheses, or a condition number out of range | ERROR | Advanced logic and its 1,000-character cap (`api_meta.txt` L71306–L71313). |
| An outcome made unreachable by an earlier, broader one | WARN | First true rule wins, in listed order (`api_meta.txt` L70247–L70250). |
| No `defaultConnector`, or a generic `defaultConnectorLabel` | WARN | The default connector runs when no rule is true (`api_meta.txt` L70233–L70236). |
| A text comparison with no `IsNull` / `IsBlank` outcome on the same field | WARN | `IsNull` is "a value that is either not set or references no value" (`api_meta.txt` L70099–L70101); nothing else in the element covers that state. |
| A boolean-RHS operator given a non-boolean right-hand value | WARN | The guide's Decision example pairs `IsNull` with `booleanValue` (`api_meta.txt` L73342–L73344). |
| A hardcoded 15- or 18-character Id literal | WARN | Routing on a person rather than a role; see `references/gotchas.md` Gotcha 1. |
| Decisions chained three deep | WARN | Each level adds a default that absorbs cases; see `references/gotchas.md` Gotcha 5. |

`UNVERIFIED (2026-09-12):` the checker's ordering rule compares only outcomes
whose `conditionLogic` is plain `and`, and detects the subset case exactly. An
outcome made unreachable through advanced logic, overlapping ranges, or
`Contains` collisions is not detectable structurally and stays a human review
job — the "which record reaches this and not the one above it?" pass.
