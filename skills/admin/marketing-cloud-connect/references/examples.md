# Examples — Marketing Cloud Connect

## Example 1: Initial MC Connect Setup with Dedicated Connector User

**Context:** A company is connecting their Salesforce Sales Cloud org to a Marketing Cloud Enterprise 2.0 account for the first time. The marketing team needs to sync Contact and Lead records into Marketing Cloud and send campaigns using Salesforce data.

**Problem:** Without a proper connector user setup, practitioners often use a shared admin account. When that admin's password changes or their profile is modified, all MC sync jobs fail silently.

**Solution:**

Step 1 — Create the connector user in Salesforce:
```
User record:
  First Name: MC
  Last Name: Connector
  Username: mc.connector@company.com.mcconnect  (unique, not a real inbox)
  Profile: Salesforce (standard internal user profile with API Enabled)
  Email: it-team@company.com  (real inbox for password reset notifications)
  User License: Salesforce

Permission Set: Assign "Marketing Cloud" permission set to this user.
Password policy: Add this user to a permission set or profile that sets
  password expiration to "Never Expires" to prevent silent sync breaks.
```

Step 2 — Install the managed package:
```
AppExchange: search "Salesforce Marketing Cloud"
Install for Admins Only (or All Users if needed for custom objects)
Package namespace: et4ae5
```

Step 3 — Connect in Marketing Cloud:
```
Marketing Cloud Setup > Platform Tools > Apps > Salesforce Integration
> Connect Account
> Authenticate with mc.connector@company.com.mcconnect credentials
> Select scope: Org-Wide (for single-BU setups)
> Save
```

Step 4 — Enable Synchronized Data Sources:
```
Marketing Cloud Connect > Synchronized Data Sources
Enable: Contact, Lead, Campaign, CampaignMember
Field selection: review and deselect fields not needed for sends (stay under 250)
Save > allow 15 min for initial sync
```

**Why it works:** The dedicated connector user isolates authentication from human admin accounts. The Marketing Cloud permission set grants the precise object-level and API access MC Connect requires without over-privileging. Using a real IT team inbox for the user's email ensures password reset notifications are seen.

---

## Example 2: Diagnosing and Fixing Missing Subscribers Due to Scope Mismatch

**Context:** A B2B company runs a Marketing Cloud campaign targeted at all Contacts in a specific Salesforce account. The audience builder shows 1,200 contacts from the SDS DE, but the final send recipient count is only 340.

**Problem:** The Marketing Cloud account is an Enterprise 2.0 instance with three Business Units. The Salesforce connector was configured at the parent-account level with Org-Wide scope, but the send is being executed from a child BU. The child BU's scope was set to BU-specific during its own connector configuration, and only contacts associated with that BU's territory are within scope.

**Solution:**

Step 1 — Confirm current scope settings:
```
Salesforce org:
  Marketing Cloud Connect > Configuration
  Scope: Org-Wide  ← this is the parent-level setting

Marketing Cloud (child BU):
  Setup > Salesforce Integration > Connected Org
  Scope: Business Unit  ← child BU has its own scope
```

Step 2 — Determine intent: does the child BU legitimately need access to all Contacts, or only contacts assigned to its territory?

Option A — If all contacts are in scope for this BU:
```
In Marketing Cloud child BU:
  Setup > Salesforce Integration > Connected Org > Edit
  Change Scope from "Business Unit" to "Org-Wide"
  Save > trigger manual sync refresh
```

Option B — If only specific contacts should be in scope:
```
In Salesforce, verify Contact records have the correct field values
(e.g., BU_Assignment__c = 'West') that the child BU scope filter references.
Correct any records that are missing the BU assignment field value.
Trigger a manual SDS sync refresh.
```

Step 3 — Validate the fix:
```
After sync completes (~15 min), re-run the audience count in Marketing Cloud.
Compare against Salesforce report of contacts matching the same criteria.
Counts should match within a small margin (allowing for opt-outs).
```

**Why it works:** Scope is evaluated at send time, not at sync time. SDS will replicate records regardless of scope, but Marketing Cloud filters the sendable audience based on the scope configured for the sending Business Unit. Aligning scope — not manipulating the DE directly — is the correct fix.

---

## Example 3: Triggered Send from Salesforce Flow for Welcome Email

**Context:** A SaaS company wants to send a personalized welcome email via Marketing Cloud when a new Contact record is created in Salesforce with `Contact_Type__c = 'Trial User'`.

**Problem:** Without triggered sends, the marketing team would have to manually export new trial users to a CSV and import them into Marketing Cloud for a Journey. This introduces delays and manual work.

**Solution:**

Step 1 — Create the Triggered Send Definition in Marketing Cloud:
```
Email Studio > Interactions > Triggered Sends > Create
Name: Welcome_Trial_User
Email: [select the Welcome email content block]
Send Classification: Transactional
Subscriber Key: ContactID (matches SF Contact ID)
From: noreply@company.com
Status: Active (start the triggered send)
```

Step 2 — Create the Flow in Salesforce:
```
Flow: Record-Triggered Flow
Object: Contact
Trigger: A record is created
Entry Condition: Contact_Type__c = 'Trial User'

Action: Marketing Cloud Send Email (from MC Connect package)
  Triggered Send External Key: Welcome_Trial_User
  Subscriber Key: {!$Record.Id}  (Contact ID as subscriber key)
  Email Address: {!$Record.Email}
```

Step 3 — Test end-to-end:
```
Create a test Contact in Salesforce with Contact_Type__c = 'Trial User'
Monitor Flow execution in Setup > Flows > Debug
Check Marketing Cloud Triggered Send Logs for the send record
Verify email delivery to the test email address
Wait 15-30 min, check Contact record activity timeline for tracking write-back
```

**Why it works:** MC Connect exposes a Flow action that calls the Marketing Cloud Triggered Send API authenticated as the connector user. The Transactional send classification means this send bypasses commercial suppression lists, ensuring delivery even to contacts who have unsubscribed from marketing sends (subject to CAN-SPAM/GDPR transactional exemptions, which must be assessed separately).

---

## Anti-Pattern: Sending Directly to a Synchronized Data Extension

**What practitioners do:** After enabling SDS for Contact, they navigate to Email Studio > Send Email, select the Contact SDS data extension as the target audience, and attempt to send.

**What goes wrong:** Marketing Cloud returns an error: the SDS data extension is not sendable. SDS DEs do not have a subscriber key field designated as the "send relationship" field required for Email Studio sends. The send fails or the DE does not appear in the audience picker.

**Correct approach:** Create a sendable data extension that derives data from the SDS DE:

Option A — SQL Query Activity in Automation Studio:
```sql
SELECT
    c.ContactID AS SubscriberKey,
    c.Email,
    c.FirstName,
    c.LastName,
    c.AccountName
FROM Contact_Salesforce c  -- SDS DE name
WHERE c.Email IS NOT NULL
  AND c.HasOptedOutOfEmail = false
```
Schedule this query to run before each send and write to a sendable target DE.

Option B — Contact Builder Data Extension Relationship:
```
Contact Builder > Data Extensions > [SDS Contact DE]
> Create Relationship
Link SDS DE to All Contacts on ContactID = SubscriberKey
Create a linked sendable DE
```
