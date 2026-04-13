---
name: analytics-security-architecture
description: "Use this skill when designing or auditing CRM Analytics (formerly Einstein Analytics / Tableau CRM) data access controls: row-level security predicates, dataset-level visibility, app-level sharing roles, sharing inheritance configuration, and cross-dataset security embedding strategies. Trigger keywords: CRM Analytics security, row-level security predicate, Analytics dataset access, sharing inheritance, security predicate design, cross-dataset security, analytics entitlement dataset. NOT for standard Salesforce sharing model design (OWD, role hierarchy, sharing rules on standard objects), standard reports/dashboards folder sharing, or Tableau Server/Tableau Cloud security."
category: architect
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "How do I restrict which rows a user sees in a CRM Analytics dashboard?"
  - "My CRM Analytics dataset is showing all records to every user — how do I lock it down by role or territory?"
  - "Should I use sharing inheritance or write a custom security predicate for this CRM Analytics dataset?"
tags:
  - crm-analytics
  - security
  - row-level-security
  - architect
  - predicate
inputs:
  - "Dataset names and sources (object/field list from connected Salesforce org or external data)"
  - "User segmentation model — which users or groups should see which rows and why"
  - "Whether source Salesforce objects use role hierarchy sharing or criteria-based sharing rules"
  - "Estimated maximum row count per user in the largest dataset"
  - "Whether a user lookup or entitlement dataset is available (for cross-dataset patterns)"
outputs:
  - "Security layer design (app-level / dataset-level / row-level) with explicit decisions for each layer"
  - "Security predicate SAQL string(s) with column references verified against actual dataset schema"
  - "Sharing inheritance configuration decision with backup predicate if applicable"
  - "Cross-dataset security embedding plan (augment step design in dataflow or recipe)"
  - "Review checklist for validating security configuration before go-live"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# Analytics Security Architecture

Use this skill when designing, implementing, or auditing row-level security and dataset access controls in CRM Analytics. CRM Analytics security is entirely independent of Salesforce record-level sharing — every layer must be explicitly configured, or all licensed users will see all rows in every dataset they can access.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the datasets are sourced from Salesforce objects (SFDC Local connector) or external systems — the sharing inheritance option is only available for Salesforce-sourced datasets.
- Identify the largest expected row count a single user might "own" across the source object. If that number can ever exceed 3,000, sharing inheritance alone is insufficient and a security predicate (or backup predicate of `'false'`) is mandatory.
- Determine whether the access model is user-based (filter by `$User.Id`), role-based (filter by `$User.UserRoleId`), profile-based, or entitlement-based (filter via a joined entitlement dataset).
- Confirm whether the `View All Data` system permission is granted to any Analytics users — this permission bypasses all predicates entirely and cannot be overridden by a predicate.
- List every dataset involved in dashboards that must be secured — each dataset needs its own predicate; there is no inherited or cascading predicate across datasets.

---

## Core Concepts

CRM Analytics has three distinct, independently-configured security layers. None of them inherit from Salesforce object-level sharing automatically.

### Layer 1 — App-Level Sharing (Viewer / Editor / Manager)

The Analytics app container controls whether a user can open the app at all. Users are assigned one of three roles:

- **Viewer** — can run dashboards and explore lenses; cannot modify or create assets.
- **Editor** — can create and edit dashboards, lenses, and dataflows within the app.
- **Manager** — full administrative control over the app, including sharing settings.

App-level sharing does not restrict which rows a user sees within a dataset. A Viewer who can open the app sees the same rows as a Manager unless a dataset-level or row-level control is also applied.

### Layer 2 — Dataset-Level Access

Dataset sharing controls whether a user can query a dataset at all, regardless of what is inside it. Users and groups (roles, permission sets, public groups) are granted access to a dataset separately from the app. A user who has app access but not dataset access will see errors in any dashboard widget that queries that dataset.

Dataset-level access is configured via the dataset's sharing settings in Analytics Studio or via the `WaveDataset` metadata type. It does not filter rows — it is a coarse on/off gate.

### Layer 3 — Row-Level Security (Security Predicate)

A security predicate is a SAQL filter string stored on the dataset record. When a user queries the dataset, CRM Analytics appends this filter automatically to every query — the user cannot bypass it (unless they have the `View All Data` permission). The predicate is evaluated server-side before results are returned.

Key technical constraints on predicates (source: Salesforce Help — Add Row-Level Security with a Security Predicate):

- Maximum length: **5,000 characters**.
- Column name references are **case-sensitive** — they must exactly match the column names in the dataset schema as materialized by the dataflow or recipe, not the source field API name.
- The predicate can reference `$User.Id`, `$User.UserRoleId`, `$User.ProfileId`, and other `$User.*` attributes available in the running user context.
- The predicate can only reference columns that exist in **that specific dataset**. It cannot join to another dataset at query time.
- A predicate of `'false'` (the literal string false as a SAQL boolean) blocks all rows for all users — this is the correct safe-default for datasets where sharing inheritance is configured but could potentially be bypassed.

### Sharing Inheritance

Sharing inheritance is an alternative to hand-written predicates for Salesforce-sourced datasets. When enabled, CRM Analytics mirrors the Salesforce role hierarchy and sharing rules to determine which rows each user can see, similar to how Salesforce enforces record visibility for standard users.

Critical limit (source: Salesforce Help — Set Up Dataset Security to Control Access to Rows): sharing inheritance only operates correctly when a user's visible row count in the **source Salesforce object** is **3,000 rows or fewer**. If the row count could exceed this threshold for any user, the sharing inheritance result is unreliable and Salesforce recommends configuring a backup predicate of `'false'` to prevent data leakage. This means that for any dataset where at least one user could see more than 3,000 source rows, sharing inheritance alone is not a complete security solution.

### Cross-Dataset Security

Because predicates can only reference columns in the dataset they are applied to, securing datasets that draw from multiple sources or that require entitlement lookups requires embedding the necessary columns during dataflow or recipe execution. The design pattern is:

1. Create or maintain a **user lookup dataset** (or entitlement dataset) that maps `UserId` to the segmentation dimension (e.g., `RegionCode`, `AccountId`, `TerritoryId`).
2. Add an **augment step** in the dataflow (or a join in the recipe) that joins the main dataset rows to this user lookup dataset on the relevant key.
3. The resulting dataset now contains user-scoped columns (e.g., `Authorized_UserId`) that the predicate can reference directly.
4. Apply a predicate such as `'Authorized_UserId' == "$User.Id"` to the augmented dataset.

This pattern means that the security logic is computed at **dataflow/recipe run time**, not at query time — so the entitlement dataset must be refreshed whenever access grants change.

---

## Common Patterns

### Pattern 1 — Direct User Ownership Predicate

**When to use:** The dataset has an owner-type column (e.g., a synchronized `OwnerId` field) and users should only see records they own. This is the simplest and most common pattern.

**How it works:**

1. Ensure the dataflow or recipe includes the `OwnerId` field from the source object in the dataset output. Verify the exact column name in the Analytics Studio dataset schema view.
2. Set the security predicate on the dataset to:
   ```
   'OwnerId' == "$User.Id"
   ```
3. Test by logging in as a user who owns a known subset of records, running a lens, and confirming only their records appear.

**Why not the alternative:** Do not rely on Salesforce OWD or role hierarchy to restrict rows — CRM Analytics does not read these settings unless sharing inheritance is explicitly configured, and even then the 3,000-row limit applies.

### Pattern 2 — Sharing Inheritance with Mandatory Backup Predicate

**When to use:** The source object uses Salesforce role-hierarchy sharing and you want to mirror that model into CRM Analytics without hand-coding a predicate. The dataset is likely to stay under the 3,000-row-per-user threshold for most users but could exceed it for edge cases (e.g., an executive near the top of the hierarchy).

**How it works:**

1. On the dataset record in Analytics Studio (or via the `WaveDataset` metadata), enable **Sharing Inheritance**.
2. Set a **backup predicate** of:
   ```
   'false'
   ```
   This ensures that if sharing inheritance cannot be applied (e.g., the row count exceeds 3,000 for a given user), those users see zero rows rather than all rows.
3. Test with a user near the top of the role hierarchy to confirm the backup predicate fires when the threshold would be exceeded.

**Why not the alternative:** Enabling sharing inheritance without a backup predicate means that users who exceed the 3,000-row threshold will see all rows in the dataset — a silent data-leakage failure mode.

### Pattern 3 — Cross-Dataset Entitlement Security via Augment

**When to use:** Row access is governed by an entitlement model (e.g., account team membership, territory assignment, or a custom junction object) rather than direct ownership. The entitlement data lives in a separate Salesforce object or dataset.

**How it works:**

1. Build or refresh an **entitlement dataset** that contains one row per (UserId, EntitlementKey) pair. The EntitlementKey is the joining dimension (e.g., `AccountId`, `TerritoryId`).
2. In the main dataflow or recipe, add an augment/join step that brings the `UserId` column from the entitlement dataset into the main dataset, keyed on the shared dimension.
3. The resulting dataset has an `Authorized_UserId` column (or equivalent) for each row.
4. Apply the predicate:
   ```
   'Authorized_UserId' == "$User.Id"
   ```
5. Schedule the dataflow/recipe to re-run whenever entitlement data changes.

**Why not the alternative:** A predicate cannot reference a separate dataset at query time — it can only filter on columns already materialized in the current dataset. Attempting to embed a sub-query or reference another dataset in the predicate string will result in a SAQL error.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Simple owner-based access, rows owned directly by running user | Direct predicate: `'OwnerId' == "$User.Id"` | Minimal complexity; no augment step needed |
| Role-hierarchy sharing mirrors Salesforce model; max rows per user well below 3,000 | Sharing inheritance + backup predicate `'false'` | Mirrors existing sharing model without custom SAQL; backup predicate is mandatory |
| Role-hierarchy sharing but some users could see >3,000 rows | Hand-written role/hierarchy predicate OR sharing inheritance with `'false'` backup | Sharing inheritance unreliable above threshold; explicit predicate needed for high-volume users |
| Access governed by territory, account team, or junction object | Cross-dataset entitlement pattern via augment step | Predicate cannot join at query time; entitlement must be embedded into dataset at dataflow run time |
| Multiple datasets in same app all need same access model | Apply predicate separately to each dataset | Predicates do not cascade across datasets; each dataset is independently controlled |
| User has View All Data system permission | Predicate is bypassed — cannot be remediated by predicate design | Audit and remove View All Data from Analytics-licensed users who should not see all data |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner designing CRM Analytics row-level security:

1. **Inventory all datasets and their columns.** For each dataset that will be exposed in dashboards, open the schema view in Analytics Studio and record the exact (case-sensitive) column names that will be used in predicates. Confirm that the required filtering columns (e.g., `OwnerId`, `RegionCode`) are present in the materialized dataset, not just in the source object.

2. **Determine the access model for each dataset.** Decide whether access is owner-based, role-hierarchy-based, or entitlement-based. If entitlement-based, design the entitlement dataset schema and the augment/join step in the dataflow or recipe before writing any predicate.

3. **Assess the sharing inheritance threshold.** For any dataset being considered for sharing inheritance, estimate the maximum number of source object rows any single user could be granted access to via role hierarchy. If that number could exceed 3,000, plan a backup predicate of `'false'` and document this explicitly in the design.

4. **Write and validate each security predicate.** Draft the SAQL predicate string. Confirm column name case matches the dataset schema exactly. Keep the predicate under 5,000 characters. Apply the predicate in a sandbox environment and test with at least three user personas: a user who should see a narrow slice, a user who should see a broader slice, and a user who should see zero rows.

5. **Audit app-level and dataset-level sharing.** Confirm that app sharing roles (Viewer/Editor/Manager) are assigned to the correct users and groups. Confirm that dataset sharing grants are scoped to only the users who need access to the dataset at all — dataset-level access is a separate control from row-level access.

6. **Verify View All Data exposure.** Run a permission set and profile audit to identify any Analytics-licensed users holding the `View All Data` permission. Document the finding and escalate for remediation if any production users have this permission without business justification, because it bypasses all predicates.

7. **Document the refresh cadence for entitlement datasets.** If the security model depends on an entitlement dataset augmented into the main dataset, confirm the dataflow/recipe schedule aligns with how frequently entitlement data changes. A stale entitlement dataset means users may have access to rows they should not see, or may be denied access to rows they should see.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every dataset exposed in production dashboards has an explicit security predicate or sharing inheritance configuration — no dataset is left open to all users by default.
- [ ] Any dataset using sharing inheritance also has a backup predicate of `'false'` if any user could potentially see more than 3,000 source rows.
- [ ] All predicate column name references have been verified as case-exact matches against the live dataset schema (not the source object field API name).
- [ ] The predicate length for each dataset is under 5,000 characters.
- [ ] Cross-dataset security uses an augment step to embed user-scoped columns — no predicate attempts to reference a separate dataset at query time.
- [ ] App-level sharing roles and dataset-level grants are scoped correctly — no overly broad Viewer grants to users who should not see the dataset at all.
- [ ] A user with `View All Data` permission has been tested to confirm they bypass predicates, and this is documented and approved.
- [ ] Security has been tested end-to-end by logging in as representative user personas in a sandbox environment.

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **OWD and sharing rules do not restrict CRM Analytics rows** — Salesforce record-level security (OWD, role hierarchy, sharing rules, manual sharing) has zero effect on what rows a user sees in a CRM Analytics dataset unless sharing inheritance is explicitly enabled on that dataset. Without a predicate or sharing inheritance, every user with dataset access sees every row, regardless of how tightly the underlying object is locked down in Salesforce proper.

2. **Sharing inheritance fails silently above 3,000 rows** — If sharing inheritance is enabled but a user's role hierarchy grants them visibility to more than 3,000 rows in the source object, sharing inheritance does not apply to that user and they may see all rows instead of their intended subset. There is no UI warning or error — data leaks silently. The mandatory safeguard is a backup predicate of `'false'`.

3. **Predicate column names are case-sensitive and reference the dataset schema, not the source object** — The predicate `'ownerid' == "$User.Id"` will silently return zero rows if the actual dataset column is `OwnerId`. Column names in the materialized dataset are determined by the dataflow/recipe, not by the Salesforce object field API name. Always verify column names in the Analytics Studio schema view before writing the predicate.

4. **Predicates cannot reference other datasets at query time** — There is no equivalent of a SQL subquery or cross-dataset join in a security predicate. If the access model requires looking up entitlements from a separate dataset, those entitlement columns must be embedded into the main dataset via an augment step during the dataflow/recipe run. A predicate that attempts to reference another dataset will produce a SAQL error.

5. **View All Data bypasses all predicates unconditionally** — The system permission `View All Data` allows a user to see all rows in every dataset regardless of any predicate or sharing inheritance configuration. This cannot be overridden at the predicate level. Any CRM Analytics user with this permission effectively has unrestricted access to all data in all datasets.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Security layer design document | Explicit decisions for app-level, dataset-level, and row-level controls for each dataset in scope |
| Security predicate strings | Verified SAQL filter strings for each dataset, with column case confirmed against live schema |
| Sharing inheritance decision record | For each dataset: whether sharing inheritance is used, max estimated row count per user, and backup predicate |
| Cross-dataset augment step design | Dataflow/recipe step design for embedding entitlement columns where needed |
| Review checklist (completed) | Signed-off checklist confirming all layers tested with representative user personas |

---

## Related Skills

- crm-analytics-app-creation — Create the app container, configure app-level sharing roles, and set up the initial dataset before applying row-level security
- analytics-dashboard-design — Dashboard binding and filter design that interacts with row-level security at render time
- industries-data-model — When CRM Analytics datasets are sourced from Financial Services Cloud or Health Cloud industry objects with specialized sharing models
