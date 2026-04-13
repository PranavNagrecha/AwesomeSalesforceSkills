# Examples — Analytics Permission and Sharing

## Example 1: Restricting Opportunity Rows to the Record Owner

**Context:** A Sales Operations team has built a CRM Analytics dashboard showing Opportunity pipeline. The org has 250 sales reps. Each rep should see only their own opportunities. Salesforce OWD for Opportunity is "Private," but the team reports that reps can see all opportunities in the Analytics dashboard.

**Problem:** The Opportunity dataset was synced with a dataflow and no security predicate was configured. In CRM Analytics, the absence of a predicate means every licensed user sees every row — regardless of Salesforce OWD settings. The "Private" OWD controls record access in Salesforce Lightning UI and SOQL-based tools, but it has no effect on CRM Analytics dataset queries.

**Solution:**

1. Open Analytics Studio, navigate to the Opportunity dataset, and open the Security tab.
2. Confirm the dataset schema includes a column named exactly `OwnerId` (view the dataset schema to verify the case).
3. Set the security predicate to:

```
'OwnerId' == "$User.Id"
```

4. To allow administrators to see all rows without logging in as individual users, extend the predicate:

```
'OwnerId' == "$User.Id" || "$User.HasViewAllData" == "true"
```

5. Save the predicate. Test by logging in as a non-admin rep and opening a lens on the Opportunity dataset. The lens should return only that rep's opportunities.

**Why it matters:** Without this predicate, a rep with Salesforce "Private" OWD on Opportunity still sees the entire pipeline in Analytics. Security predicates are the only mechanism that enforces row-level visibility in CRM Analytics. Salesforce sharing rules do not cross into Analytics unless sharing inheritance is explicitly enabled.

---

## Example 2: Sharing Inheritance with Backup Predicate for Account Data

**Context:** A service team uses CRM Analytics to analyze Account health metrics. The org uses complex territory-based Salesforce sharing on the Account object. The analytics team wants to mirror that sharing logic into CRM Analytics without duplicating it in a custom predicate that would drift every time territory assignments change.

**Problem:** Sharing inheritance is the right approach here, but when first enabled, the admin leaves the backup predicate blank. Two regional managers who oversee more than 3,000 accounts each begin seeing all account rows in Analytics — because sharing inheritance was bypassed at the 3,000-record threshold and the blank backup predicate defaulted to all-visible access.

**Solution:**

1. Open the Account dataset in Analytics Studio and navigate to Security.
2. Set the Security Predicate Type to **Sharing Inheritance**.
3. Set the Salesforce Object to `Account`.
4. In the Backup Predicate field, explicitly enter:

```
'false'
```

   This ensures that any user for whom sharing inheritance is bypassed (3,000+ accessible records) sees zero rows rather than all rows. If those users legitimately need broader access, they should be granted the View All Data permission on the permission set, which causes `"$User.HasViewAllData"` to resolve to `"true"` and bypasses the predicate entirely through a separate mechanism.
5. Save and test with a user who has restricted account access. Confirm only their accounts appear in a lens.
6. If possible, identify a user who owns more than 3,000 accounts in the org and confirm they see zero rows (backup predicate firing), then escalate to grant them View All Data if appropriate.

**Why it matters:** The 3,000-record threshold is a hard platform limit. Leaving the backup predicate blank is the most common security defect in sharing inheritance configurations — it converts a scoped-access design into an all-visible dataset for high-volume users, which is the opposite of the intended behavior.

---

## Example 3: Diagnosing a "No Data" Report from a Sales Rep

**Context:** A sales rep opens a CRM Analytics dashboard and sees empty charts. They confirm they have a CRM Analytics license and can open the app. The dashboard was working for other reps last week.

**Problem:** The rep was recently moved to a new territory. As part of the territory update, their `OwnerId` on their Opportunities was bulk-updated, but an admin also recently narrowed the security predicate on the Opportunity dataset to filter by both `OwnerId` and a `Territory__c` column. The `Territory__c` column name in the dataset is actually `Territory_c` (single underscore, the Analytics column name normalization dropped a character). The predicate references `'Territory__c'` (two underscores) which does not match the actual column name, so the predicate evaluates to zero rows for all users.

**Solution:**

1. Navigate to the Opportunity dataset's Security tab and copy the current predicate.
2. Open the dataset schema viewer and search for all column names containing "Territory". Note the exact name (case and underscores).
3. Update the predicate to use the exact column name found in the schema.
4. Save and test by opening the lens as the affected rep.

**Why it matters:** Predicate column name mismatches cause a silent deny — no error is shown, the dashboard just renders empty. This is indistinguishable from a correct deny predicate working as intended unless you know to check the schema column names. Always verify column names from the schema, not from the Salesforce field API name.

---

## Anti-Pattern: Using Salesforce Permission Sets to Control Analytics Row Access

**What practitioners do:** They add users to a permission set that grants "View Encrypted Data" or object-level access on Opportunity, assuming this will also control which rows those users see in CRM Analytics.

**What goes wrong:** Permission sets control Salesforce Lightning and API access. They have no effect on CRM Analytics dataset row visibility. A user can have zero Salesforce object permissions and still see all rows in a CRM Analytics dataset if no predicate is configured. Conversely, a user can have full Salesforce object access and see zero rows in Analytics if a predicate denies them.

**Correct approach:** Configure security predicates or sharing inheritance directly on each CRM Analytics dataset. Treat Analytics row-level security as a completely independent control plane from Salesforce permissions and sharing.
