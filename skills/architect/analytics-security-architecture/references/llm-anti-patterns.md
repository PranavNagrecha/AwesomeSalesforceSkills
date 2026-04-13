# LLM Anti-Patterns — Analytics Security Architecture

Common mistakes AI coding assistants make when generating or advising on CRM Analytics security design. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Salesforce Record-Level Sharing Automatically Restricts Analytics Dataset Rows

**What the LLM generates:** "Since your Salesforce Opportunity object has OWD set to Private with role-hierarchy sharing, your CRM Analytics dashboard will automatically show each user only their own records. No additional configuration is needed."

**Why it happens:** LLMs conflate the Salesforce sharing model (which governs SOQL queries via record visibility) with CRM Analytics dataset access (which is governed by independent security predicates). Training data often discusses Salesforce security holistically without clearly distinguishing the Analytics-specific layer. The assumption that security "cascades down" from the platform to the BI layer is intuitive but incorrect for CRM Analytics.

**Correct pattern:**

```
CRM Analytics security is independent of Salesforce OWD and sharing rules.
After building any dataset from a sensitive Salesforce object, you MUST either:
  1. Configure a security predicate on the dataset (e.g., 'OwnerId' == "$User.Id"), OR
  2. Enable sharing inheritance AND set a backup predicate of 'false'.
Without one of these configurations, all licensed Analytics users see all rows.
```

**Detection hint:** Look for phrases like "CRM Analytics will automatically respect", "inherits from Salesforce sharing", "OWD applies to Analytics", or any Analytics security guidance that does not mention a predicate or sharing inheritance configuration.

---

## Anti-Pattern 2: Recommending Sharing Inheritance Without Mentioning the 3,000-Row Limit or Backup Predicate

**What the LLM generates:** "Enable Sharing Inheritance on the dataset in Analytics Studio. This will mirror your Salesforce role hierarchy so that managers see their team's records and individual reps see only their own. This is simpler than writing a custom predicate."

**Why it happens:** Sharing inheritance is a legitimate and documented feature that LLMs correctly identify as an alternative to hand-written predicates. However, the 3,000-row threshold constraint is a specific platform limit that may not be prominent in training data, and the backup predicate requirement is an easy-to-miss detail even in official documentation.

**Correct pattern:**

```
Sharing inheritance is valid when:
  - The source is a Salesforce-connected dataset.
  - Every user's accessible row count in the source object is verifiably under 3,000.

A backup predicate of 'false' is MANDATORY alongside sharing inheritance:
  Dataset predicate (backup): 'false'

Without the backup predicate, users who exceed 3,000 rows see ALL rows in the dataset.
```

**Detection hint:** Any recommendation to use sharing inheritance that does not mention "3,000 rows", "backup predicate", or the threshold limit. Also flag sharing inheritance recommendations for datasets where any user role could plausibly have visibility to thousands of records.

---

## Anti-Pattern 3: Writing Predicates That Reference Other Datasets or Use SQL-Style Subqueries

**What the LLM generates:**

```sql
-- Suggested predicate:
'OwnerId' in (SELECT UserId FROM entitlement_ds WHERE TeamId == "$User.TeamId__c")
```

Or: "Apply a predicate that joins to your account_entitlement dataset to determine which accounts the current user is authorized to see."

**Why it happens:** Developers trained on SQL naturally reach for subqueries and joins when the filter condition requires a lookup. LLMs replicate this pattern without accounting for the CRM Analytics predicate constraint that only allows SAQL filter expressions over columns present in the current dataset.

**Correct pattern:**

```
Predicates are SAQL filter strings — they cannot reference other datasets or use subqueries.
Cross-dataset security MUST be solved at dataflow/recipe run time using an augment step:

  1. Build an entitlement dataset (e.g., user_team_entitlement_ds) with columns:
       UserId | EntitlementKey
  2. In the main dataflow/recipe, augment the main dataset with this entitlement dataset
       joined on the shared dimension.
  3. The resulting dataset has Authorized_UserId embedded as a column.
  4. Apply the predicate: 'Authorized_UserId' == "$User.Id"
```

**Detection hint:** Any predicate string that contains `SELECT`, `FROM`, `JOIN`, or references a dataset name (e.g., `entitlement_ds`, `user_lookup`). Also flag any suggestion to "query another dataset" or "look up from" another source within the predicate string.

---

## Anti-Pattern 4: Using Source Object Field API Names Instead of Verified Dataset Column Names in Predicates

**What the LLM generates:**

```
Security predicate: 'ownerid' == "$User.Id"
```

(Lowercase `ownerid`, matching the Salesforce field API name convention.)

**Why it happens:** Salesforce field API names are conventionally lowercase (e.g., `ownerid`, `accountid`, `recordtype`), and LLMs trained on Salesforce documentation reproduce this convention. However, CRM Analytics dataset column names are case-sensitive and are determined by the dataflow or recipe transformation steps — not by the source Salesforce field API name. The dataset column may be `OwnerId`, `Owner_Id`, `OWNERID`, or any other casing depending on how the dataflow was built.

**Correct pattern:**

```
NEVER write a predicate using an assumed column name.
ALWAYS verify column names by:
  1. Opening Analytics Studio.
  2. Navigating to the target dataset.
  3. Opening the Schema tab.
  4. Copying the exact column name character-for-character.

A predicate with wrong casing returns zero rows silently — no error is produced.
Example: if schema shows 'OwnerId', the predicate must be:
  'OwnerId' == "$User.Id"   ← correct
  'ownerid' == "$User.Id"   ← silently broken
```

**Detection hint:** Any predicate that uses all-lowercase column names (e.g., `'ownerid'`, `'accountid'`, `'recordtypeid'`) without an explicit note that the column casing was verified in the dataset schema. Flag and require schema verification before accepting the predicate.

---

## Anti-Pattern 5: Claiming a Predicate of 'false' Will Block Users with View All Data Permission

**What the LLM generates:** "To lock down this dataset for all users during testing, set the security predicate to `'false'`. This will prevent any user from seeing rows until you're ready."

Or: "If you need to restrict even administrators from seeing data, use a predicate of `'false'`."

**Why it happens:** The predicate `'false'` is legitimately used as a safe-default backup predicate when sharing inheritance cannot apply. LLMs correctly describe its effect for normal users but do not account for the View All Data permission bypass. The bypass is a platform-level override that is not overridable by any predicate.

**Correct pattern:**

```
A predicate of 'false' blocks all rows for users WITHOUT the View All Data permission.
Users WITH the View All Data system permission bypass ALL predicates unconditionally.
No predicate — including 'false' — can restrict a View All Data user.

To fully restrict Analytics access for privileged users:
  - Remove the CRM Analytics license from users who should not have access.
  - Remove the View All Data permission from users who should be subject to predicates.
  - Use dataset-level sharing to remove dataset access entirely for those users.
```

**Detection hint:** Any statement suggesting that `'false'` or any predicate can restrict access for system administrators, users with View All Data, or users with "full Salesforce access". Also flag any security design that does not separately address View All Data holders in the user population.

---

## Anti-Pattern 6: Treating Analytics Security as a One-Time Configuration

**What the LLM generates:** "Configure the security predicate on the dataset once during setup and you're done. The predicate will automatically enforce the correct access control going forward."

**Why it happens:** Predicates appear static — they are a string on a dataset record — so LLMs treat them as a set-and-forget configuration. The operational reality is that predicates may need to be updated when dataflow changes rename columns, and cross-dataset entitlement patterns require ongoing refresh to remain accurate.

**Correct pattern:**

```
CRM Analytics security requires ongoing operational maintenance:

1. When dataflow or recipe changes rename or restructure columns, predicates referencing
   those columns must be updated before the next dataflow run to avoid silent zero-row returns.

2. Cross-dataset entitlement datasets must be refreshed on the same schedule as
   entitlement changes in Salesforce (e.g., account team membership, territory assignment).

3. View All Data permission holders must be reviewed periodically as users are granted
   or promoted to admin-level permissions.

4. Dataset-level sharing grants must be reviewed as teams and user populations change.

Analytics security is an operational discipline, not a project-phase deliverable.
```

**Detection hint:** Any security design documentation that describes predicate configuration without a maintenance cadence, a refresh schedule for entitlement datasets, or a periodic access review process.
