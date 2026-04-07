# Gotchas — MCAE (Pardot) Setup

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: v2 Connector Auto-Created in Paused State — Sync Never Starts Without Manual Activation

**What happens:** When Salesforce provisions a new MCAE business unit, it automatically creates a Salesforce v2 connector for that BU. This connector is in a **Paused** state by default. No prospect sync, user sync, or campaign sync occurs while the connector is Paused. MCAE does not display a warning, send an email, or surface an error in the sync log — the BU simply operates as an island, with no data flowing to or from Salesforce.

**When it occurs:** Every time a new MCAE business unit is provisioned. Also occurs if an admin disconnects and re-creates the connector without explicitly resuming it afterward.

**How to avoid:** Immediately after BU provisioning, navigate to Account Engagement Settings > Connectors, open the v2 connector, click "Verify Now" to confirm authentication, then click "Resume." Add "Connector Active status confirmed" to every BU setup checklist as the first item — before configuring anything else.

---

## Gotcha 2: Connector User FLS Silently Blocks Field Sync — No Error Is Raised

**What happens:** If the connector user's profile or permission set lacks field-level security (read or write) on any object field that is mapped for sync, that field is silently skipped during sync. MCAE does not log a field-level sync failure, does not flag the field as unavailable, and does not alert the admin. From the admin's perspective, the connector is "Active" and sync appears to be working — but specific fields simply never update between systems.

**When it occurs:** Any time a new custom field is added to a synced object (Lead, Contact, Account, Opportunity) without updating the connector user's FLS. Also occurs if a Salesforce admin changes a profile or permission set that the connector user depends on, inadvertently removing FLS from previously syncing fields.

**How to avoid:** Maintain a dedicated permission set named something like "MCAE Connector Field Access" containing explicit read/write FLS for every MCAE-synced field. Assign this permission set to the connector user. When a new field is added to the sync, add it to the permission set before mapping it in MCAE. Periodically audit the connector user's effective field permissions using Setup > Field Accessibility and cross-reference against the MCAE field mapping configuration.

---

## Gotcha 3: Salesforce User Sync Is Irreversible in Standard Orgs

**What happens:** Once Salesforce User Sync is enabled in an MCAE business unit, it cannot be turned off through the MCAE admin UI. The "Disable User Sync" option is not available in the standard interface. Rolling back requires opening a Salesforce Support case, which can take days. During that time, the BU is in a state where MCAE-native user management is hidden but administrators expect it to be accessible.

**When it occurs:** Any time an admin enables User Sync to "try it out" without understanding the commitment, or enables it before the profile-to-role mapping is finalized, or enables it before verifying that all existing MCAE users have matching Salesforce records.

**How to avoid:** Treat User Sync enablement as a one-way door. Before enabling:
1. Verify every existing MCAE user has a Salesforce user with a matching email address on a profile that maps to an MCAE role.
2. Test the profile-to-role mapping in a sandbox MCAE BU first if available.
3. Get explicit sign-off from the MCAE admin who owns user management for the org.
4. Document that User Sync is enabled in the BU configuration record so future admins do not attempt to manage users through the MCAE UI and wonder why it is hidden.

---

## Gotcha 4: Prospect Email Is the Only Sync Key — Duplicate Emails Cause Split Prospect Records

**What happens:** MCAE uses email address as the sole matching key when syncing prospects to Salesforce Leads and Contacts. If the same email address exists on both a Lead record and a Contact record in Salesforce, MCAE creates two separate prospect records — one linked to the Lead and one linked to the Contact. These prospects have separate activity histories, scores, and campaign memberships and do not merge automatically. If the same email address is submitted through an MCAE form that already exists in MCAE under a different Salesforce record, the existing prospect is updated but no CRM record merge occurs.

**When it occurs:** Common in orgs that convert Leads to Contacts without deduplicating, or that import lists into both MCAE and Salesforce independently. Also surfaces during CRM data migrations that import contact records without deduplicating against existing MCAE prospects.

**How to avoid:** Before the first sync or before a list import:
1. Run a deduplication report in Salesforce for Leads and Contacts with overlapping email addresses.
2. Merge or delete duplicates in Salesforce before enabling the connector or importing into MCAE.
3. In MCAE, use the Prospect Audit report to identify prospects that have no CRM record link and reconcile them before go-live.
4. Establish a policy for whether new form submissions should create a Lead or a Contact, and keep that consistent with the MCAE-to-CRM sync object preference setting.

---

## Gotcha 5: Campaign Member Status Mapping Must Be Done Before First MCAE Send — Retroactive Mapping Is Not Applied

**What happens:** MCAE writes Campaign Member records to Salesforce when a prospect engages with an MCAE campaign that is linked to a Salesforce campaign. However, the Campaign Member Status values (e.g., "Sent," "Opened," "Clicked," "Responded") must be configured on the Salesforce campaign before the MCAE send occurs. If a send happens before the status mapping is configured, those engagement events are not retroactively written as Campaign Member records — the data is simply lost from the Salesforce campaign attribution perspective.

**When it occurs:** Most commonly during initial BU setup when an eager marketing team starts sending emails before the admin has finished the campaign connector configuration. Also occurs when a new campaign type is introduced (e.g., SMS, webinar) that uses different status values that were never added to the Campaign Member Status picklist.

**How to avoid:**
1. Before any MCAE campaign send, confirm the Salesforce campaign is created, linked in MCAE, and has the required Campaign Member Status values added.
2. Standard required statuses to add: "Sent," "Opened," "Clicked," "Responded," "Unsubscribed."
3. Add campaign connector configuration to the pre-send launch checklist in the marketing team's campaign operations process.
4. If a send has already occurred without proper mapping, create the Campaign Member records manually or via data load for the affected campaign — MCAE will not backfill them automatically.

---

## Gotcha 6: Tracking Domain Requires DNS CNAME Before Any Visitor Tracking or Email Link Tracking Works

**What happens:** The MCAE tracking pixel (used for website visitor tracking) and the tracking URLs embedded in MCAE email links both rely on requests routed through the configured tracking domain. Until the tracking domain's CNAME DNS record is created at the domain registrar and propagated, all tracking calls fail silently. Visitors are not recorded as prospects, email opens and clicks are not counted, and scoring based on website activity does not accumulate.

**When it occurs:** During initial BU setup when the connector and user sync are configured but the DNS step is either unknown to the admin or deferred to a separate team. Also occurs when the tracking domain is changed (e.g., rebranding) and DNS is updated before MCAE domain management is updated, or vice versa.

**How to avoid:**
1. Add tracking domain configuration as an explicit step in the BU setup project plan, with ownership assigned to the team that manages DNS (often IT or web ops, not the MCAE admin).
2. After DNS propagation, verify the tracking domain shows as Active in Account Engagement Settings > Domain Management before embedding the tracking pixel in any website pages or sending any MCAE emails.
3. Use a DNS propagation checker tool to confirm the CNAME resolves correctly from multiple geographic locations before marking the domain as ready.
