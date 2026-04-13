# Gotchas — Analytics Permission and Sharing

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Salesforce OWD and Sharing Rules Have No Effect on CRM Analytics Row Visibility

**What happens:** An admin configures Salesforce OWD as "Private" on Opportunity and adds sharing rules so that reps only see their own records in Lightning. They assume this carries through to CRM Analytics. It does not. Every CRM Analytics licensed user sees every row in every dataset unless a security predicate or sharing inheritance is explicitly configured on that dataset.

**When it occurs:** Any time a new dataset is created via a dataflow, recipe, or direct data connector without a subsequent security predicate being applied. The dataset is all-visible by default with no warning in the UI.

**How to avoid:** After every dataset creation, immediately check the Security tab and confirm whether a predicate or sharing inheritance is intentionally absent. If absent without justification, treat it as a security defect. Add the security review to the dataset creation checklist (see the Review Checklist in SKILL.md).

---

## Gotcha 2: Sharing Inheritance Silently Falls Back to the Backup Predicate at 3,000 Source Records

**What happens:** Sharing inheritance is enabled on a dataset and the backup predicate is left blank (the default). For users who have access to fewer than 3,000 source records, sharing inheritance works correctly. For users who have access to 3,000 or more records, sharing inheritance is bypassed and the backup predicate is applied instead. A blank backup predicate defaults to all-visible, meaning high-volume users see every row in the dataset — the opposite of the intended restriction.

**When it occurs:** Typically affects managers, executives, or territory owners who have broad Salesforce record access. Sharing inheritance is bypassed silently; no error is shown and no log entry is generated. The affected users simply see more data than they should.

**How to avoid:** Always set the backup predicate to `'false'` when enabling sharing inheritance. This produces a deny-all for users who breach the threshold. If those users legitimately need broad Analytics access, grant them the View All Data permission on their permission set rather than relying on a permissive backup predicate. The `'false'` value is a literal SAQL expression that evaluates to false for all rows.

---

## Gotcha 3: Security Predicate Column Names Are Case-Sensitive and Must Match the Dataset Schema Exactly

**What happens:** An admin writes a predicate referencing `'ownerid'` (lowercase) when the dataset column is named `OwnerId`. The predicate saves without error but returns zero rows for all users. The dashboard renders empty, which is indistinguishable from a correct deny predicate.

**When it occurs:** Especially common when column names are typed from memory using the Salesforce API field name rather than inspected from the dataset schema. Also occurs when a recipe renames a column during transformation (e.g., joining two objects and aliasing a field), and the predicate author uses the source field name instead of the alias.

**How to avoid:** Before writing any predicate, open the dataset schema viewer in Analytics Studio and copy the exact column name from the schema. Treat column names as opaque strings and never assume they match the Salesforce API field name. After saving a predicate, immediately test by opening a lens as a non-admin user and confirming rows are returned (not silently empty).

---

## Gotcha 4: App-Level Sharing Does Not Restrict Dataset Row Access

**What happens:** An admin shares an app with a user as Viewer and believes this is sufficient to control data visibility. The user opens a lens, gets the URL, bookmarks it, and later accesses it directly — even after being removed from the app share. Or, a user who is a Viewer on the app queries the dataset via the CRM Analytics REST API and retrieves all rows because no predicate exists.

**When it occurs:** Any time the security model relies on app sharing as the row-level control rather than as the UI access control it actually is. Removing a user from an app share blocks the Analytics Studio UI, but the dataset remains directly queryable if the user knows the dataset ID.

**How to avoid:** Use dataset-level security predicates as the authoritative row-level control. App sharing is only the first layer (which assets are visible in the UI). For sensitive datasets, always configure a predicate regardless of app sharing state.

---

## Gotcha 5: The 5,000-Character Predicate Limit Has No UI Warning

**What happens:** An admin builds a complex role-hierarchy predicate that includes many OR branches for individual user IDs or role IDs. Once the predicate text exceeds 5,000 characters, CRM Analytics silently truncates or rejects it at save time (behavior varies by API version). Truncated predicates grant incorrect access — typically more access than intended because the trailing deny conditions are cut off.

**When it occurs:** Common in orgs with deep role hierarchies or when building predicates that enumerate explicit user or role IDs instead of using join-based approaches (role-expansion datasets joined in a recipe).

**How to avoid:** Keep predicates short and data-driven. Instead of enumerating role IDs in the predicate string, pre-compute role hierarchy membership in a recipe join and reference a single dataset column in the predicate (e.g., `'RolePath' matches ".*/" + "$User.UserRoleId" + "/.*"`). Monitor predicate length programmatically using the checker script. If the predicate is approaching the limit, refactor using a role-expansion or user-mapping dataset.
