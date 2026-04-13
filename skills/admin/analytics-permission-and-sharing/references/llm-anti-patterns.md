# LLM Anti-Patterns — Analytics Permission and Sharing

Common mistakes AI coding assistants make when generating or advising on CRM Analytics permissions and row-level security. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Salesforce OWD Automatically Controls CRM Analytics Row Visibility

**What the LLM generates:** "Since your Opportunity OWD is set to Private, each sales rep will only see their own opportunities in your Analytics dashboard."

**Why it happens:** LLMs conflate the Salesforce security model (OWD, sharing rules, profiles) with the CRM Analytics security model. Training data contains many references to Salesforce data access controlled by OWD, and the model generalizes this incorrectly to Analytics. CRM Analytics is a separate runtime with a separate data store; it does not apply OWD at query time.

**Correct pattern:**

```
Salesforce OWD controls record access in Lightning UI and SOQL-based tools only.
CRM Analytics requires a separate, explicit row-level security configuration on each dataset.

To restrict Opportunity rows to the record owner:
1. Open the Opportunity dataset in Analytics Studio → Security tab.
2. Set security predicate to: 'OwnerId' == "$User.Id"
3. Verify the OwnerId column name matches the dataset schema exactly (case-sensitive).
4. Test by logging in as a non-admin rep and opening a lens.
```

**Detection hint:** Look for phrases like "your Salesforce sharing rules will control," "OWD will restrict," or "since the object is Private, users won't see..." when discussing Analytics dashboards — these are incorrect framing.

---

## Anti-Pattern 2: Forgetting the Backup Predicate When Enabling Sharing Inheritance

**What the LLM generates:** "Enable Sharing Inheritance on the Account dataset and set the Salesforce Object to Account. This will automatically mirror your Salesforce sharing rules into Analytics."

**Why it happens:** The LLM describes sharing inheritance correctly but omits the backup predicate step. The 3,000-record threshold is a non-obvious platform constraint that is rarely emphasized in surface-level documentation, so training data underrepresents it.

**Correct pattern:**

```
When enabling sharing inheritance:
1. Set Predicate Type → Sharing Inheritance
2. Set Salesforce Object → Account (or Case/Contact/Lead/Opportunity)
3. Set Backup Predicate → 'false'
   (REQUIRED — if left blank, users with 3,000+ source records see ALL rows)
4. Save and test with a user who has limited account access.
```

**Detection hint:** Any response that recommends enabling sharing inheritance without mentioning the backup predicate field or the 3,000-record threshold is incomplete and potentially creates a security defect.

---

## Anti-Pattern 3: Writing Predicate Column Names from Memory Instead of from the Dataset Schema

**What the LLM generates:**
```
Set security predicate to: 'opportunity_owner_id__c' == "$User.Id"
```
using the Salesforce custom field API name rather than the actual dataset column name.

**Why it happens:** LLMs derive column names from context (e.g., the user says "the OwnerId field") and use Salesforce field API naming conventions (`__c` suffix, lowercase). Dataset column names are set at sync time and often differ — they can be normalized, aliased in recipes, or have different casing.

**Correct pattern:**

```
Before writing any predicate:
1. Open the dataset in Analytics Studio.
2. Navigate to the dataset schema viewer.
3. Find the exact column name as it appears in the schema (copy-paste, do not type from memory).
4. Use that exact string in the predicate, including exact case and underscores.

Example: if the schema shows 'OwnerId', the predicate is:
'OwnerId' == "$User.Id"
NOT 'ownerid' == "$User.Id"
NOT 'Owner_Id' == "$User.Id"
```

**Detection hint:** If a predicate references a column name with `__c` suffix or all-lowercase field names without having been verified against the schema, flag it for column name verification.

---

## Anti-Pattern 4: Treating App-Level Sharing as Row-Level Security

**What the LLM generates:** "To ensure reps only see their own data, share the Analytics app with each rep as a Viewer and remove Manager access. This will prevent them from seeing other reps' data."

**Why it happens:** LLMs correctly understand that app sharing controls access to the app, and incorrectly extend this to assume it controls data row visibility. The distinction between UI access control (app sharing) and data access control (dataset predicate) is subtle and counterintuitive.

**Correct pattern:**

```
App-level sharing (Viewer/Editor/Manager) controls:
- Which assets appear in the app navigation
- Who can edit or re-share the app
- UI-level access to dashboards and lenses

App-level sharing does NOT control:
- Which rows a user sees in a dataset
- Direct REST API access to dataset data

To restrict row visibility, configure a security predicate on the dataset
(separate from app sharing, independently required).
```

**Detection hint:** Responses that describe restricting data access only through app sharing roles without mentioning dataset predicates are incomplete. Look for "share the app as Viewer" as the only security step.

---

## Anti-Pattern 5: Suggesting Salesforce Permission Sets or Profiles to Control Analytics Row Access

**What the LLM generates:** "Create a permission set that grants Read access only to the user's own Opportunity records (using a standard object permission with record ownership filter). Assign this to the Analytics users."

**Why it happens:** LLMs correctly know that permission sets control Salesforce record access and apply this pattern to Analytics incorrectly. Permission sets affect Salesforce Lightning, SOQL, and APIs — they have no runtime effect on CRM Analytics dataset queries.

**Correct pattern:**

```
Permission sets in CRM Analytics control:
- Whether a user can access Analytics at all (PSL assignment: CRM Analytics Plus/Growth)
- Admin-level capabilities within Analytics Studio

Permission sets do NOT control:
- Which rows a user sees in a CRM Analytics dataset
- Dataset-level read/write access

Row visibility in CRM Analytics is controlled exclusively by:
1. Security predicates on the dataset
2. Sharing inheritance on the dataset (for 5 supported objects)

Configure row-level security in Analytics Studio → Dataset → Security tab.
```

**Detection hint:** Any recommendation to use Salesforce permission sets or profiles as the primary mechanism for controlling Analytics row visibility (as opposed to licensing) is an anti-pattern. Permission sets are only relevant for the license (PSL) layer, not the data layer.

---

## Anti-Pattern 6: Assuming Sharing Inheritance Works for Custom Objects or External Data

**What the LLM generates:** "Enable sharing inheritance on your custom object `Revenue_Record__c` dataset so that users only see their own revenue records."

**Why it happens:** Sharing inheritance sounds like a general mechanism and the name implies it would work for any Salesforce-sourced data. LLMs over-generalize from the Account example without noting the five-object limit.

**Correct pattern:**

```
Sharing inheritance is supported ONLY for these five standard objects:
- Account
- Case
- Contact
- Lead
- Opportunity

For all other data sources (custom objects, external data, CSV uploads):
Use a security predicate instead.

Example for a custom object with OwnerId:
'OwnerId' == "$User.Id"

If the custom object has a lookup to Account and you want to mirror Account sharing,
join the Account dataset and filter on the Account's sharing-inherited column.
```

**Detection hint:** Any response that recommends enabling sharing inheritance for a custom object (`__c` suffix) or an external data source should be flagged as incorrect.
