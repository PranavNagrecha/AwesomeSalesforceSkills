---
name: analytics-permission-and-sharing
description: "Use this skill when configuring CRM Analytics (formerly Einstein Analytics) app sharing, dataset-level permissions, row-level security predicates, sharing inheritance, or license assignment. Trigger keywords: CRM Analytics security, row-level security predicate, dataset permissions, analytics sharing inheritance, Analytics Plus license. NOT for standard Salesforce OWD/sharing rules, profile-based record access, or non-Analytics report folder sharing."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
triggers:
  - "Users in CRM Analytics can see records that belong to other users or territories"
  - "How do I restrict which rows appear in a CRM Analytics dataset based on the running user"
  - "CRM Analytics dashboard shows all data even though Salesforce sharing rules are configured"
  - "Setting up sharing inheritance for Analytics but some users still see too many rows"
  - "Analytics app sharing roles — difference between Viewer, Editor, and Manager"
tags:
  - analytics
  - crm-analytics
  - row-level-security
  - security-predicate
  - sharing-inheritance
  - dataset-security
  - license-management
  - admin
inputs:
  - "List of users or public groups that need access to the Analytics app"
  - "Salesforce objects whose record-level visibility should be mirrored in Analytics (Account, Case, Contact, Lead, Opportunity only)"
  - "Whether any user can see 3,000 or more source records (determines backup predicate requirement)"
  - "CRM Analytics license type assigned to each user (Analytics Plus or Analytics Growth)"
  - "SAQL column names from the dataset schema (required for writing predicates — they are case-sensitive)"
outputs:
  - "Configured app-level sharing with correct Viewer/Editor/Manager roles per user or group"
  - "Dataset-level security predicate (SAQL filter string) restricting row visibility to the running user"
  - "Sharing inheritance configuration with backup predicate where the 3,000-row limit applies"
  - "Validation checklist confirming all three security layers are independently configured"
  - "Documented security architecture with layer-by-layer audit trail"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-13
---

# CRM Analytics — Permission and Sharing

This skill activates when a practitioner needs to configure access control in CRM Analytics: granting app access, restricting dataset rows to the running user, wiring up sharing inheritance from Salesforce objects, or assigning and validating Analytics licenses. It produces a working three-layer security configuration and an audit checklist.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Verify license assignment first.** Without a CRM Analytics Plus or CRM Analytics Growth permission set license assigned to the user, no amount of sharing configuration will let them open the app. Check Setup > Users > Permission Set License Assignments before diagnosing any other access issue.
- **The most common wrong assumption is that Salesforce OWD and sharing rules control CRM Analytics row visibility.** They do not. CRM Analytics maintains a completely independent security layer. A user with no Salesforce record access can still see every row in a dataset unless an explicit predicate or sharing inheritance is configured on that dataset.
- **Platform constraints in play:** Sharing inheritance works only for five standard objects (Account, Case, Contact, Lead, Opportunity). When a user has access to 3,000 or more source records, sharing inheritance is blocked and a backup predicate set to `'false'` (deny-all) must be provided. Security predicates are SAQL filter strings with a hard 5,000-character limit; column names in the predicate are case-sensitive and must match the dataset schema exactly.

---

## Core Concepts

### 1. Three Independent Security Layers

CRM Analytics enforces three distinct security layers. None inherit from each other or from Salesforce object-level security:

1. **Permission Set License (access gate):** The user must hold a CRM Analytics Plus or CRM Analytics Growth permission set license. Without it, the user cannot open any Analytics asset regardless of sharing settings.
2. **App-Level Sharing (asset access):** Each CRM Analytics app has its own sharing configuration. Roles are: **Viewer** (read-only dashboards and lenses), **Editor** (can modify assets), **Manager** (can share the app and manage membership). Sharing an app does not grant row access — it only controls which assets the user can see in the UI.
3. **Dataset-Level Row Security (data visibility):** By default, every user with app access sees every row in every dataset in that app. To restrict rows, an admin must configure either a **security predicate** or **sharing inheritance** on the dataset. Both mechanisms are opt-in and must be explicitly enabled.

All three layers must be independently configured. A gap in any layer is a security defect.

### 2. Security Predicates

A security predicate is a SAQL filter string applied to a dataset. When the running user queries that dataset, CRM Analytics appends the predicate as an implicit WHERE clause. Only rows that satisfy the predicate are returned.

Key platform constraints:
- Predicates are set on the dataset, not on the dashboard or the app.
- Column names in the predicate are **case-sensitive** and must exactly match the field names in the dataset schema (not the Salesforce API name of the source field, but the column name that was created during the dataflow or recipe sync).
- Maximum predicate length is **5,000 characters**. Complex multi-branch predicates for large hierarchies can hit this limit.
- The predicate runs at query time; it does not filter the dataset during sync.
- Built-in variables like `"$User.Id"`, `"$User.Username"`, and `"$User.ProfileId"` resolve to the running user at query time.
- To allow a System Administrator to bypass the predicate, include `OR "$User.ProfileId" == "00eXXXXXXXXXXXXX"` (replace with actual profile ID) or use the `"$User.HasViewAllData"` variable.

Example — restrict Opportunity rows to the record owner:
```
'OwnerId' == "$User.Id"
```

Example — restrict rows to the user and their subordinates in the role hierarchy (requires a role-expansion dataset joined in the recipe):
```
'OwnerId' == "$User.Id" || 'RolePath' matches ".*/" + "$User.UserRoleId" + "/.*"
```

### 3. Sharing Inheritance

Sharing inheritance is an alternative to hand-writing a predicate. When enabled on a dataset, CRM Analytics queries the Salesforce sharing infrastructure at runtime to determine which source records the running user can see, and returns only the corresponding rows.

Platform constraints:
- Supported only for five objects: **Account, Case, Contact, Lead, Opportunity**.
- If the running user would have access to **3,000 or more** source records, sharing inheritance is **blocked** for that user and the system falls back to the backup predicate.
- The backup predicate **must** be set. The recommended fallback for users who breach the 3,000-record threshold is `'false'` (deny all) unless you have a business reason to allow broader access. Leaving the backup predicate empty causes those users to see all rows — the opposite of the intent.
- Sharing inheritance respects OWD, manual shares, sharing rules, and territory assignments on the source object.
- Sharing inheritance cannot be combined with a regular security predicate on the same dataset.

### 4. Dataset Permissions vs. App Sharing

App sharing and dataset-level security are perpendicular:
- A user can be a **Viewer** on an app (sees the UI) but still be blocked by a predicate (sees no data rows).
- A user who is not shared into an app cannot see any asset in that app, even if the dataset has no predicate.
- Removing a user from an app does not remove their dataset-level predicate configuration — it just blocks UI access.

---

## Common Patterns

### Pattern A: Owner-Based Row-Level Security

**When to use:** Each dataset row belongs to a single Salesforce user (OwnerId is present as a dataset column) and users should only see their own rows.

**How it works:**
1. Confirm the dataflow or recipe syncs `OwnerId` and that the column name in the dataset schema is exactly `OwnerId` (case-sensitive).
2. In Analytics Studio, open the dataset, go to Security, and set the predicate to:
   ```
   'OwnerId' == "$User.Id"
   ```
3. Test by logging in as a non-admin user and opening a lens on the dataset. Confirm the lens returns only that user's rows.
4. Optionally add a bypass clause for admins:
   ```
   'OwnerId' == "$User.Id" || "$User.HasViewAllData" == "true"
   ```

**Why not the alternative:** Sharing inheritance does not apply when the source object is not one of the five supported objects, or when no Salesforce record-level sharing exists (e.g., data loaded from external systems).

### Pattern B: Sharing Inheritance with Backup Predicate

**When to use:** The dataset is built from Account, Case, Contact, Lead, or Opportunity data and the org already has Salesforce sharing rules configured correctly for those objects. Mirroring Salesforce sharing into Analytics avoids duplicating logic.

**How it works:**
1. In Analytics Studio, open the dataset and navigate to Security.
2. Set Security Predicate Type to **Sharing Inheritance**.
3. Set the Salesforce Object field to the relevant object (e.g., `Account`).
4. Set the Backup Predicate to `'false'`. This ensures users who would see 3,000 or more records get an explicit deny rather than a data breach.
5. Save and verify by running a lens as a user with limited Salesforce account access.

**Why not the alternative:** Writing a manual predicate that mirrors OWD + sharing rules + territory assignments is extremely complex and will drift from Salesforce sharing configuration over time. Sharing inheritance delegates that logic to the platform.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Source object is Account, Case, Contact, Lead, or Opportunity and Salesforce sharing is correct | Sharing inheritance + backup predicate `'false'` | Reuses existing Salesforce sharing logic; stays in sync automatically |
| Source is not one of the five supported objects (e.g., custom object, external data) | Security predicate | Sharing inheritance unavailable; predicate is the only row-level option |
| Users need to see their own rows plus their subordinates' rows (role hierarchy) | Custom predicate with role-expansion join | Built-in `$User` variables do not traverse the role hierarchy without a join |
| All licensed users should see all rows (intentional, e.g., aggregate-only dashboards) | No predicate required; document explicitly | Default behavior is all-visible; explicit documentation prevents future audit confusion |
| User reports seeing no data at all | Check three layers in order: license → app sharing → predicate | A deny-all predicate or missing app share blocks all data regardless of license |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner configuring CRM Analytics security:

1. **Confirm license assignment.** In Setup > Users, verify each target user has the CRM Analytics Plus or CRM Analytics Growth PSL. Without this, no other step produces access.
2. **Configure app-level sharing.** In Analytics Studio, open the app, select Share, and assign Viewer/Editor/Manager roles to the appropriate users or public groups. Use public groups for scalability — avoid assigning individual users when a group exists.
3. **Inventory dataset columns.** Open the target dataset's schema and note the exact column names (case-sensitive) for fields you will reference in a predicate (e.g., `OwnerId`, `AccountId`, `RolePath`).
4. **Choose the row-level security method.** If the source object is one of the five supported objects and Salesforce sharing is already correct, use sharing inheritance with backup predicate `'false'`. Otherwise, write a security predicate in SAQL.
5. **Configure and test the predicate or sharing inheritance.** Apply the configuration in the dataset's Security panel. Immediately test by impersonating or logging in as a non-admin user and opening a lens on the dataset. Confirm rows are restricted as expected.
6. **Verify the backup predicate is set if sharing inheritance is used.** Confirm the backup predicate field is explicitly set to `'false'` (not left blank), to prevent the 3,000-row-threshold bypass from silently granting full visibility.
7. **Document the security architecture.** Record which datasets have predicates or sharing inheritance, which objects they reference, and who holds Manager role on each app. This audit trail is required for security reviews.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every target user has a CRM Analytics Plus or CRM Analytics Growth PSL assigned
- [ ] App-level sharing is set with correct roles (Viewer/Editor/Manager) for all intended users and groups
- [ ] Every dataset that contains per-user sensitive data has either a security predicate or sharing inheritance configured (no dataset is left with default all-visible access unless explicitly documented)
- [ ] If sharing inheritance is used, the backup predicate is explicitly set to `'false'`
- [ ] Predicate column names match the dataset schema exactly (case-sensitive verification done)
- [ ] Predicate SAQL length is under 5,000 characters
- [ ] Row-level security has been tested by logging in as a non-admin user and confirming the lens returns only the expected rows
- [ ] Security architecture is documented (dataset → method → object/predicate → scope)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Salesforce OWD does not control CRM Analytics row visibility** — Without an explicit predicate or sharing inheritance configuration on the dataset, every CRM Analytics licensed user sees every row. Org-wide defaults, sharing rules, and manual shares have no effect on Analytics row access until sharing inheritance is turned on for a specific dataset.
2. **Sharing inheritance silently fails for users at the 3,000-row threshold** — If a user has access to 3,000 or more source records, sharing inheritance is bypassed for that user and the backup predicate is applied instead. If the backup predicate is blank (the default), those users see all rows — the opposite of the security intent.
3. **Predicate column names are case-sensitive** — A predicate of `'ownerid' == "$User.Id"` silently returns zero rows (no error) if the dataset column is named `OwnerId`. There is no validation at save time; the failure surfaces only when a user opens a lens and sees no data.
4. **Adding a user to an app as Viewer does not grant row access** — App sharing only controls which assets appear in the app navigation. A Viewer with no predicate bypass will see all rows; a Viewer with an overly restrictive predicate will see no rows. The two layers are completely independent.
5. **Removing a user from an app share does not revoke their direct dataset access** — If the user has a direct dataset URL or a bookmark to a lens, they may still be able to query the dataset. Dataset-level predicates are the authoritative row-level control; app sharing is not a substitute.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| App sharing configuration | Named app with Viewer/Editor/Manager assignments per user or public group |
| Security predicate | SAQL filter string applied to each sensitive dataset, restricting rows to the running user |
| Sharing inheritance configuration | Dataset configured to mirror Salesforce object sharing, with backup predicate `'false'` |
| Security architecture document | Per-dataset table recording the security method, object reference, predicate text, and tested scope |
| Validation test log | Record of lens results verified as a non-admin user confirming row restriction is working |

---

## Related Skills

- crm-analytics-app-creation — Creating the Analytics app container, connecting data sources, and setting up the initial Viewer/Editor/Manager share before applying dataset-level security
- analytics-dashboard-design — Dashboard bindings and filters that display user-context values; relies on row-level security being correctly configured upstream
