# Gotchas — Service Metrics Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: IsViolated = true Does Not Mean the Milestone Is Still Open

**What happens:** A `CaseMilestone` record with `IsViolated = true` and `IsCompleted = true` (and a non-null `CompletionDate`) represents a late completion — the milestone was finished, but after the `TargetDate`. `IsViolated` is set to `true` when the `TargetDate` passes without completion, and it stays `true` permanently even after a belated completion. It is never reset to `false`.

**When it occurs:** Any time a case milestone is completed after its `TargetDate` — for example, a First Response milestone met 2 hours late, or a Resolution milestone closed the next business day past the SLA deadline. Both `IsCompleted = true` AND `IsViolated = true` are simultaneously true on the same record.

**How to avoid:** Never use `IsViolated = true` as a filter meaning "still open and unresolved." Use the full four-quadrant state model:
- Compliant: `IsCompleted = true AND IsViolated = false`
- Late completion (SLA miss): `IsCompleted = true AND IsViolated = true`
- Open/overdue: `IsCompleted = false AND IsViolated = true`
- Open/on-track: `IsCompleted = false AND IsViolated = false`

---

## Gotcha 2: No Native MTTR Field — ElapsedTimeInMins Is Milestone-Scoped, Not Case-Scoped

**What happens:** Practitioners assume `ElapsedTimeInMins` on `CaseMilestone` is the equivalent of MTTR for the overall case. It is not. `ElapsedTimeInMins` measures the business-hours duration from `StartDate` to `CompletionDate` for that specific milestone only (e.g., how long it took to achieve First Response). A case with a 30-minute First Response milestone followed by a 2-day Resolution milestone has separate `ElapsedTimeInMins` values per milestone — neither represents the full case lifecycle from creation to close.

**When it occurs:** When building "average time to resolve" reports using `CaseMilestone.ElapsedTimeInMins` instead of a Case-level MTTR field. Reports using AVG(ElapsedTimeInMins) grouped by milestone type will show correct per-milestone averages but cannot produce end-to-end case resolution time.

**How to avoid:** Derive MTTR at the Case level. For calendar MTTR: formula field `IF(IsClosed, (ClosedDate - CreatedDate) * 24 * 60, NULL)`. For business-hours MTTR: Apex trigger using `BusinessHours.diff(bhId, CreatedDate, ClosedDate)` stored in a custom field. Report on the Case-level field for MTTR.

---

## Gotcha 3: Expired or Future-Dated Entitlements Silently Suppress Milestone Creation

**What happens:** If a Case is created with an `EntitlementId` pointing to an Entitlement whose `EndDate` is in the past (expired), or whose `StartDate` is in the future, no `CaseMilestone` records are created for that case. The `EntitlementId` is populated and looks correct in the UI, but no SLA clock is running. The case appears to have SLA coverage but produces zero CaseMilestone records.

**When it occurs:** After an annual contract renewal, if the old Entitlement record is used instead of the new one; or when demo/test cases use expired entitlements. Also occurs if entitlement status is set to "Inactive" after case creation — existing open milestones continue, but no new milestones fire.

**How to avoid:** Validate that the Entitlement linked to a case is Active and within its `StartDate`–`EndDate` range at the time of case creation. Add a Validation Rule or Flow check on Case creation that warns when `EntitlementId` references an expired Entitlement. Include a data quality check: cases with `EntitlementId` populated but zero associated `CaseMilestone` records indicate a gap in SLA coverage.

---

## Gotcha 4: BusinessHours.diff() Uses the ID You Pass — Not the Entitlement's Business Hours Automatically

**What happens:** When writing an Apex trigger to compute business-hours MTTR, developers often query the org's default Business Hours (`IsDefault = true`) rather than the Business Hours assigned to the case's Entitlement. Cases on premium SLA tiers may use extended Business Hours (e.g., 24/7 or extended weekday coverage). Using the wrong Business Hours ID understates or overstates MTTR.

**When it occurs:** Any org with multiple Business Hours records where different Entitlement tiers have different coverage schedules. A developer hardcodes the default Business Hours ID in the MTTR trigger. Cases on extended-hours entitlements get MTTR computed against standard hours — the metric is wrong and cannot be used for SLA reporting.

**How to avoid:** Retrieve the Business Hours ID from the Entitlement linked to the case: `Case.Entitlement.BusinessHoursId`. Fall back to the org default only if `BusinessHoursId` is null on the Entitlement. Pass the correct ID to `BusinessHours.diff()`.

---

## Gotcha 5: CaseMilestone.TargetDate Is Immutable After Creation

**What happens:** Once a `CaseMilestone` record is created, its `TargetDate` is set by the Entitlement Process configuration and cannot be changed via DML or Process Builder. If business requirements change (e.g., a VIP customer gets a manually extended deadline), the `TargetDate` cannot be overridden without deleting and recreating the milestone. Attempts to update `TargetDate` via Apex fail with a field-level security or read-only field error.

**When it occurs:** Support managers trying to grant extensions on SLA deadlines for individual cases; admins trying to retroactively adjust milestone deadlines after an Entitlement Process configuration change.

**How to avoid:** Design escalation workflows that act before `TargetDate` rather than modifying it. For genuine extensions, document the business process: close the existing milestone manually (set `CompletionDate`) and create a new milestone type (e.g., "Extended Resolution") with a separate timer. Never build automation that tries to update `TargetDate` via DML — it will fail silently or throw an error depending on the context.
