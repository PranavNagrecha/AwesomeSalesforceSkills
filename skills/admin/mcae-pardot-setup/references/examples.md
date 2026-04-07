# Examples — MCAE (Pardot) Setup

## Example 1: Activating a Paused v2 Connector After New BU Provisioning

**Context:** A marketing ops admin was told by the Salesforce team that the new Account Engagement business unit was "ready to go." The admin creates a test prospect in MCAE but the Lead never appears in Salesforce. The admin checks the connector page in MCAE and sees the connector status shows "Paused."

**Problem:** Every new MCAE business unit auto-creates a Salesforce v2 connector in a Paused state. No sync of any kind (prospect-to-Lead, user sync, campaign sync) occurs while the connector is Paused. The system does not raise an alert or send an email to indicate this is the cause of missing data — the prospect creation succeeds without error, but the sync job never runs.

**Solution:**

```text
Steps to activate the connector:

1. In Account Engagement, navigate to:
   Account Engagement Settings > Connectors

2. Click the name of the Salesforce connector (labeled "Salesforce CRM").

3. Click "Verify Now" to run an authentication handshake.
   - If verification fails: confirm the connector user's OAuth permissions
     and that the connector user's Salesforce profile has API Enabled.
   - If verification succeeds: the connector moves to a Verified/Paused state.

4. Click "Resume" (or "Unpause") to set the connector to Active.

5. Confirm status reads "Active" in the Connectors list.

6. Create a new test Lead in Salesforce with an email address that does not
   already exist in MCAE. Within 2–5 minutes, verify a matching prospect
   record appears in MCAE Prospects.
```

**Why it works:** The v2 connector uses OAuth 2.0 to authenticate against the Salesforce org using the designated connector user. Verification confirms the token exchange succeeds. Once Active, the connector begins polling for sync changes on a near-real-time cadence (sync typically completes within 1–4 minutes for individual record changes).

---

## Example 2: Diagnosing a Field That Is Not Syncing Due to Missing Connector User FLS

**Context:** A Salesforce admin adds a new custom field `Renewal_Interest__c` (Picklist) to the Lead object and maps it to a matching MCAE custom prospect field `renewal_interest`. Both fields are visible in their respective UIs, but values updated in MCAE never appear in Salesforce, and values updated in Salesforce never appear in MCAE.

**Problem:** The connector user's profile does not have field-level security (read/write) on `Renewal_Interest__c`. The connector runs as the connector user, so it inherits that user's FLS. The connector does not log a warning for FLS-blocked fields — it silently skips them. Practitioners routinely spend hours troubleshooting the sync rule and field mapping, not realizing the issue is permissions.

**Solution:**

```text
To audit and fix connector user FLS:

1. In Salesforce Setup, navigate to Profiles > [Connector User's Profile].
2. Under "Field Permissions," search for "Renewal_Interest."
3. Confirm both "Read Access" and "Edit Access" are checked for
   Renewal_Interest__c on the Lead object.
4. If missing, edit the profile (or the assigned permission set) to add
   Read and Edit access.
5. No connector restart or re-verification is needed — the next sync
   cycle will pick up the field.

Alternatively, use the Field Accessibility tool:
  Setup > Field Accessibility > Lead > View by Profiles
  Filter by connector user's profile to see all fields in one view.

Recommended: create a Permission Set named "MCAE Connector Field Access"
containing explicit FLS for every MCAE-synced field, then assign this
permission set to the connector user. This separates MCAE field permissions
from the base profile and makes future additions auditable.
```

**Why it works:** Salesforce field-level security is enforced at the API layer — the connector's REST/SOAP calls are subject to the same FLS as any other API user with those credentials. By maintaining a dedicated permission set, new synced fields can be added to the permission set without modifying the connector user's profile directly, reducing the risk of unintentional permission escalation.

---

## Example 3: Configuring Salesforce User Sync to Eliminate Dual-User Management

**Context:** A marketing team has 15 users managed separately in both Salesforce and Account Engagement. When a new hire joins, the Salesforce admin creates their Salesforce user, and the MCAE admin separately creates their MCAE user and assigns a role. When someone is terminated, the Salesforce admin deactivates their Salesforce user, but forgets to deactivate their MCAE user — leaving an active MCAE account for a departed employee.

**Problem:** Without User Sync, MCAE user management is independent of Salesforce user management. The two systems can diverge, producing security gaps (active MCAE users without active Salesforce users) and operational overhead (dual provisioning/deprovisioning for every user change).

**Solution:**

```text
Steps to enable Salesforce User Sync:

Pre-conditions to verify BEFORE enabling:
  a. Salesforce v2 connector is Active (not Paused).
  b. Every current MCAE user has a corresponding active Salesforce user
     record with a matching email address.
  c. Profile-to-role mapping is decided:
     - Salesforce Profile "Marketing Admin" → MCAE Role "Administrator"
     - Salesforce Profile "Marketing User" → MCAE Role "Marketing"
     - Salesforce Profile "Sales User" → MCAE Role "Sales" (read-only access)

Enablement steps:
  1. In Account Engagement Settings > User Management > User Sync,
     click "Map Profiles."
  2. For each MCAE role, select the corresponding Salesforce profile(s).
     A single MCAE role can map to multiple Salesforce profiles.
  3. Review the sync preview — MCAE will show which existing users will be
     matched and which will be orphaned.
  4. Resolve any orphaned MCAE users (assign them the correct Salesforce
     profile or deactivate them in MCAE first).
  5. Click "Enable Salesforce User Sync."
  6. Verify: add a test Salesforce user to a mapped profile and confirm
     they appear in MCAE within 5 minutes.
  7. Verify: deactivate the test Salesforce user and confirm their MCAE
     record is deactivated automatically.
```

**Why it works:** Once User Sync is active, MCAE listens for profile assignment changes on Salesforce users. When a user is assigned to a mapped profile, MCAE provisions them with the corresponding role. When a user is deactivated or moved to an unmapped profile in Salesforce, MCAE deactivates their account automatically. The single source of truth for user access becomes Salesforce — consistent with Salesforce's identity governance model.

---

## Anti-Pattern: Enabling Recycle Bin Sync Without Auditing the CRM Recycle Bin First

**What practitioners do:** An admin is asked to "clean up" MCAE prospects after a CRM data cleanup project. They enable the Recycle Bin Sync option in MCAE connector settings, assuming it will only affect future record deletions.

**What goes wrong:** Recycle Bin Sync is retroactive on first enable. If the Salesforce Recycle Bin contains deleted Lead or Contact records that have matching MCAE prospects, those prospects are archived (soft-deleted) in MCAE on the next sync cycle. In one documented scenario, enabling this setting without auditing the Recycle Bin archived several thousand active prospects, including records from live nurture campaigns.

**Correct approach:** Before enabling Recycle Bin Sync:
1. Export the current CRM Recycle Bin contents for Lead and Contact objects.
2. Cross-reference those emails against active MCAE prospects.
3. Permanently delete any CRM Recycle Bin records whose matching prospects must remain active in MCAE.
4. Only then enable Recycle Bin Sync.
5. Document the decision to enable or disable Recycle Bin Sync in the BU configuration record so future admins understand the setting's state.
