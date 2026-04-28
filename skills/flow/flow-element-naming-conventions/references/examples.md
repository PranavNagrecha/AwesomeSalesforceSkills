## Examples — Flow Element Naming Conventions

Concrete BAD vs GOOD examples for the canonical naming patterns. Use these
side-by-side tables when auditing or refactoring an existing Flow.

---

## Example 1: Element API Names — BAD vs GOOD

| Element type | BAD (Salesforce default / weak) | GOOD (canonical) | Why |
|---|---|---|---|
| Get Records | `Get_Records_1` | `Get_OpenCasesByOwner` | Self-describing in fault emails |
| Get Records | `Lookup_Acct` | `Get_AccountById` | Verb matches element type, noun is full word |
| Update Records | `Update_2` | `Update_OpportunityStageToClosedWon` | Encodes the post-condition |
| Update Records | `UpdAcct` | `Update_AccountTier` | No abbreviations; reads in a diff |
| Create Records | `myCreate_1` | `Create_ChildAccount` | No `my` prefix; clear intent |
| Delete Records | `Del_Old` | `Delete_StaleTasks_OlderThan90Days` | Qualifier explains the scope |
| Decision | `Decision_3` | `Decision_HasActiveContract` | Yes/no question framing on the noun |
| Loop | `Loop_1` | `Loop_OverContacts` | Iteration target is explicit |
| Assignment | `Assignment_1` | `Assignment_AccumulateTaskList` | Verb (Accumulate) + target collection |
| Screen | `Screen_2` | `Screen_CollectShippingAddress` | Purpose of the screen, not its index |
| Action (Apex) | `myAction` | `Action_SendDocuSignEnvelope` | Reads as a remote call |
| Subflow call | `Subflow_1` | `Subflow_Account_RollupChildContactsCount` | Mirrors the called Flow's API name |
| Fault target | `LogError` | `LogFault_Update_OpportunityStageToClosedWon` | Routes the fault email to the right element |

---

## Example 2: Resource Variable Names — BAD vs GOOD

| Resource type | BAD | GOOD | Why |
|---|---|---|---|
| Variable (single record ID) | `accountId` | `varAccountId` | Type prefix; safe to read in formulas |
| Variable (string form) | `accountIdStr` | `varAccountIdString` | Explicit shape in the suffix |
| Collection variable | `cases` | `collOpenCases` | `coll` prefix signals List shape |
| Collection variable | `Contacts` | `collContactsToInsert` | Capitalization is consistent; intent is encoded |
| Map / Apex-defined map | `accts` | `mapAccountById` | Map shape + the key field |
| Formula | `fullName` | `formulaFullName` | Distinguishes formula from variable in mixed-resource flows |
| Constant | `MAX_RETRIES` | `constantMaxRetries` | Removes ambiguity with Apex-style globals |
| Choice | `taskType` | `choiceTaskType` | Distinguishes Choice resource from a regular variable |
| Stage (orchestration) | `S1` | `Stage_LegalReview` | Business-readable; appears in stage tracker |
| Step (orchestration) | `Step2` | `Step_LegalReview_AssignToCounsel` | Stage prefix + action verb |

---

## Example 3: Decision Branch Outcome Names — BAD vs GOOD

```
BAD                                         GOOD
Decision_3                                  Decision_HasActiveContract
  ├── Yes                                     ├── HasActiveContract           (rule: Account.Active_Contract__c = TRUE)
  └── (default, no name)                      └── NoActiveContract_Default    (default outcome — no rule)

Decision_2                                  Decision_AccountSize
  ├── Yes                                     ├── IsEnterprise                (rule: AnnualRevenue >= 500_000_000)
  ├── No                                      ├── IsMidMarket                 (rule: AnnualRevenue >= 50_000_000)
  └── (blank)                                 └── IsSMB_Default               (default outcome)

Decision_1                                  Decision_RouteByRegion
  ├── Match1                                  ├── Region_NA
  ├── Match2                                  ├── Region_EMEA
  ├── Match3                                  ├── Region_APAC
  └── Default                                 └── Region_Other_Default
```

Rule of thumb: the Default outcome **always** gets an explicit name. `Default`
on its own is acceptable but `<NegativeCondition>_Default` is better because
the next reader does not have to inspect the other outcomes to figure out what
the default catches.

---

## Example 4: Subflow Input/Output Naming

A `Account_RollupChildContactsCount` subflow exposes a clean public contract:

```
Subflow:  Account_RollupChildContactsCount
  Description (in Flow Description field):
    Inputs:
      - inputAccountId           (Text, required)        — Account whose children to roll up
      - inputContactStatusFilter (Text, default 'Active') — Filter on Contact Status__c
    Outputs:
      - outputContactCount       (Number) — count of matching child contacts
      - outputLastContactDate    (DateTime) — most recent CreatedDate among matches

  Variables (API Name | Type | Available for input | Available for output):
    inputAccountId            | Text     | Yes | No
    inputContactStatusFilter  | Text     | Yes | No
    outputContactCount        | Number   | No  | Yes
    outputLastContactDate     | DateTime | No  | Yes
    varCollMatchingContacts   | Contact[]| No  | No   (internal)
    varRollupCount            | Number   | No  | No   (internal)
```

The `input` / `output` prefix communicates direction at the call site without
having to flip back to the subflow's variable list.

---

## Anti-Pattern: Renaming a Subflow Input Without Bumping Version

**What practitioners do:** open the subflow `Account_RollupChildContactsCount`,
rename `inputAccountId` to `inputAcctId` "for brevity", save the active version.

**What goes wrong:** the rename saves cleanly. Every parent flow that
previously called this subflow with `inputAccountId = {!varAccountId}` now
fails at the next interview with `The flow couldn't find a referenced
variable inputAccountId.` There is no save-time warning, and there is no
global "find references" tool for Flow variables.

**Correct approach:** treat Subflow inputs/outputs as a published API.

1. If the rename is necessary, create a **new flow version** per `flow-versioning-strategy`.
2. Keep the old input variable in the new version (deprecated, mapped to the new variable internally) for at least one release cycle.
3. Update every parent flow's Subflow element to use the new input name.
4. Activate the new version. Retire the old version only after all parents are updated.

---

## Anti-Pattern: Process-Builder Migration Names Left Untouched

**What practitioners do:** convert a Process Builder to a Flow using the
auto-converter, deploy the result with names like `myWaitEvent_4`,
`myDecision_2`, `myRule_1_A1` intact.

**What goes wrong:** the resulting flow is a maintainability disaster.
Fault emails reference `myDecision_2`, formula references inside the flow
read `{!myRule_1_A1.outcome}`, and the next developer has to open Flow
Builder to figure out what each element does. The migration "succeeded"
but technical debt is now baked in.

**Correct approach:** treat the migration's auto-generated names as a
**rename pass to-do list**. Use this skill's Decision Guidance table to
rename every `my<Type>_<n>` element before deploying. See
`process-builder-to-flow-migration` for the broader migration workflow.
