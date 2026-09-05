# Worked Examples — Sales Process Mapping

One scenario, mapped end to end, as artefacts you can copy and adapt. Everything
below is the *output of the mapping exercise* — the specification that
`admin/opportunity-management` turns into Setup changes. Nothing here is a
substitute for that skill's metadata reference.

**Scenario — Northwind Analytics.** A 180-seat B2B SaaS vendor selling an
analytics platform. Inbound-led: marketing generates MQLs, an SDR qualifies,
an AE runs the cycle with a Solution Engineer, Deal Desk prices anything
non-standard, and Legal reviews redlines above $100k ACV. Renewals are worked
by CSMs on a separate, shorter motion. One Salesforce org, Sales Cloud +
Service Cloud, Collaborative Forecasts already switched on.

---

## 1. Swim lane — persona × stage × what Salesforce actually touches

Read this left to right as the handoff chain. Every "Automation / control" cell
is a downstream build requirement, not a description of what already exists.

| Stage | Owning persona | Contributing personas | Object + key fields written | Automation / control | Handoff at exit |
|---|---|---|---|---|---|
| Inbound Qualification | SDR | Marketing Ops | `Lead` → `Opportunity` on convert; `Opportunity.LeadSource`, `Amount`, `CloseDate` | Lead assignment rule; conversion mapping | SDR → AE (Opportunity owner change) |
| Discovery | AE | SDR (context), Marketing | `Opportunity.Success_Metric__c`, `Economic_Buyer__c`, `Pain_Quantified__c` | Validation rule: exit requires `Success_Metric__c` | AE → SE (SE added to Opportunity Team) |
| Solution Validation | Solution Engineer | AE | `Opportunity.Technical_Win_Date__c`; `Product2` / `OpportunityLineItem` rows | Screen Flow to log the validation outcome | SE → AE |
| Proposal | AE | Deal Desk | `Quote` (primary), `QuoteLineItem`, `Opportunity.Amount` synced from Quote | Approval process on non-standard discount | AE → Deal Desk if discount > 15% |
| Negotiation | AE | Legal, Deal Desk, Finance | `Opportunity.Legal_Review_Status__c`, `Contract` draft | Approval process on ACV > $100k; stage-entry alert to Legal | AE → Legal |
| Closed Won | AE | Finance, CSM | `Opportunity.Win_Reason__c`, `Contract_Start_Date__c`; `Contract` activated | Record-triggered Flow: create onboarding `Case`, notify Finance | Sales → Service **and** Sales → Finance |
| Closed Lost | AE | Marketing | `Opportunity.Loss_Reason__c`, `Competitor__c`, `Nurture_Restart_Date__c` | Validation rule on close; Flow to re-enrol in nurture | Sales → Marketing |

Two handoffs deserve their own row in the handoff brief because they cross a
cloud boundary and a different team owns the failure:

- **Sales → Service at Closed Won.** The onboarding `Case` is created by
  automation, not by the AE. Decide in the workshop which fields the Case needs
  at creation (account, entitlement, promised go-live date) — see
  `admin/case-management-setup` for the Case side and
  `admin/entitlements-and-milestones` if the promised go-live is contractual.
- **Sales → Finance at Closed Won.** The `Quote` → `Contract` step is where the
  amount the forecast reported and the amount finance bills can diverge. Map
  which record is authoritative for ACV before configuring anything; see
  `admin/quote-to-cash-process`.

This is a *stage-anchored* lane view. If the engagement also needs a
step-anchored As-Is/To-Be swim lane with exception paths and automation-tier
annotations, that is `admin/process-flow-as-is-to-be` — do not rebuild it here.

---

## 2. The stage ladder as a machine-readable map

This is the artefact `scripts/check_sales_process_mapping.py --map` lints. Keep
it beside the narrative document; the narrative persuades stakeholders, the YAML
is what survives a handoff.

```yaml
process: New Logo - Enterprise
object: Opportunity
record_type: Enterprise_New_Logo
owner: VP Sales (definition authority)
stages:
  - name: Inbound Qualification
    entry: "MQL score >= 70 and the lead has been routed by the assignment rule"
    exit: "Budget, authority, need and timing confirmed on a live call; discovery booked"
    forecast_category: Pipeline
    probability: 10
    owner: SDR
    required_fields: [LeadSource, Amount, CloseDate]
  - name: Discovery
    entry: "Discovery call held with a named business owner, not only a practitioner"
    exit: "Quantified pain and one agreed success metric recorded on the opportunity"
    forecast_category: Pipeline
    probability: 20
    owner: AE
    required_fields: [Success_Metric__c, Economic_Buyer__c]
  - name: Solution Validation
    entry: "Solution Engineer assigned and a validation plan agreed with the champion"
    exit: "Technical win confirmed in writing by the champion"
    forecast_category: Best Case
    probability: 40
    owner: Solution Engineer
    required_fields: [Technical_Win_Date__c]
  - name: Proposal
    entry: "Technical win recorded and the economic buyer has agreed to see pricing"
    exit: "Quote issued and acknowledged by the buyer"
    forecast_category: Best Case
    probability: 60
    owner: AE
    required_fields: [Quote_Id__c, Amount]
  - name: Negotiation
    entry: "Buyer is negotiating commercial terms, not evaluating alternatives"
    exit: "Commercial terms agreed and legal review closed"
    forecast_category: Commit
    probability: 80
    owner: AE
    required_fields: [Legal_Review_Status__c, Close_Plan__c]
  - name: Closed Won
    entry: "Countersigned order form received"
    exit: "Onboarding case created and finance notified of the booking"
    forecast_category: Closed
    probability: 100
    owner: AE
    won: true
    closed: true
    required_fields: [Win_Reason__c, Contract_Start_Date__c]
  - name: Closed Lost
    entry: "Buyer has confirmed no purchase, or the cycle has been inactive 90 days"
    exit: "Loss reason and competitor recorded; nurture restart date set"
    forecast_category: Omitted
    probability: 0
    owner: AE
    won: false
    closed: true
    required_fields: [Loss_Reason__c, Nurture_Restart_Date__c]
```

Run it:

```bash
python3 skills/admin/sales-process-mapping/scripts/check_sales_process_mapping.py \
  --map design/new-logo-stage-map.yaml
# or lint every map plus a retrieved stage value set in one directory:
python3 skills/admin/sales-process-mapping/scripts/check_sales_process_mapping.py \
  --manifest-dir design/
```

Four things the checker is enforcing that reviewers routinely miss:

- **`entry` and `exit` on the terminal stages too.** "Closed Won" has an exit
  condition: the obligations that must be discharged before the record is left
  alone. That condition is the Sales → Service and Sales → Finance handoff, and
  a ladder that leaves it blank is the reason those handoffs get built by
  nobody.
- **Monotonic non-decreasing probability.** If a later stage is less likely to
  close than an earlier one, the stage boundary is in the wrong place. The lost
  terminal is excluded from the ladder and pinned at 0.
- **`forecast_category` in the `ForecastCategoryName` vocabulary** — `Best Case`,
  `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline`
  (object_reference.txt:195492–195504). The deployed XML uses a *different*
  token set; see §4 and `admin/opportunity-management` `references/gotchas.md`
  Gotcha 13.
- **At least one `required_fields` entry per stage.** A stage with no field
  requirement produces no validation rule and asks nothing of the rep; it is a
  label, not a gate.

The same ladder in CSV, if the workshop output lives in a spreadsheet
(`required_fields` semicolon-separated):

```
name,entry,exit,forecast_category,probability,owner,required_fields,won,closed
Renewal Outreach,Renewal date within 120 days,Renewal intent confirmed on a call,Pipeline,60,CSM,Renewal_Intent__c,false,false
Renewal Negotiation,Pricing options presented to the account,Order form issued from the quote,Commit,85,CSM,Quote_Id__c;Amount,false,false
Closed Won,Countersigned renewal order form received,Subscription end date extended and finance notified,Closed,100,CSM,Win_Reason__c,true,true
Closed Lost,Customer has confirmed churn or downgrade,Churn reason recorded and win-back date set,Omitted,0,CSM,Loss_Reason__c;Churn_Category__c,false,true
```

---

## 3. Required fields per stage, expressed as validation-rule intent

The mapping document must not ship formulas — it ships *intent* precise enough
that the formula is mechanical. One row per enforced requirement.

| # | Enforce at | Requirement | Intent (condition in words) | Error message to the rep |
|---|---|---|---|---|
| VR-01 | Entering Discovery or later | Success metric captured | Stage is at or past Discovery and `Success_Metric__c` is blank | "Record the agreed success metric before moving past Discovery." |
| VR-02 | Entering Proposal or later | A quote exists | Stage is at or past Proposal and `Quote_Id__c` is blank | "Issue a quote before moving to Proposal." |
| VR-03 | Entering Negotiation | Legal review started when ACV > $100k | Stage is Negotiation, `Amount` > 100000, `Legal_Review_Status__c` is blank | "Deals above $100k need Legal review before Negotiation." |
| VR-04 | Saving as Closed Won | Win reason and start date | Stage is Closed Won and either `Win_Reason__c` or `Contract_Start_Date__c` is blank | "Record the win reason and contract start date." |
| VR-05 | Saving as Closed Lost | Loss reason and competitor | Stage is Closed Lost and `Loss_Reason__c` is blank | "Record why this deal was lost." |
| VR-06 | Any backward move past Proposal | Manager approval | Prior stage was at or past Proposal, new stage is earlier, and the editor is not a sales manager | "Moving a deal backwards past Proposal needs manager approval." |

"Stage is at or past X" is not a comparison the platform gives you for free —
`StageName` is a picklist, not an ordinal. The handoff brief must say which
representation the implementation should use (a stage-order number held in
Custom Metadata, or an explicit `ISPICKVAL` list per rule). Decide it once, in
the mapping, or every rule will invent its own. Formula syntax and the
`PRIORVALUE` pattern for VR-06 belong to `admin/validation-rules`.

---

## 4. The record-type and sales-process decision

New logo and renewal diverge at every stage past the first, use different
owners, and need different probability norms. That is two stage sequences,
therefore two Sales Processes, therefore **two Record Types** — the platform
makes this non-optional, not a style choice:

> `RecordType.businessProcess` — "The name of the business process associated
> with the record type … **This field is required in record types for lead,
> opportunity, solution, and case, and not allowed otherwise**."
> (api_meta.txt:45007–45014)

Consequences the mapping document has to carry into the handoff brief:

| Because | The design must also budget for |
|---|---|
| A sales process is only reachable through a record type (api_meta.txt:42957–42958) | A record type per motion, with page layout and profile/permission-set assignment |
| "Only one path can be created per record type for each object, including `__Master__` record type" (api_meta.txt:94494–94496) | A second `PathAssistant` for the renewal motion — see `admin/path-and-guidance` |
| `BusinessProcess.fullName` is object-qualified for API addressing (`Opportunity.Bulk Orders`) but bare when nested in a `CustomObject` definition (api_meta.txt:42993–43007) | Two different spellings of the same process name in the same repo |
| New stage values loaded through the Metadata API "don't display in the picklist UI by default" — the record type must be edited to add them to Selected Fields (api_meta.txt:130774–130779) | A per-record-type stage availability matrix in the handoff brief, not just a stage list |

What two record types do **not** buy you, and what the mapping document must
therefore *not* promise:

> "Don't use business processes as an access control mechanism. Profile
> assignment governs create and edit access for business process but doesn't
> govern read access." (api_meta.txt:42960–42962) — and the identical warning on
> `RecordType` (api_meta.txt:44974–44980).

"The renewal team shouldn't see new-logo pipeline" is a sharing requirement, not
a record-type requirement. Route it through
`standards/decision-trees/sharing-selection.md` and record the answer in the
open-questions log before anyone configures a record type expecting it to hide
rows.

---

## 5. One deployable block: the stage value set

The ladder in §2 becomes exactly one file. Field names and the enumeration come
from the `StandardValueSet` sample and the `StandardValue` / `CustomValue` field
tables (api_meta.txt:130783–130797, 47532–47536, 47578–47614); the
`forecastCategory` + `probability` shape on stage values comes from the guide's
own opportunity `StageName` sample (api_meta.txt:44857–44880).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<StandardValueSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <sorted>false</sorted>
    <standardValue>
        <fullName>Inbound Qualification</fullName>
        <default>true</default>
        <forecastCategory>Pipeline</forecastCategory>
        <probability>10</probability>
    </standardValue>
    <standardValue>
        <fullName>Discovery</fullName>
        <default>false</default>
        <forecastCategory>Pipeline</forecastCategory>
        <probability>20</probability>
    </standardValue>
    <standardValue>
        <fullName>Solution Validation</fullName>
        <default>false</default>
        <forecastCategory>BestCase</forecastCategory>
        <probability>40</probability>
    </standardValue>
    <standardValue>
        <fullName>Proposal</fullName>
        <default>false</default>
        <forecastCategory>BestCase</forecastCategory>
        <probability>60</probability>
    </standardValue>
    <standardValue>
        <fullName>Negotiation</fullName>
        <default>false</default>
        <forecastCategory>Forecast</forecastCategory>
        <probability>80</probability>
    </standardValue>
    <standardValue>
        <fullName>Closed Won</fullName>
        <default>false</default>
        <forecastCategory>Closed</forecastCategory>
        <probability>100</probability>
        <won>true</won>
    </standardValue>
    <standardValue>
        <fullName>Closed Lost</fullName>
        <default>false</default>
        <forecastCategory>Omitted</forecastCategory>
        <probability>0</probability>
    </standardValue>
</StandardValueSet>
```

How to read it:

- **File name and location are fixed by the type**, not chosen: suffix
  `.standardValueSet`, folder `standardValueSets`, so this is
  `force-app/main/default/standardValueSets/OpportunityStage.standardValueSet-meta.xml`
  (api_meta.txt:130751–130752). `<fullName>OpportunityStage</fullName>` appears
  in the guide's sample because that sample is a standalone component; in a
  source-format project the file name carries it.
- **`<forecastCategory>` is the metadata token, not the label the map used.**
  `Commit` in §2 becomes `Forecast` here; `Best Case` becomes `BestCase`. The
  element is typed as the `ForecastCategories` enumeration with members
  `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`
  (api_meta.txt:47578–47585). `Most Likely` is a legal `ForecastCategoryName`
  but has no token here.
- **`<default>` is required on every value** (api_meta.txt:47513–47515); exactly
  one should be `true`.
- **`<won>` is the flag that exists for opportunity stages** — "associated with
  a closed or won status … only relevant for the standard `Stage` field in
  opportunities" (api_meta.txt:47611–47614). `<closed>` is documented as
  relevant to the case and task `Status` fields, up to API 36.0
  (api_meta.txt:47542–47546).
- **Order of `<standardValue>` elements is the order of the ladder**, and the
  file must contain at least one value or the deploy errors
  (api_meta.txt:130771–130772). **UNVERIFIED (2026-09-05):** the
  minimum-one-value rule is grounded, but that element order determines the
  picklist sort order is an inference — the guide does not state how deployed
  order maps to `OpportunityStage.SortOrder`, which is itself read-only
  (object_reference.txt:195552–195562, 195577). Verify with the SOQL below
  after the first deploy rather than assuming the order held.

`BusinessProcess`, `RecordType` and `PathAssistant` XML for the two motions
live in `admin/opportunity-management` `references/metadata-examples.md` §2 and
§3 — deploy the value set first, because a process can only reference stages
that already exist globally.

package.xml — `StandardValueSet` does not accept the `*` wildcard
(api_meta.txt:130826–130828), so name the member:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>OpportunityStage</members>
        <name>StandardValueSet</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# retrieve what the org has today, before proposing changes
sf project retrieve start -m "StandardValueSet:OpportunityStage" -o my-sandbox

# validate without committing
sf project deploy start -x manifest/package.xml -o my-sandbox --dry-run

sf project deploy start -x manifest/package.xml -o my-sandbox
```

Verify — the ladder is queryable, so check it rather than clicking through
Setup. `OpportunityStage` supports `query()` (object_reference.txt:195438–195439):

```sql
SELECT ApiName, MasterLabel, SortOrder, DefaultProbability,
       ForecastCategoryName, IsActive, IsClosed, IsWon
FROM OpportunityStage
ORDER BY SortOrder
```

Compare `ForecastCategoryName` in that result against the `forecast_category`
column of the §2 map — they are in the same vocabulary, which is the point of
keeping the design map in labels and the deploy file in tokens. Note the object
"is read-only via the API" (object_reference.txt:195577), so a mismatch is fixed
by editing the value set and redeploying, never by a Data Loader update.

---

## 6. Discovery workshop — the questions, and what each answer changes

Run this table in the room. The right-hand column is the point: a question whose
answer changes nothing in the artefact is a question you can drop.

| Ask the room | Why it matters in Salesforce terms | What a good answer changes in the artefact |
|---|---|---|
| "Walk me through the last deal you lost at the proposal stage — what happened first?" | Loss narratives surface the real exit gate; stated criteria are aspirational | Rewrites one `exit` line to something observable, and usually adds a `required_fields` entry |
| "Who is allowed to move a deal into Negotiation, and who actually does?" | The gap between the two is what a validation rule has to close, and the owner column drives the swim-lane handoff | Fills `owner` per stage; produces or drops VR-06 |
| "When this deal closes, who has to know, and what do they need from the record?" | The Closed Won exit condition — the Case and the Contract — is built by nobody unless it is captured as a stage requirement | Adds the Service and Finance handoff rows and the fields those consumers need |
| "Do renewals really run these same stages, or does your CSM run something else?" | Two sequences means two Sales Processes and two Record Types (api_meta.txt:45007–45014), plus a second Path (api_meta.txt:94494–94496) | Decides record type count — the single largest cost line in the handoff |
| "Is there any stage a deal legitimately goes backwards into?" | The platform allows backward movement silently; only a rule stops it | Turns a policy sentence into an explicit validation-rule row, or removes it |
| "Which team must *not* see the other team's pipeline?" | Record types and business processes do not govern read access (api_meta.txt:42960–42962, 44974–44980) | Moves the requirement out of the stage map into a sharing decision — `standards/decision-trees/sharing-selection.md` |
| "What does your board pack call each forecast bucket?" | Only `Best Case`, `Closed`, `Commit`, `Most Likely`, `Omitted`, `Pipeline` exist (object_reference.txt:195492–195504) | Produces the internal-label ↔ platform-value translation table, or exposes that the forecast design needs its own session |

---

## 7. Which artefact feeds which consumer

Nothing in this file is a deliverable on its own; each block has a named next
reader.

| Artefact (this file) | Consumed by | What it becomes |
|---|---|---|
| §1 swim lane | `agents/process-flow-mapper/AGENT.md`, `admin/process-flow-as-is-to-be` | The actor lanes and handoff points of the To-Be process map |
| §2 stage ladder YAML | `agents/sales-stage-designer/AGENT.md`, `admin/opportunity-management` | `StandardValueSet` + `BusinessProcess` values, and the forecast-category mapping |
| §3 validation-rule intent | `admin/validation-rules`, `agents/story-drafter/AGENT.md` | Validation-rule formulas, and the acceptance criteria of the stage-gate stories |
| §4 record-type decision | `admin/record-types-and-page-layouts`, `admin/record-type-strategy-at-scale` | Record type count, layout assignment, and the org-level record-type budget |
| §5 stage value set XML | `admin/picklist-and-value-sets`, `agents/path-designer/AGENT.md` | The deployed ladder, and the `picklistValueName` list every Path step binds to |
| §6 workshop questions | `admin/requirements-gathering-for-sf`, `agents/config-workbook-author/AGENT.md` | Session agenda; answers land in the workbook's process section |
| Closed Won handoff row | `admin/case-management-setup`, `admin/quote-to-cash-process` | Onboarding case creation and the Quote → Contract booking rule |

Once the ladder is live, `admin/pipeline-review-design` is what turns it into a
weekly inspection cadence — stage boundaries only pay off if someone looks at
the distribution across them.
