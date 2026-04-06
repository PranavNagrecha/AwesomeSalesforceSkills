# Gotchas — Sharing Recalculation Performance

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Apex Share Rows Are Silently Dropped With No Warning

**What happens:** When Salesforce runs a full sharing recalculation — triggered by an OWD change, a manual recalculation, or clearing Defer Sharing Calculations — all Apex managed share rows (rows with a custom `RowCause`) on the affected object are deleted before the rebuild. Salesforce does not surface any error, warning, or audit entry about these deletions. Users simply lose access.

**When it occurs:** Any full recalculation on an object that uses a custom Apex sharing reason. This includes OWD changes (even relaxing, not just tightening), clicks of the "Recalculate" button under Sharing Settings, and clearing the Defer Sharing Calculations checkbox after structural changes have been queued.

**How to avoid:** Before making any structural sharing change, check every affected object in Object Manager > [Object] > Apex Sharing Reasons. Every custom reason must have a registered `Database.Batchable` recalculation class. The class must be idempotent: delete existing rows for the reason and reinsert correct grants. Verify after recalculation that Apex share rows exist on sample records.

---

## Gotcha 2: Defer Sharing Calculations Is Org-Wide — All Admins Are Affected

**What happens:** When the Defer Sharing Calculations checkbox is enabled, all incremental sharing recalculation is suspended across the entire org. This means any structural sharing change made by any admin, deployment, or automation during the deferral window is silently queued. When deferral is cleared, all queued changes — including unexpected ones — are collapsed into the recalculation job.

**When it occurs:** During maintenance windows when multiple admins or CI/CD pipelines are active. A developer deploying a change set that includes a sharing rule modification while deferral is enabled will silently add their change to the pending recalculation queue. This can expand the scope of the job beyond what the primary admin planned.

**How to avoid:** Communicate clearly to all administrators, deployment pipelines, and integration users that a deferral window is active. Ideally, freeze all deployments and non-emergency admin changes while sharing is deferred. Review Setup Audit Trail before clearing deferral to confirm the full scope of queued changes matches expectations.

---

## Gotcha 3: OWD Tightening Cannot Be Staged or Rolled Back Mid-Job

**What happens:** Changing OWD from a more permissive to a more restrictive setting (e.g., Public Read/Write → Private) on a large object triggers a full recalculation that runs as a single atomic background job. Once the job starts, it cannot be cancelled from the UI. The only way to stop the job's effects is to reverse the OWD change — which triggers another full recalculation in the opposite direction.

**When it occurs:** Any time OWD is tightened on an object with a large record volume. Orgs often discover this mid-incident when an admin makes a "quick" OWD change during business hours and then cannot undo the hours-long background job that results.

**How to avoid:** Always plan OWD tightening during a scheduled maintenance window with adequate runway. Estimate recalculation time by checking similar past jobs in Apex Jobs history. Never tighten OWD on objects with more than 500K records during business hours, even if the change seems minor. Use Defer Sharing Calculations to batch any associated rule changes alongside the OWD edit.

---

## Gotcha 4: Criteria-Based Sharing Rules Re-Evaluate on Every Matching DML — Not Just Rule Changes

**What happens:** A criteria-based sharing rule (e.g., share records where `Status = 'Escalated'`) is re-evaluated for all records each time the criteria field is updated in bulk. If a batch job or Data Loader operation updates the `Status` field on 100,000 records, Salesforce re-evaluates the criteria-based sharing rule for all 100,000 records, even if only a few changed from or to the `Escalated` value.

**When it occurs:** Any mass DML update touching the field referenced in a criteria-based sharing rule condition. This is especially common on objects with active bulk integrations, batch cleanup jobs, or mass-status-update processes.

**How to avoid:** Avoid writing criteria-based sharing rules on fields that are frequently updated in bulk (e.g., `Status`, `Rating`, `Stage`). Prefer role- or group-based sharing rules, which only re-evaluate when role or group membership changes — an infrequent, controlled event. If criteria-based rules are required, target fields that change rarely (e.g., a custom boolean set at record creation).

---

## Gotcha 5: Nested Public Groups Multiply Recalculation Cost Non-Linearly

**What happens:** When a public group is a member of another public group (nested groups), Salesforce must traverse the full group membership graph during sharing recalculation. Adding a member to a deeply nested group forces Salesforce to evaluate that member's transitive group memberships against all sharing rules that reference any ancestor group. With 3–4 levels of nesting, the recalculation cost grows significantly compared to flat group structures.

**When it occurs:** Orgs that model organizational hierarchies using nested public groups, or that inherit group structures from legacy implementations. The cost spike often appears suddenly when a new sharing rule is added that sources from a parent group, which then multiplies the scope of recalculation for all nested members.

**How to avoid:** Keep public groups used as sharing rule sources flat — one level of nesting at most. For large-scale access management, prefer role-based sharing (which Salesforce optimizes internally) over deeply nested group structures. Audit group nesting depth before adding sharing rules that source from any group in a complex hierarchy.
