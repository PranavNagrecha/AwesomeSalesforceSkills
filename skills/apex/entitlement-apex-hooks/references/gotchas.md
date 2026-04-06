# Gotchas — Entitlement Apex Hooks

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: CaseMilestone.IsCompleted Is Read-Only — Writes Are Silently Discarded

**What happens:** Writing `caseMilestone.IsCompleted = true` in Apex and calling `update` produces no DML exception. The save operation appears to succeed. However, when you query the record immediately after, `IsCompleted` is still `false` and the milestone remains open. The field value is silently discarded by the platform.

**When it occurs:** Any time a developer tries to complete a milestone by directly setting the boolean flag, which is the intuitive approach for anyone familiar with standard Salesforce boolean checkbox fields.

**How to avoid:** Write `caseMilestone.CompletionDate = System.now()` instead. `CompletionDate` is the actual writable field that controls milestone completion. Once it is non-null, the platform's formula field `IsCompleted` evaluates to `true` automatically. Never write `IsCompleted` directly.

---

## Gotcha 2: SlaExitDate Cannot Be Written by Apex

**What happens:** Attempting to set `CaseMilestone.SlaExitDate` in a DML update call produces no error but the field is not persisted. The platform recalculates and overwrites any value you set, because `SlaExitDate` is managed entirely by the entitlement process engine based on business hours and the entitlement process definition.

**When it occurs:** When a requirement asks for dynamically adjusting milestone deadlines based on case priority, customer tier, or other runtime conditions. Developers attempt to read `SlaExitDate`, add or subtract time, and write it back.

**How to avoid:** Milestone deadline adjustment is not supported through Apex. If variable deadlines are required, design different entitlement processes (e.g., Platinum, Gold, Standard) with different time triggers, and apply the appropriate process based on case or account attributes. Dynamic deadline manipulation is a design smell that indicates the entitlement process model should be revisited.

---

## Gotcha 3: No Trigger Fires When IsViolated Becomes True

**What happens:** Developers write an `after update` trigger on `CaseMilestone` expecting it to fire when `IsViolated` transitions from `false` to `true`. The trigger is never invoked for violation state transitions because the platform sets `IsViolated` through a background calculation process, not through a DML operation that would cause a trigger to execute.

**When it occurs:** When building real-time violation alerting or escalation using a reactive trigger pattern. The trigger on `CaseMilestone` may fire for other DML operations (e.g., when `CompletionDate` is written), but it will not fire at the moment of violation.

**How to avoid:** Use Scheduled Apex to poll `CaseMilestone WHERE IsViolated = true AND CompletionDate = null` at a regular interval. For simple notifications (emails, field updates), use the native Milestone Actions in the entitlement process configuration, which do fire on violation without requiring Apex.

---

## Gotcha 4: CaseMilestone Records Require an Active Entitlement Process on the Case

**What happens:** In developer orgs, scratch orgs, or sandboxes where no entitlement process is configured and applied to cases, `CaseMilestone` records are never created. Trigger code runs against empty query results. Tests that rely on querying `CaseMilestone` return empty lists and pass vacuously, giving false confidence.

**When it occurs:** During development in a fresh org or a sandbox that has not had entitlement data refreshed or manually configured. Also occurs in unit tests that do not create the full entitlement process hierarchy in `@testSetup`.

**How to avoid:** In test classes, create the full hierarchy: `EntitlementProcess` > `MilestoneType` > `EntitlementProcessMilestone` > `Entitlement` > associate with Account > apply to Case. The Entitlements Implementation Guide includes the required test data structure. Without this, no `CaseMilestone` records exist and tests prove nothing.

---

## Gotcha 5: MilestoneType.Name Is Case-Sensitive in SOQL

**What happens:** A SOQL query with `MilestoneType.Name = 'first response'` returns zero records even though a milestone type named `'First Response'` exists and is active on the case. SOQL string comparison for this relationship field is case-sensitive, unlike most standard SOQL text field comparisons.

**When it occurs:** When a developer types the milestone type name by hand without checking the exact casing in Setup, or when the milestone type name is changed in Setup after the Apex code is already written.

**How to avoid:** Use the exact name from Setup > Entitlement > Milestone Types. Store milestone type names as named constants in a top-level class or custom metadata to avoid repeated string literals and make case changes easier to propagate. Consider querying `MilestoneType` by name first and storing the Id if performance and robustness are priorities.
