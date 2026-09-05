# Metadata Examples — Flow Formula And Expression Patterns

Deployable `*.flow-meta.xml` for the four places a formula lives inside a flow's XML:
a `filterFormula` entry condition on `<start>`, three `<formulas>` (`FlowFormula`)
resources with `dataType` and `scale` declared, a `<textTemplates>` entry with
`isViewedAsPlainText` false and merge fields, and a `<decisions>` rule that branches on a
Boolean formula resource. Plus a `FlowTest` that asserts the formula's output, a
`package.xml`, deploy order, and two verification steps you can actually run.

---

## Read this before you trust any function semantics below

The **Formula Operators and Functions** reference — the document that defines what
`ISBLANK`, `ISPICKVAL`, `TEXT`, `CASE`, `MOD`, `DATE`, `MAX`, `BLANKVALUE` and every other
formula function actually *do* — is a help.salesforce.com article. It is **not** in the
PDF corpus this file is grounded against (`api_meta.txt`, `object_reference.txt`,
`apexdev.txt`, `salesforce_app_limits_cheatsheet.txt`). `grep -n -i "Formula Operators and
Functions"` returns nothing in `api_meta.txt`, `object_reference.txt` or `apexrefguide.txt`;
the only mention anywhere is `apexdev.txt` L28148, which names the document without
reproducing it.

So: **every element name, enum value, default and version floor below is cited to
`api_meta.txt` or `object_reference.txt` by `grep -n` line. Every claim about what a
formula *function* returns is marked `UNVERIFIED (2026-09-05)` inline.** They are not
guesses — they are the working semantics practitioners rely on — but this corpus cannot
confirm them, and §7 gives you a SOQL query that settles the *membership* question
(is this function legal in Flow at all?) from your own org rather than from memory.

### Negative results worth writing down

| Thing the skill says exists | Search | Result |
|---|---|---|
| `$Record__Prior` | `grep -n 'Record__Prior' api_meta.txt` | **0 hits.** `$Record` is grounded (L74307, L74350, L102253); the prior-value token is not documented in the Metadata API guide. |
| `$Flow.FaultMessage`, `$Flow.CurrentDate`, `$Flow.InterviewStartTime` | `grep -n '\$Flow\.'` | **0 hits each.** Only `$Flow.CurrentDateTime` (L27212, L73380, L73641, L73744), `$Flow.ActiveStages` (L69784–L69840) and `$Flow.CurrentStage` (L71996) appear. |
| `$Flow.InterviewGuid` | `grep -n 'InterviewGuid' api_meta.txt` | **0 hits.** The sibling `flow/fault-handling` reached the same negative independently. If you see it recommended for correlating fault logs, it is undocumented in this corpus — state the negative rather than repeating the claim. |
| `$Profile.`, `$Setup.`, `$Label.` in a Flow context | `grep -n '\$Profile\.\|\$Setup\.\|\$Label\.'` | **0 Flow hits.** `$Label.` appears only inside a Gift Entry YAML block (L78590+), `$Organization.` at L66217 and L140282, `$User.` at L12949/L31153/L66249/L66825, `$Permission.CustomPermission` / `$Permission.StandardPermission` at L67560–L67562. |
| A "formula" value for `<conditionLogic>` on a decision rule | `grep -n 'formula_evaluates'` | **0 hits.** `FlowRule.conditionLogic` (L71301–L71313) documents only `and`, `or`, and advanced logic like `1 AND (2 OR 3)`. See §4. |
| A 5,000-character / 5,000-byte compiled-formula ceiling | `grep -n -i "5,000 bytes\|5000 bytes\|Compiled formula"` across all four guides | **0 hits.** What *is* grounded is 3,900 characters — see §3. |

---

## Assumed org model

A field-service business triages warranty claims. Nothing here overlaps the sibling
examples: `flow/flow-loop-element-patterns` uses `Grant_Application__c`,
`flow/fault-handling` uses `Invoice`/`Payment`, `flow/flow-bulkification` uses
`Shipment__c`, `flow/subflows-and-reusability` uses `Case`.

| Component | Type | Why the formula work needs it |
|---|---|---|
| `Warranty_Claim__c` | Custom object | the triggering record |
| `Claim_Amount__c` | Currency, **required** | never null — the non-guarded operand |
| `Deductible__c` | Currency, **not required** | the nullable operand every formula here has to guard |
| `Approved_Amount__c` | Currency, scale 2 | the Currency formula's write target |
| `Received_On__c` | Date | input to the business-day formula |
| `Due_On__c` | Date | the business-day formula's write target |
| `Claim_Status__c` | Picklist: `Submitted`, `Under_Review`, `Approved`, `Denied` | the `ISPICKVAL` operand and the `filterFormula`'s change test |
| `Priority_Tier__c` | Text(40) | the decision's write target |
| `Claim_Log__c` | Custom object; `Source__c`, `Message__c` (Long Text) | every `faultConnector` target |

Canonical shapes this file does not re-invent:

- `templates/flow/RecordTriggered_Skeleton.flow-meta.xml` — the `<start>` block shape.
  §1 adds `filterFormula` to it; the skeleton owns the rest.
- `templates/flow/FaultPath_Template.md` — what a `faultConnector` must land on.
  `Log_Failure` below is that shape with a formula-built message.
- `flow/fault-handling` owns `$Flow.FaultMessage` semantics. This file only shows the
  formula that concatenates it.
- `flow/flow-loop-element-patterns` owns `FlowCollectionProcessor` and its `<formula>`
  child (formula-based collection filtering). Do not duplicate it here — §6 points at it.

---

## 1. The deployable flow — `Warranty_Claim_Triage.flow-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Flow xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <description>Warranty claim triage. Every formula resource declares dataType; the Currency resource also declares scale. Nullable operands are guarded inside the resource, not at the call site.</description>
    <environments>Default</environments>
    <interviewLabel>Warranty Claim Triage {!$Flow.CurrentDateTime}</interviewLabel>
    <label>Warranty Claim Triage</label>
    <processType>AutoLaunchedFlow</processType>
    <runInMode>SystemModeWithSharing</runInMode>
    <status>Draft</status>

    <start>
        <locationX>50</locationX>
        <locationY>0</locationY>
        <connector>
            <targetReference>Route_Claim</targetReference>
        </connector>
        <filterFormula>AND(
  NOT(ISBLANK({!$Record.Received_On__c})),
  {!$Record.Claim_Amount__c} &gt; 0,
  TEXT({!$Record.Claim_Status__c}) &lt;&gt; TEXT({!$Record__Prior.Claim_Status__c})
)</filterFormula>
        <object>Warranty_Claim__c</object>
        <recordTriggerType>Update</recordTriggerType>
        <triggerType>RecordAfterSave</triggerType>
    </start>

    <formulas>
        <name>dueDate</name>
        <dataType>Date</dataType>
        <expression>{!$Record.Received_On__c}
+ 7
+ CASE(MOD({!$Record.Received_On__c} - DATE(1985, 6, 24), 7),
    5, -1,
    6, -2,
    0)</expression>
    </formulas>

    <formulas>
        <name>netClaimAmount</name>
        <dataType>Currency</dataType>
        <expression>MAX(
  0,
  {!$Record.Claim_Amount__c} - BLANKVALUE({!$Record.Deductible__c}, 0)
)</expression>
        <scale>2</scale>
    </formulas>

    <formulas>
        <name>isEscalation</name>
        <dataType>Boolean</dataType>
        <expression>AND(
  {!netClaimAmount} &gt; 25000,
  NOT(ISPICKVAL({!$Record.Claim_Status__c}, &quot;Denied&quot;))
)</expression>
    </formulas>

    <formulas>
        <name>faultLogLine</name>
        <dataType>String</dataType>
        <expression>&quot;Warranty_Claim_Triage failed at &quot;
&amp; TEXT({!$Flow.CurrentDateTime})
&amp; &quot; on claim &quot; &amp; {!$Record.Id}
&amp; &quot;: &quot; &amp; {!$Flow.FaultMessage}</expression>
    </formulas>

    <textTemplates>
        <name>adjusterSummary</name>
        <isViewedAsPlainText>false</isViewedAsPlainText>
        <text>&lt;p&gt;Claim &lt;b&gt;{!$Record.Name}&lt;/b&gt; nets {!netClaimAmount}, due {!dueDate}.&lt;/p&gt;</text>
    </textTemplates>

    <decisions>
        <name>Route_Claim</name>
        <label>Route Claim</label>
        <locationX>176</locationX>
        <locationY>134</locationY>
        <defaultConnector>
            <targetReference>Stamp_Standard</targetReference>
        </defaultConnector>
        <defaultConnectorLabel>Standard</defaultConnectorLabel>
        <rules>
            <name>Escalate</name>
            <conditionLogic>and</conditionLogic>
            <conditions>
                <leftValueReference>isEscalation</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <booleanValue>true</booleanValue>
                </rightValue>
            </conditions>
            <connector>
                <targetReference>Stamp_Escalated</targetReference>
            </connector>
            <label>Escalate</label>
        </rules>
    </decisions>

    <recordUpdates>
        <name>Stamp_Escalated</name>
        <label>Stamp Escalated</label>
        <locationX>50</locationX>
        <locationY>260</locationY>
        <faultConnector>
            <targetReference>Log_Failure</targetReference>
        </faultConnector>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Approved_Amount__c</field>
            <value>
                <elementReference>netClaimAmount</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Due_On__c</field>
            <value>
                <elementReference>dueDate</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Priority_Tier__c</field>
            <value>
                <stringValue>Escalated</stringValue>
            </value>
        </inputAssignments>
        <object>Warranty_Claim__c</object>
    </recordUpdates>

    <recordUpdates>
        <name>Stamp_Standard</name>
        <label>Stamp Standard</label>
        <locationX>300</locationX>
        <locationY>260</locationY>
        <faultConnector>
            <targetReference>Log_Failure</targetReference>
        </faultConnector>
        <filters>
            <field>Id</field>
            <operator>EqualTo</operator>
            <value>
                <elementReference>$Record.Id</elementReference>
            </value>
        </filters>
        <inputAssignments>
            <field>Approved_Amount__c</field>
            <value>
                <elementReference>netClaimAmount</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Due_On__c</field>
            <value>
                <elementReference>dueDate</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Priority_Tier__c</field>
            <value>
                <stringValue>Standard</stringValue>
            </value>
        </inputAssignments>
        <object>Warranty_Claim__c</object>
    </recordUpdates>

    <recordCreates>
        <name>Log_Failure</name>
        <label>Log Failure</label>
        <locationX>500</locationX>
        <locationY>380</locationY>
        <inputAssignments>
            <field>Message__c</field>
            <value>
                <elementReference>faultLogLine</elementReference>
            </value>
        </inputAssignments>
        <inputAssignments>
            <field>Source__c</field>
            <value>
                <stringValue>Warranty_Claim_Triage</stringValue>
            </value>
        </inputAssignments>
        <object>Claim_Log__c</object>
    </recordCreates>
</Flow>
```

### How to read it

- **`<filterFormula>` on `<start>`** — `api_meta.txt` L72390–L72392: *"A formula that's
  used to filter what records execute the flow during a save. Available only in
  record-triggered flows. This field is available in API version 55.0 and later."* It is the
  formula-shaped alternative to the `<filters>` + `<filterLogic>` pair (L72395–L72404).
  Use it when the entry condition needs a *function* — `ISBLANK`, `TEXT`, a comparison
  between two fields — which the condition-row grammar (`field`, `operator`, `value`;
  `FlowRecordFilter` L71066–L71090) cannot express.
- **`{!$Record__Prior....}` inside `filterFormula`** — UNVERIFIED (2026-09-05): the token
  is not documented anywhere in `api_meta.txt` (0 hits for `Record__Prior`), only
  `$Record` is. The *behaviour* it substitutes for — "did this field change on this
  update?" — has a grounded declarative equivalent instead:
  `doesRequireRecordChangedToMeetCriteria` on `FlowStart` (L72315–L72318) and on
  `FlowRule` (L71321–L71324). `flow/flow-record-save-order-interaction` owns that field;
  prefer it over a prior-value formula when the condition is expressible as a condition
  row, because it is documented and this token is not.
- **`<dataType>` on every `<formulas>`** — `api_meta.txt` L70599–L70609: valid values are
  `Boolean`, `Currency`, `Date`, `DateTime`, `Number`, `String`, `Time`, and
  *"dataType defaults to Number if it isn't defined in a formula"*, available in API 31.0+.
  That default is the single most consequential line in the FlowFormula section: an
  undeclared Text formula silently becomes a Number formula. The checker flags it.
- **`<expression>`** — L70611–L70614: *Required.* *"Salesforce formula expression. The
  return value must match the data type."* The guide states the contract; it does not
  state what happens when the return type disagrees.
- **`<scale>` on `netClaimAmount`** — L70618–L70622: *"Scale of the return value,
  specifically, the number of digits to the right of the decimal point. Available only when
  the data type is Number or Currency. Corresponds to the Decimal Places field in Flow
  Builder."* Omitting it on a Currency formula that feeds a Currency field is how you get a
  value that does not match what the record shows. The guide does not say what `scale`
  defaults to when omitted — that is a genuine gap, not an omission here.
- **`{!netClaimAmount}` inside `isEscalation`** — formula-to-formula composition. The
  guide's own sample composes the same way: `<formulas><name>created_or_updated</name>`
  references the element `{!Create_Contact}` at L73357–L73362.
- **`<textTemplates>`** — L72820–L72831: `isViewedAsPlainText` *"If set to true, the flow
  resource remembers the View as Plain Text setting… If set to false, the flow resource
  uses the View as Rich Text setting. The default value is false."* and `text`
  *"Actual text of the template. Supports merge fields."* The guide's own sample at
  L73573–L73577 sets `false` and merges a formula resource by name — exactly the shape
  above. Because `false` means **rich text**, the `<p>`/`<b>` markup renders; the same
  string with `true` renders the tags literally.
- **The decision branches on a Boolean formula resource, not on inline formula syntax.**
  `isEscalation` is the `leftValueReference`; the rule compares it to `booleanValue true`
  with `conditionLogic` `and`. This is the fully-documented shape (`FlowRule` L71301–L71325,
  and the guide's own decision sample at L73310–L73325). §4 covers the inline-formula
  alternative and why this file does not deploy it.
- **`recordTriggerType` + `triggerType`** — `RecordTriggerType` values `Create`, `Update`,
  `CreateAndUpdate`, `Delete`, `None` at L72448–L72460; `FlowTriggerType` includes
  `RecordAfterSave` (API 49.0+) at L72522–L72524. Note the discrepancy: L72458 says
  `recordTriggerType` is *"Available only when triggerType is RecordBeforeSave or
  DataCloudDataChange"*, yet `filterFormula` (L72390) is scoped to record-triggered flows
  generally and `RecordAfterSave` is a documented `triggerType`. UNVERIFIED
  (2026-09-05): the guide's availability sentence and its own enum list disagree; this file
  pairs `Update` with `RecordAfterSave` because that is what Flow Builder emits, and the
  guide gives no other way to express an after-save update trigger.
- **Every DML element carries a `faultConnector`** — `FlowRecordUpdate` L71271–L71274
  (`faultConnector`, `filters`, `inputAssignments`, `inputReference`, `object` — note
  there is **no** `filterLogic` on `FlowRecordUpdate`, so a single filter row is the whole
  criteria). `flow/fault-handling` owns the fault path; this file only shows the formula
  that builds the log line.
- **`{!$Flow.FaultMessage}` in `faultLogLine`** — UNVERIFIED (2026-09-05): 0 hits in
  `api_meta.txt`. Only `$Flow.CurrentDateTime` is grounded, and only as a merge field
  inside `<interviewLabel>` (L27212, L73380, L73641, L73744) — the guide never states its
  semantics either.

### Function-semantics claims in this flow, each UNVERIFIED (2026-09-05)

None of these are in the corpus; all rest on the help.salesforce.com Formula Operators and
Functions reference, which cannot be fetched.

| Claim | Where it is used |
|---|---|
| `ISBLANK(x)` is TRUE for null, and for Text also for empty string | `filterFormula` |
| `TEXT(picklist)` returns the API name, so `TEXT(a) <> TEXT(b)` is a locale-safe change test | `filterFormula` |
| `ISPICKVAL(field, "ApiName")` compares against the API name, not the label | `isEscalation` |
| `BLANKVALUE(x, d)` returns `d` when `x` is null/blank; arithmetic on a null operand otherwise yields null | `netClaimAmount` |
| `MAX(a, b)` returns the larger operand | `netClaimAmount` |
| `Date - Date` yields a Number of days, and `Date + Number` yields a Date | `dueDate` |
| `MOD(n, 7)` against a known-Monday anchor yields 0=Mon … 6=Sun | `dueDate` |
| `CASE(expr, v1, r1, …, default)` returns `default` on no match | `dueDate` |
| `&` concatenates, and a Date/DateTime operand needs `TEXT()` to be locale-deterministic | `faultLogLine` |

`dueDate` computes **five business days** from `Received_On__c`: `+7` for a weekday
receipt, `+6` for Saturday (`MOD` = 5 → `-1`), `+5` for Sunday (`MOD` = 6 → `-2`).
`DATE(1985, 6, 24)` is the Monday anchor that makes `MOD(...)` a weekday index.
**It does not know about holidays** — Business Hours and Holiday records are a separate
mechanism; see `admin/business-hours-and-holidays`. A formula cannot read them.

---

## 2. The FlowTest — `Warranty_Claim_Triage_Formulas.flowtest-meta.xml`

`FlowTest` is the only mechanism in this corpus that asserts a formula's *runtime value*
rather than its syntax. `api_meta.txt` L73960-L73980: components have the suffix
`.flowtest`, live in the `flowtests` folder, and are available in API version 55.0 and later.
`FlowTestCondition.leftValueReference` (L74183-L74188) is *"The reference to the flow
resource that the specified operator applies to"* - a formula resource is a flow resource,
so `netClaimAmount` is a legal left value.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlowTest xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Asserts netClaimAmount guards a null Deductible__c and floors at zero.</description>
    <flowApiName>Warranty_Claim_Triage</flowApiName>
    <label>Formula resources return guarded values</label>
    <testPoints>
        <elementApiName>Start</elementApiName>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordInitial</type>
            <value>
                <sobjectValue>{&quot;Claim_Amount__c&quot;:30000,&quot;Claim_Status__c&quot;:&quot;Submitted&quot;,&quot;Received_On__c&quot;:&quot;2026-09-05&quot;}</sobjectValue>
            </value>
        </parameters>
        <parameters>
            <leftValueReference>$Record</leftValueReference>
            <type>InputTriggeringRecordUpdated</type>
            <value>
                <sobjectValue>{&quot;Claim_Amount__c&quot;:30000,&quot;Claim_Status__c&quot;:&quot;Under_Review&quot;,&quot;Received_On__c&quot;:&quot;2026-09-05&quot;}</sobjectValue>
            </value>
        </parameters>
    </testPoints>
    <testPoints>
        <assertions>
            <conditions>
                <leftValueReference>netClaimAmount</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <numberValue>30000.0</numberValue>
                </rightValue>
            </conditions>
            <errorMessage>netClaimAmount returned null or a discounted value when Deductible__c was absent, so the BLANKVALUE guard is missing or wrong.</errorMessage>
        </assertions>
        <assertions>
            <conditions>
                <leftValueReference>$Record.Priority_Tier__c</leftValueReference>
                <operator>EqualTo</operator>
                <rightValue>
                    <stringValue>Escalated</stringValue>
                </rightValue>
            </conditions>
            <errorMessage>isEscalation did not evaluate true at 30000, so the decision took the default outcome.</errorMessage>
        </assertions>
        <elementApiName>Finish</elementApiName>
    </testPoints>
</FlowTest>
```

### How to read it

`FlowTestPoint.elementApiName` (L74138–L74146) accepts only `Start`
and `Finish` — you cannot assert mid-flow. The `Start` test point supplies the triggering
record via `InputTriggeringRecordInitial` and `InputTriggeringRecordUpdated`
(`FlowTestParameterType`, L74318–L74323); the guide's own sample at L74341–L74385 has the
same two-parameter shape. The two records differ only in `Claim_Status__c`, which is what
makes the `filterFormula`'s change test pass. `FlowTestAssertion.errorMessage`
(L74172–L74177) is what appears in Flow Builder when the condition is false — write it as
the diagnosis, not as a restatement of the assertion. `FlowTestType`
`WithAssertion` (L74110–L74116) is available in API 66.0 and later; below 66.0 omit
`testType` entirely, as this file does.

The deliberate omission: **there is no assertion on `dueDate`.** `FlowTestReferenceOrValue`
(L74247–L74295) offers `dateValue`, so the assertion is expressible — but its expected
value depends on which weekday `2026-09-05` is, which makes the test a restatement of the
formula rather than a check on it. Assert the *guard* (null handling, floor at zero) and
the *branch*, not the arithmetic.

---

## 3. The formula length limit — what is grounded and what is not

The package previously stated a 5,000-character per-formula ceiling and quoted the error
`Compiled formula is too big to execute (5,001 characters)`. **Neither appears in this
corpus.** `grep -n -i "5,000 bytes\|5000 bytes\|Compiled formula"` across `api_meta.txt`,
`object_reference.txt`, `apexdev.txt` and `salesforce_app_limits_cheatsheet.txt` returns
nothing.

What is grounded is **3,900 characters**, from two different guides making two different
claims — do not conflate them:

| Source | Line | Exact claim | What it bounds |
|---|---|---|---|
| `apexdev.txt` | L28143–L28144 | *"Formula evaluation in Apex is bound by the formula field character limit, but not the compile size limit. A formula can contain up to 3,900 characters including spaces, return characters, and comments."* | the **source text** of a formula |
| `object_reference.txt` | L2210 | *"The length of text calculated fields is 3,900 characters or less—anything longer is truncated."* | the **returned string** of a Text formula field |

The `apexdev.txt` sentence is the useful one, and it also confirms a *separate* "compile
size limit" exists without giving its number. UNVERIFIED (2026-09-05): whether the 3,900
source-character limit applies to a Flow `FlowFormula` `<expression>` as well as to an
object formula field is not stated anywhere in the corpus — `FlowFormula` (L70596–L70622)
documents no length bound at all. The checker treats 3,900 as an **advisory** threshold
for that reason, not an error.

Practical consequence: compose defensively well under 3,900 rather than arguing about
5,000. The composition mechanic is grounded — the guide's own flow composes `<formulas>`
by name (L73357–L73362) — even though the ceiling that motivates it is not.

---

## 4. The inline-formula decision outcome, and why §1 does not use it

Flow Builder offers "Formula Evaluates to True" as an outcome criteria mode. In XML that
emits a `<conditionLogic>` value other than `and`/`or` plus a formula body. **The Metadata
API guide documents neither.** `FlowRule` (L71301–L71325) lists exactly three shapes for
`conditionLogic` — `and`, `or`, and advanced logic like `1 AND (2 OR 3)` capped at 1,000
characters — and lists no `<formula>` child at all. `grep -n 'formula_evaluates'` returns 0
hits across `api_meta.txt`.

UNVERIFIED (2026-09-05): the shape below is what Flow Builder emits, reconstructed from
practice, not from the guide. Treat it as a thing your checker must *tolerate and validate*
when it appears in a retrieved flow, not as a shape to author from scratch.

```xml
<rules>
    <name>Escalate_Inline</name>
    <conditionLogic>formula_evaluates_to_true</conditionLogic>
    <conditions>
        <leftValueReference></leftValueReference>
        <operator>EqualTo</operator>
        <rightValue>
            <stringValue>{!netClaimAmount} &gt; 25000</stringValue>
        </rightValue>
    </conditions>
    <connector>
        <targetReference>Stamp_Escalated</targetReference>
    </connector>
    <label>Escalate (inline)</label>
</rules>
```

**Prefer the §1 shape.** A Boolean `FlowFormula` referenced by `leftValueReference` is
fully documented, is assertable by a `FlowTest` (§2a — you cannot assert an inline
condition body), is greppable by name across the flow, and can be reused by a second rule.
The inline form buys nothing except one fewer resource in the list.

---

## 5. `filterFormula` and `filters` on the same `<start>`

Both are documented, adjacent, on `FlowStart`: `filterFormula` at L72390–L72392,
`filterLogic` at L72395–L72400, `filters` at L72402–L72404. **The guide does not say they
are mutually exclusive**, and it does not say which wins when both are populated. There is
no note, no "only one of", no cross-reference between the three field descriptions.

That is a genuine gap, not an inference — so the checker reports the combination as a
**WARN**, not an ERROR. If you are reviewing a flow that has both, the correct action is to
determine empirically in a scratch org which one the runtime honours and then delete the
other, because a reader cannot tell from the XML.

Compare the one place the guide *does* state exclusivity, so you can see what an
exclusivity statement looks like when Salesforce writes one:
`FlowElementReferenceOrValue` (L70411–L70413) — *"Defines a reference to an existing
element or a particular value that you specify. Make sure that you specify only one of the
fields."* No such sentence exists for `filterFormula`/`filters`.

And this is why the checker parses rather than greps: a regex that looks for
`<filterFormula>` and `<filters>` as strings reports the pair on a file whose real defect is
that it does not parse at all. Parse first, then inspect.

---

## 6. Formula-based collection filtering — owned elsewhere

`FlowCollectionProcessor` carries a `<formula>` child and a `<conditionLogic>` that selects
between the formula route and the condition-row route. That element belongs to
`flow/flow-loop-element-patterns`, whose checker already implements the
both-routes-populated rule (`LOOP04`). Do not duplicate it here.

What *this* skill adds to that: the formula inside a Filter processor is subject to the
same three rules as any other Flow formula — it must guard nullable operands, it must use
`ISPICKVAL` for picklists rather than `=` against a label, and it re-evaluates once per
collection item, so an expensive expression there is an `n`-times cost with no loop in the
XML to make that visible.

---

## 7. `package.xml`, deploy order, verification

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Warranty_Claim__c</members>
        <members>Claim_Log__c</members>
        <name>CustomObject</name>
    </types>
    <types>
        <members>Warranty_Claim_Triage</members>
        <name>Flow</name>
    </types>
    <types>
        <members>Warranty_Claim_Triage_Formulas</members>
        <name>FlowTest</name>
    </types>
    <version>62.0</version>
</Package>
```

### Deploy order

1. `CustomObject` — `Warranty_Claim__c` and `Claim_Log__c` with every field named in the
   formulas. A `FlowFormula` `<expression>` referencing a field that does not exist fails
   the deploy of the whole flow, and the error names the flow, not the field.
2. `Flow` — deploys as `Draft`. `FlowSettings.enableFlowDeployAsActiveEnabled`
   (`api_meta.txt` L116877–L116888) defaults to `false` in production and `true` in
   scratch/sandbox/developer orgs, so the same `<status>Active</status>` behaves
   differently by org type. Keep `Draft` in the source and activate deliberately.
3. `FlowTest` — after the flow, because `flowApiName` (L73995–L74000) is Required and must
   resolve.

```bash
sf project retrieve start -m "Flow:Warranty_Claim_Triage" -o my-sandbox
sf project deploy start -x manifest/package.xml -o my-sandbox --dry-run
sf project deploy start -x manifest/package.xml -o my-sandbox
python3 scripts/check_flow_formula_and_expression_patterns.py \
  --manifest-dir force-app/main/default --strict
```

### Verification step 1 — is the function even legal in Flow?

This is the question the missing Formula Operators and Functions reference would answer.
Your org answers it directly. `object_reference.txt` L149310–L149400 documents
`FormulaFunctionAllowedType` (API 48.0 and later): a lookup `FunctionId` → `FormulaFunction`
plus a restricted picklist `Type` whose values are exactly **`FLOW`**, `VALIDATION`, and
`VISUALFORCE`. `FormulaFunction.ExampleString` (L149244–L149247) *"Describes the function
and what arguments you can use with it."*

```sql
SELECT Function.Name, Function.Label, Function.ExampleString
FROM FormulaFunctionAllowedType
WHERE Type = 'FLOW'
ORDER BY Function.Name
```

Run it before you claim any function is or is not available in a Flow formula. It settles
`PRIORVALUE`, `ISCHANGED`, `HYPERLINK`, `REGEX`, `MROUND`, `TIMENOW` and every other
disputed name without a help-article round trip. (The older per-context booleans
`FormulaFunction.IsAllowedInFlowContext` and `IsAllowedInEntityContext` at L149248–L149267
were **removed in API version 48.0 and later** — the guide says so explicitly and tells you
to use `FormulaFunctionAllowedType` instead. Any tooling still reading those booleans is
reading a removed field.)

### Verification step 2 — did the formulas actually write?

```sql
SELECT Id, Name, Claim_Amount__c, Deductible__c, Approved_Amount__c,
       Received_On__c, Due_On__c, Priority_Tier__c
FROM Warranty_Claim__c
WHERE LastModifiedDate = TODAY
ORDER BY LastModifiedDate DESC
LIMIT 20
```

Read three things off it. `Approved_Amount__c` must equal `Claim_Amount__c` on rows where
`Deductible__c` is null — if it is null instead, the `BLANKVALUE` guard is missing and the
null propagated through the subtraction. `Due_On__c` must never land on a Saturday or
Sunday. `Priority_Tier__c` must be `Escalated` on every row over 25,000 — a row over 25,000
sitting at `Standard` means the decision read a null Boolean, which is what happens when
`netClaimAmount` returned null rather than a number.

Then check Setup → Process Automation Settings for the four org-level switches that change
formula behaviour underneath all of this — `doesFormulaEnforceDataAccess` (L116855),
`doesFormulaGenerateHtmlOutput` (L116860), `enableFlowBREncodedFixEnabled` (L116865) and
`enableFlowFormulasFixEnabled` (L116910). `references/gotchas.md` Gotchas 41–44 explain what
each one does to a formula that is otherwise identical between two orgs.
