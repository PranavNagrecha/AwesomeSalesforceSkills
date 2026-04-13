# Gotchas — Analytics Security Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Salesforce OWD and Sharing Rules Have Zero Effect on CRM Analytics Dataset Rows

**What happens:** Users who are restricted from seeing certain Salesforce records (due to OWD = Private, role hierarchy, or sharing rules) see all rows in CRM Analytics datasets that contain those records. There is no automatic inheritance of Salesforce record-level security into CRM Analytics. Without an explicit security predicate or sharing inheritance configuration on the dataset, every user with dataset-level access sees every row.

**When it occurs:** Any time a CRM Analytics dataset is built from a Salesforce object that has record-level security configured (OWD, role hierarchy, sharing rules) and the implementation team assumes the Analytics layer will respect that security. This is nearly universal in first implementations — the assumption is that "we locked down the object in Salesforce, so the dashboard must be locked down too."

**How to avoid:** Treat CRM Analytics security as a completely independent layer. After building any dataset from a sensitive Salesforce object, explicitly configure a security predicate or sharing inheritance on that dataset. Verify by testing with a restricted user persona in a full sandbox.

---

## Gotcha 2: Sharing Inheritance Silently Fails Above 3,000 Rows — and Defaults to Showing All Rows

**What happens:** When sharing inheritance is enabled on a dataset, it works correctly for users whose role hierarchy grants them access to 3,000 or fewer rows in the source Salesforce object. For users whose access would span more than 3,000 rows, sharing inheritance cannot be applied. Without a backup predicate, those users see all rows in the dataset — the platform does not error, warn, or block them.

**When it occurs:** Whenever a sharing-inheritance-enabled dataset is accessed by a user high in the role hierarchy (e.g., a VP, regional director, or system administrator) whose subordinates collectively own more than 3,000 records. The failure is silent — the user simply sees data they should not see, and there is no error in any log.

**How to avoid:** Always configure a backup predicate of `'false'` alongside any sharing inheritance configuration. This ensures that users who exceed the threshold see zero rows (a visible failure that can be investigated and addressed) rather than all rows (an invisible data leakage). Design a separate predicate-based access pattern for high-volume users who need broad access.

---

## Gotcha 3: Security Predicate Column Names Are Case-Sensitive and Reference the Dataset Schema, Not the Source Object

**What happens:** A predicate such as `'ownerid' == "$User.Id"` silently returns zero rows for all users if the actual column name in the dataset is `OwnerId`. The predicate does not produce an error — it evaluates as a filter that never matches. The dashboard shows empty charts or zero-count tiles, which is indistinguishable from "user has no data" rather than "predicate is misconfigured."

**When it occurs:** When a practitioner writes a predicate using the Salesforce field API name (always lowercase in Salesforce conventions, e.g., `ownerid`) instead of the actual column name as materialized in the dataset by the dataflow or recipe. Dataflow transformation steps may rename or alter casing — the dataset schema is the authoritative source for column names.

**How to avoid:** Before writing any predicate, open Analytics Studio > the target dataset > Schema tab and copy the exact column name from there. Never assume the column name matches the Salesforce field API name. After applying a predicate, test with a user who should see data — if they see zero rows, the first check should always be column name case.

---

## Gotcha 4: Predicates Cannot Reference Other Datasets at Query Time — Cross-Dataset Security Requires Augment at Dataflow Run Time

**What happens:** A practitioner writes a predicate that attempts to filter based on data in a separate entitlement or user-mapping dataset. The predicate references a column that does not exist in the target dataset. The result is a SAQL error that prevents the dataset from being queried, or the predicate is silently ignored depending on how it is malformed.

**When it occurs:** When the access model is entitlement-based (e.g., account team membership, territory assignment, queue membership) and the entitlement data lives in a separate Salesforce object or dataset. Practitioners familiar with SQL assume a JOIN or subquery can be embedded in the predicate — this is not supported.

**How to avoid:** Embed the necessary entitlement columns into the main dataset during the dataflow or recipe run using an augment/join step. The security predicate then filters on those pre-embedded columns at query time. The entitlement dataset must be refreshed on the same cadence as entitlement data changes in Salesforce — stale entitlement data in the augmented dataset means stale security.

---

## Gotcha 5: View All Data Permission Bypasses All Predicates Unconditionally — No Predicate Can Override It

**What happens:** Users holding the `View All Data` system permission see all rows in every CRM Analytics dataset, regardless of any security predicate or sharing inheritance configuration. This bypass is unconditional and cannot be overridden at the dataset level or predicate level. Setting a predicate of `'false'` does not block a View All Data user — they still see all rows.

**When it occurs:** Salesforce administrators often hold `View All Data` for operational reasons (support, troubleshooting, data audits). When those same users are granted CRM Analytics licenses, they silently bypass all dataset predicates. Because dashboards render correctly for these users (they see data, no errors), the bypass is invisible in normal usage and will only be discovered during a security audit or when a privileged user reports seeing unexpected records.

**How to avoid:** Audit all CRM Analytics-licensed users for the `View All Data` permission before go-live and as part of periodic access reviews. Where View All Data is legitimately needed for system administration but not for analytics, consider using separate admin accounts for Salesforce operations vs. Analytics access. Document any approved View All Data exceptions explicitly in the security design.
