# The no-matching-account fallback — `Case_BeforeSave_StampEntitlementAndCalendar`

Q48 (answered) requires "a documented fallback for cases with no matching account". This is
that document. It also covers the two adjacent cases the same flow has to survive: an account
that exists but carries no `Region__c`, and an account that carries no active `Entitlement`.

`decisions.md` **D1** states the consequence this note discharges: *"a Case whose Account has
no entitlement must fall through to a documented default rather than throw (Q48)."*

## 1. What the flow does on each shape of missing data

| Shape | `EntitlementId` | `BusinessHoursId` | `Priority` | Which element decides |
|---|---|---|---|---|
| Case has no `AccountId` (Web-to-Case with an unmatched email, API insert with no account) | left null | `US Support` | derived | `Get_Account` returns no row → `Get_Account.Region__c` is null → `Region_Unknown_Calendar_Unset` |
| Account found, `Region__c` blank | left null or stamped, per the entitlement | `US Support` | derived | `Region_Unknown_Calendar_Unset` |
| Account found, no active `Entitlement` | left null | per region | derived | `Decision_Stamp_Entitlement` default outcome `No_Active_Entitlement_Or_Case_Already_Stamped` |
| Account found, `Entitlement` exists but `Status` is not `Active` | left null | per region | derived | the `Status EqualTo Active` filter on `Get_Active_Entitlement` |
| Either `Get Records` raises at run time | left null | `US Support` (a `Get_Account` fault routes to the calendar decision) | derived | the `faultConnector` on each `recordLookups` |

**Nothing here throws and nothing here blocks the save.** There is no `customErrors` element in
this flow: a before-save create flow that rejected the Case would reject the customer's email at
intake, which is the opposite of what the intake design asks for.

## 2. Why `US Support` is the calendar fallback

Q40, answered: *"from the account's `Region__c`; unknown accounts default to US. US is the default
calendar."* `artefacts/M4-S01/settings/BusinessHours.settings-meta.xml` carries `US Support` with
`<default>true</default>`, so the choice and the org default agree.

The flow stamps it **explicitly** rather than leaving the field null. Leaving it null would work —
`skills/admin/business-hours-and-holidays/SKILL.md` ("Empty means the default calendar for every
consumer that says 'use the Case's hours'") and `references/gotchas.md` #4 both say so — but an
explicit stamp is what makes `M4-S04`'s monitoring query readable: that query treats
`BusinessHoursId IS NULL` as *"a case entry 2 measured on an unverified clock"*
(`artefacts/M4-S04/escalation-monitoring-note.md` § "Rows with a null `BusinessHoursId`"). If this
flow left the fallback implicit, every US case would look like that failure.

## 3. What the fallback costs — the consequence to accept at the M4 gate

A Case that leaves this flow with `EntitlementId` null **never enters an entitlement process and
shows no milestone**. `skills/admin/entitlements-and-milestones/references/gotchas.md` #2:
*"the entitlement process only triggers when `Case.EntitlementId` is populated at case creation."*
`artefacts/M4-S02/deploy-order.md` names this step as the only thing in the plan that populates it.

So the fallback is silent by design: the case is worked, and no first-response SLA is measured on
it. Nothing in this build reports on that population. The cheap detector, for the gate:

```sql
SELECT COUNT(Id)
FROM Case
WHERE EntitlementId = NULL AND CreatedDate = LAST_N_DAYS:7
```

A number that is not small means the account-matching half of intake, not this flow, is what needs
fixing — an unmatched Email-to-Case sender produces a Case with no `ContactId` and no `AccountId`,
and no flow can stamp an entitlement that nothing links to.

## 4. What this flow deliberately does NOT do about it

- It does not **create** an entitlement for an account that has none. A before-save flow cannot do
  DML at all (`check_record_triggered_flow_patterns.py` rule 2), and
  `entitlements-and-milestones/references/gotchas.md` #11 records that a Flow cannot write
  `Entitlement.BusinessHoursId` in any case — an `EntitlementTemplate` is how that is done, and no
  step in this plan owns one.
- It does not **log** the fallback. See `deploy-order.md` § 5: a before-save flow has no element
  that can write a log row, so the four fault paths route to the next decision rather than to the
  `LogFault_<Parent>` target `flow/flow-element-naming-conventions` Pattern 5 asks for. That is the
  one place this artefact knowingly diverges from a cited skill's convention, and it is recorded
  there rather than worked around here.
- It does not **notify** anyone. No clarification in this build names a recipient for an
  unmatched-account case; inventing one is the failure mode `D-M4S02-01` already rejected once.
