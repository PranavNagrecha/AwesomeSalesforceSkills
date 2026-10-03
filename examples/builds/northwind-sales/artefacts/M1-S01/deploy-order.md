# Deploy order — M1-S01

Build: `northwind-sales` · Milestone: M1 (Enterprise and Renewal data model) · Step type: `object-model` · API version 62.0

This note is written by `metadata-builder` and is text for a human. Nothing here is executed by this
agent or by any acceptance test.

---

## 0. Before anything else — merge the stage value set against the org (BLOCKING)

Run this first, against the target org, and merge the result into the shipped file:

```bash
sf project retrieve start --metadata "StandardValueSet:OpportunityStage" --target-org <alias>
```

`standardValueSets/OpportunityStage.standardValueSet-meta.xml` as shipped contains **only the eight
new Northwind stages**. It is a fragment, not a complete file. Deploying it as it stands deactivates
every OpportunityStage value it does not mention — including every stage the SMB team's generic
pipeline runs on — because for a value set omission is the deactivate instruction, not "no opinion":
*"If picklist values are missing from a component definition, they get deactivated when deployed.
Deactivation occurs for picklist values of both standard and custom fields"* (api_meta.txt:47482–47483,
quoted in `skills/admin/picklist-and-value-sets/references/metadata-examples.md` §3 and
`references/gotchas.md` Gotcha 10). The file that is deployed must be the **union** of the retrieved
active values and these eight — that is decision **D1**, and assumption **A24** carries it at risk
`high` because a design-only build cannot perform the retrieve. Requirement item 6 ("nothing should
break the existing generic process for the SMB team") is decided entirely by whether this merge
happens.

Two merge rules that are easy to get wrong:

- **Keep the org's existing `<default>true</default>`.** All eight shipped stages carry
  `<default>false</default>` deliberately, so the merge does not move the org-wide default stage and
  disturb the SMB record type. Exactly one value in the merged file may be `true`
  (`skills/admin/picklist-and-value-sets/references/metadata-examples.md` §1; the checker treats two
  as an ERROR). The per-motion default lives on the business processes instead — Qualify for
  Enterprise, Renewal Review for Renewal.
- **Retire values with `<isActive>false</isActive>`, never by deleting the element.** Deletion leaves
  no trace in the diff of what was turned off (Gotcha 10, same file).

`StandardValueSet` takes no `*` wildcard, so the member is named explicitly in `package.xml`
(api_meta.txt:130826–130828).

---

## 1. Order within this step

One `sf project deploy start` resolves all four types together — the platform resolves references
inside a single deploy. The order below is what a **split** deploy must follow, and it is also the
order to fix failures in.

| # | Component | Must come after | Why |
|---|---|---|---|
| 1 | `StandardValueSet` `OpportunityStage` (merged per §0) | — | A stage must exist globally before a sales process can list it. `admin/opportunity-management/references/gotchas.md` Gotcha 6: *"the platform requires the stage to exist globally before it can be added to a process."* A partial manifest that ships the process without the values fails on the missing picklist value (`references/metadata-examples.md` §7). |
| 2 | `BusinessProcess` `Enterprise_Sales_Process`, `Renewal_Sales_Process` | 1 | Each `<values><fullName>` is a stage from step 1. A business process is a subset of the global value set (api_meta.txt:42956–42958). |
| 3 | `RecordType` `Enterprise`, `Renewal` | 2 | `<businessProcess>` on each record type resolves to the process name from step 2. A record type naming a process the org does not yet hold fails on the cross-reference, not on the pairing rule — which sends you hunting in the wrong place (`admin/record-types-and-page-layouts/references/gotchas.md` #6). |
| 4 | `CustomField` `Discount__c`, `Approval_Status__c` | — (independent of 1–3) | No dependency either way inside this step. Ordered last here only because the data-model-then-everything-else sequence in `admin/change-management-and-deployment/references/llm-anti-patterns.md` Anti-Pattern 4 puts objects and fields first and everything that references them after. |

**Two spellings of the same process name, in the same repo.** Inside the object definition the
`<businessProcess>` element carries the **bare** name (`Enterprise_Sales_Process`). In `package.xml`
the member is **object-qualified** (`Opportunity.Enterprise_Sales_Process`). Both forms are in this
step's artefacts on purpose; a mismatch between them is the most common
`INVALID_CROSS_REFERENCE_KEY` in this package (api_meta.txt:42993–43008).

---

## 2. Dependencies on components outside this step

| Outside component | Step | Direction |
|---|---|---|
| The two Opportunity page layouts | **M1-S02** | Deploy **after** this step. A layout assignment resolves a record type; the record types are built here. The M1 milestone checker (`check_record_type_layouts.py --manifest-dir artefacts`) only asserts the link once both step directories exist. |
| `Profile` layout assignments and `recordTypeVisibilities` (`<default>`) | **M2-S02** (human-gated) | Deploy **after** M1-S02. A permission set can grant record-type *visibility* only; the default record type and the page layout assignment exist solely on `Profile` (`admin/record-types-and-page-layouts/references/metadata-examples.md`, "Making the record type visible and assigning the page"). Until that ships, **these two record types are deployed but nobody can select them.** |
| The `PathAssistant` for each motion | **M1-S02 / M2-S05** | Deploy **after** the record types. `recordTypeName` on a Path is not updateable, and only one Path may exist per record type per object (api_meta.txt:94496, 94513–94530). |
| Validation rules referencing `Discount__c` / `Approval_Status__c` | **M2-S03 / M2-S04** | Deploy **after** the two fields. |
| The discount approval process (sets `Approval_Status__c`) | **M3** | Deploy **after** the field. The field ships with no default value because blank is a legal state until a rep submits (Q22). |

---

## 3. Manual steps no deploy performs

1. **Add the new stages to every record type's Selected Fields.** A green deploy is not evidence
   anyone can pick the value: *"new picklist values loaded into your organization through the
   Metadata API don't display in the picklist UI by default. For users to see the new values, go to
   the Record Types list for the object containing the picklist field, click Edit, and add the new
   value to the Selected Fields list"* (api_meta.txt:130774–130779). Brand-new record types receive
   all current master values by default (`admin/picklist-and-value-sets/references/gotchas.md`
   Gotcha 5), so Enterprise and Renewal should be correct on arrival **if** the value set deployed
   first — verify it by opening a record of each type rather than by reading the deploy log
   (`admin/sales-process-mapping/references/gotchas.md` Gotcha 7). Named owner required.
2. **Reassign the ~140 open Enterprise deals** from the generic record type to `Enterprise`, as a
   one-time post-go-live data update (Q8). Q8 records no field mapping change; reassignment blanks
   any picklist value absent from the target record type, so re-run the at-risk query in
   `admin/record-types-and-page-layouts/references/gotchas.md` #1 before the update, not after.
3. **Confirm Opportunity field history tracking is actually on.** Assumption **A4** relies on the
   platform default (`OpportunitySettings.enableOpportunityFieldHistoryTracking` defaults to `true`,
   api_meta.txt:123321–123323); no settings file ships in this build. History cannot be backfilled,
   so check it before go-live, not after (Q39, unanswered).

---

## 4. Verify after deploy

```sql
SELECT ApiName, MasterLabel, SortOrder, DefaultProbability,
       ForecastCategoryName, IsActive, IsClosed, IsWon
FROM OpportunityStage
ORDER BY SortOrder
```

`OpportunityStage` is read-only through the API (object_reference.txt:195577), so a mismatch is fixed
by editing the value set and redeploying, never by a data update. Expect
`ForecastCategoryName` = **Commit** on Negotiate and Renewal Proposed: the SOQL/UI label for the
metadata token `Forecast`. The word `Commit` appears nowhere in the deployed XML and must not — the
`ForecastCategories` enum is exactly `Omitted`, `Pipeline`, `BestCase`, `Forecast`, `Closed`
(api_meta.txt:47578–47586; `admin/opportunity-management/references/gotchas.md` Gotcha 13).

```sql
SELECT SobjectType, DeveloperName, Name, IsActive, BusinessProcessId
FROM RecordType
WHERE SobjectType = 'Opportunity'
ORDER BY DeveloperName
```

---

## 5. Validate-only command for the human

Run this yourself once §0's merge is done. **This agent does not run it, and no acceptance test
invokes it.**

```bash
sf project deploy start \
  --manifest .sfskills/builds/northwind-sales/artefacts/M1-S01/package.xml \
  --target-org <alias> \
  --dry-run
```

---

## 6. Repair after run 1 (2026-09-18)

`reports/MOCK-DEPLOY-M1.md` run 1 (`mode manifest`, milestone M1) returned **N3-F-01 (HIGH)** on both
`BusinessProcess` components: *"Cannot specify a default on: Opportunity"*. Both processes shipped
`<default>true</default>` on their opening stage — Qualify for `Enterprise_Sales_Process`, Renewal
Review for `Renewal_Sales_Process`.

**Deviation from decision D1.** D1 (this note's §0 and the M1-S01 decision record, run 1) put the
per-motion default on the `BusinessProcess`, reasoning that the org's existing global default on
`StandardValueSet` `OpportunityStage` must not move (requirement item 6, the SMB process must not
break) and that the per-motion default could live on the process instead. `admin/opportunity-management`
metadata-examples § 2 was read as authority for that shape — its "New Business" sales-process sample
carries `<default>true</default>` on `Prospecting`. The org rejects that shape for Opportunity outright:
a `BusinessProcess` on this object may not carry `<default>true</default>` on any value. **§ 2's example
is contradicted by the org and is filed for the library** — it is a real deploy-time failure this build
surfaced, not a misreading of the example, and the skill needs either a gotcha or a per-object caveat
before another build copies it onto Opportunity again.

**Fix applied.** `<default>true</default>` is removed from the opening-stage `<values>` block in both
files — `Qualify` in `Enterprise_Sales_Process.businessProcess-meta.xml`, `Renewal Review` in
`Renewal_Sales_Process.businessProcess-meta.xml`. Nothing else in either file changed: the five
remaining `<values>` blocks in each process keep their `<default>false</default>` exactly as shipped in
run 1, since the org's rejection is on the finding's own evidence a rejection of *specifying a default*
(`<default>true</default>`) on this object's process, not of the `<default>` element as such, and the
scope for this repair is the opening stage only.

**Where the default stage now comes from.** `UNVERIFIED (2026-09-18):` none of this step's cited skills
(`admin/picklist-and-value-sets`, `admin/opportunity-management`, `admin/record-types-and-page-layouts`,
`admin/object-creation-and-design`, `admin/sales-process-mapping`) document a per-`BusinessProcess` or
per-`RecordType` default-stage override for Opportunity. The only `<default>` mechanism these skills
document for `OpportunityStage` at all is the global `StandardValueSet`'s own element — "`<default>` is
required on every value … exactly one should be true" (`admin/sales-process-mapping`
references/worked-examples.md § 5) — which is the same element § 0 above already preserves at the org's
existing value during the retrieve-and-merge. Two things follow from that gap rather than from a stated
platform rule:
- The likely mechanism is that a new Enterprise or Renewal Opportunity's Stage field takes whatever
  stage carries `<default>true</default>` on the global value set, with no per-process override — but no
  cited skill states this for Opportunity specifically (`admin/opportunity-management` §2's "How to read
  it" describes the element's shape, not what happens when a process sets none), so it is recorded here
  as an inference, not a grounded claim.
- If the org's existing global default is not one of the eight stages this step ships, or not a member
  of the Enterprise or Renewal stage subset, which stage a new record opens on is unresolved by
  anything in this step's skills[]. Confirm with the § 4 verification SOQL after deploy — check
  `OpportunityStage.IsActive`/default membership against each process's subset — rather than assuming
  Qualify or Renewal Review will show as selected by default in the UI.

Re-run declared checkers on the two edited files: **clean** (see the M1-S01 envelope for this run,
`envelopes/M1-S01/<run_id>.md`, § 5). `check-outputs` still reports all nine declared outputs present.
No other file in this step's nine outputs changed.

`--dry-run` validates without saving to the org. Use `sf project deploy validate` instead only
against a **production** org: it requires Apex tests and returns a job ID for a later
`sf project deploy quick`.
