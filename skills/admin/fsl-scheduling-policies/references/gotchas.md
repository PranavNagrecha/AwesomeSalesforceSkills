# Gotchas — FSL Scheduling Policies

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing Service Resource Availability Rule Silently Ignores All Absences and Working Hours

**What happens:** If a custom scheduling policy does not include the Service Resource Availability work rule, the scheduling engine treats every time slot as available for every resource, regardless of the resource's configured working hours, operating hours, and absence records. Technicians get scheduled during lunch breaks, on their days off, during approved vacation, and outside their shift windows. No error or warning is displayed anywhere in the UI or logs.

**When it occurs:** Any custom policy built from scratch or cloned from a base that had the rule removed. This is particularly common when administrators build a lightweight "test" policy and forget to add the rule, then deploy it to production.

**How to avoid:** Treat Service Resource Availability as a mandatory baseline rule in every policy. The check script in this skill's scripts directory validates for its presence. After any policy configuration change, verify the rule list explicitly — do not assume the clone retained it.

---

## Gotcha 2: Gantt Yellow Triangle Is Informational Only — Dispatch Proceeds Regardless

**What happens:** When a dispatcher manually assigns a service appointment that violates one or more work rules in the active policy, the Gantt view displays a yellow warning triangle on the appointment block. Many practitioners interpret this as a blocking validation error and believe the appointment has not been saved. The appointment is, in fact, saved and the resource is dispatched. The violation is recorded but not enforced.

**When it occurs:** Any manual drag-and-drop or direct assignment in the Dispatcher Console when the chosen slot violates a work rule (e.g., the technician lacks the required skill, or the appointment is outside operating hours). It also occurs during bulk optimization when the optimizer is configured to allow violations.

**How to avoid:** Train dispatchers that yellow triangles are warnings, not errors. If policy violations must be prevented, consider implementing a before-save Apex trigger or validation rule on ServiceAppointment to block saves where critical work rules are violated. Alternatively, audit yellow triangle rates in a custom report to identify dispatchers routinely overriding policy.

---

## Gotcha 3: Service Objective Weights Do Not Enforce a 100% Sum — Imbalanced Weights Produce Unpredictable Rankings

**What happens:** Salesforce does not validate that the percentage weights of service objectives within a policy sum to 100%. A policy can have three objectives weighted at 10%, 10%, and 10% (total 30%) and will save without error. The scheduling engine normalizes the weights internally, but the resulting behavior differs from what a practitioner intending 33%/33%/33% would expect. Similarly, weights summing to 200% are accepted.

**When it occurs:** Whenever objectives are added, removed, or reweighted without manually recalculating the total. This is especially common after an objective is removed and the remaining weights are not redistributed.

**How to avoid:** After any change to service objective weights, manually sum all active objective percentages and confirm they total 100%. Document the intended weights in a configuration record or a notes field on the policy. The check script in this skill validates objective weight totals.

---

## Gotcha 4: Work Rule Ordering Within a Policy Has No Effect

**What happens:** The list of work rules in a scheduling policy can be reordered via drag-and-drop in the UI. Practitioners familiar with firewall rules, conditional logic, or ordered filter chains expect earlier work rules to apply first. FSL applies all work rules in a policy simultaneously as a set — not sequentially. Reordering work rules changes only the display order, not the filtering logic or outcome.

**When it occurs:** When troubleshooting unexpected scheduling results, administrators often reorder rules trying to "prioritize" a specific filter. The reordering has no observable effect, leading to confusion about why the behavior did not change.

**How to avoid:** Understand that all work rules in a policy are evaluated as a single combined filter gate. To prioritize or deprioritize filtering behavior across different use cases, use separate policies — not rule ordering within a single policy.

---

## Gotcha 5: Default Policies Are Not Write-Protected — Edits Affect All Territories Using Them

**What happens:** Salesforce prevents deletion of the four default policies but does not prevent in-place edits to their work rules or objective weights. An edit to the Customer First policy immediately propagates to every service territory configured to use it as its default scheduling policy. There is no draft/publish mechanism, no change tracking in standard audit fields, and no warning that other territories are affected.

**When it occurs:** During initial setup or troubleshooting, when administrators experiment with settings on what they assume is a safe default object. It also occurs during upgrades if a sandbox refresh carries the modified default into a new environment.

**How to avoid:** Never edit default policies in place. Clone them before making any changes, name the clone descriptively, and assign territories to the clone. Treat the four defaults as read-only reference implementations. Periodically audit default policy configurations against the Salesforce documentation to detect accidental drift.
