# Gotchas — Marketing Cloud Connect

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: The 250-Field Limit Is Silent and Retrospective

**What happens:** When a Salesforce object enabled for Synchronized Data Sources has more than 250 fields, Marketing Cloud silently excludes all fields beyond 250. There is no error in the Salesforce org, no warning in Marketing Cloud Setup, and no log entry identifying which specific fields were dropped. The SDS data extension appears to sync normally — it simply has fewer columns than expected.

**When it occurs:** This most commonly surfaces when a heavily customized org enables SDS on the Contact or Lead object, both of which frequently accumulate hundreds of custom fields over time. It also occurs when a deployment adds new fields to a synced object, pushing it past the 250-field threshold. The sync continues to run — it does not fail — so the problem often goes undiscovered until a marketer reports that a personalization field in an email is blank.

**How to avoid:** Before enabling SDS on any object, export the object's field list from Salesforce (Setup > Object Manager > [Object] > Fields & Relationships) and count the fields. If the count exceeds or approaches 250, prioritize the fields actually used in Marketing Cloud sends and create a custom permission set or profile review to exclude unnecessary fields. Document the excluded fields explicitly in configuration notes. Re-audit after any deployment that adds fields to a synced object.

---

## Gotcha 2: Connector User Credential Changes Break Sync Without Alerting

**What happens:** MC Connect authenticates to Salesforce using a stored session for the connector user. If the connector user's password is reset, their profile is changed, their permission set is removed, or their user record is deactivated, all SDS sync jobs and triggered send executions fail. The Marketing Cloud Connect Configuration page in Salesforce can continue to show "Connected" status for an extended period (sometimes many hours) until the next scheduled sync attempt exposes the authentication failure.

**When it occurs:** Most commonly happens during org security hardening (forced password resets for all users, profile restructuring), user management projects (cleaning up "unused" accounts), or Salesforce release preparation. The connector user looks like an inactive system account to an admin not familiar with MC Connect, making it a common accidental deactivation target.

**How to avoid:** Add the connector user to a group or add a description that clearly flags it as MC Connect integration infrastructure. Exclude the connector user from org-wide password expiration policies. Establish a change-control process: any change to the connector user (profile, permission set, password) must include re-authentication in Marketing Cloud Setup > Salesforce Integration before the change is finalized. Monitor the MC Connect Configuration status page weekly.

---

## Gotcha 3: Scope Is Enforced at Send Time, Not at Sync Time

**What happens:** SDS replicates all records of the configured objects regardless of scope settings. A marketer reviewing the SDS data extension in Contact Builder will see all synced records. However, when a send is executed, Marketing Cloud filters the audience against the scope configured for the sending Business Unit. Records outside the BU's scope are silently excluded from the send — there is no error and no indication in the send report that records were filtered.

**When it occurs:** This is the primary cause of "mystery subscriber drops" in Enterprise 2.0 multi-BU Marketing Cloud accounts. It also occurs when a single-BU account later adds a second BU and forgets to configure scope on the new BU. The send appears to succeed at a lower-than-expected subscriber count, with no error to investigate.

**How to avoid:** After any scope configuration change (new BU, scope type change), run a test audience query in the affected BU and compare the count against a Salesforce report of the expected records. Do this before any production send. Document the scope configuration for each BU in the configuration log. Make subscriber count validation part of the pre-send checklist for every campaign.

---

## Gotcha 4: Contact Key Strategy Misalignment Creates Duplicate MC Contacts

**What happens:** MC Connect defaults to using the Salesforce Contact ID (18-character record ID) as the Marketing Cloud Subscriber Key. If the Marketing Cloud account was previously set up with email address as the Subscriber Key (a common early-stage setup), the two strategies conflict. When SDS syncs Contact records, Marketing Cloud creates new contact records using the SF Contact ID as the key, duplicating all contacts that already exist under their email address as key. This splits engagement history, creates duplicate subscription records, and can cause unsubscribes on one record to not propagate to the duplicate.

**When it occurs:** Most commonly surfaces in Marketing Cloud accounts that predate the MC Connect integration — the account was used for campaigns before the Salesforce connector was configured. Also occurs when a new Salesforce org is connected to an existing Marketing Cloud account that already has an established contact model.

**How to avoid:** Before enabling SDS sync, audit the existing Marketing Cloud contact model: what field is the current Subscriber Key? If it is email address, work with the Marketing Cloud architect to establish a migration plan before connecting SF. Do not enable SDS until the Contact Key strategy is aligned. After alignment, perform a full contact merge to eliminate duplicates before the first production send.

---

## Gotcha 5: Triggered Send Failures Are Not Surfaced in Salesforce

**What happens:** When a Salesforce Flow triggers an MC Connect triggered send, the Flow action call is fire-and-forget. If the triggered send fails in Marketing Cloud (send definition inactive, MC account suspended, API limit hit), the Flow does not throw an error and does not create a fault path. The Flow executes successfully from Salesforce's perspective; the email simply never goes out.

**When it occurs:** This affects any Triggered Send configuration where the Marketing Cloud Triggered Send Definition is paused, set to Inactive, or has hit its daily send limit. It also occurs when the Marketing Cloud account's IP is under review or the account's send access is suspended.

**How to avoid:** Set up Marketing Cloud send monitoring: use Automation Studio or Journey Builder's built-in send logging to capture triggered send completions and failures. Create a Marketing Cloud alert on the triggered send definition for failure notifications. Periodically reconcile Salesforce Flow execution logs against Marketing Cloud triggered send logs to confirm all trigger events produced a corresponding send record. Do not use triggered sends for truly critical transactional communications (e.g., password resets) without a fallback delivery path.

---

## Gotcha 6: SDS Does Not Sync Deleted Salesforce Records

**What happens:** When a Salesforce Contact or Lead is deleted (moved to the Recycle Bin), the SDS data extension in Marketing Cloud continues to hold the record. The record is not deleted from the SDS DE in the next sync. The deleted record can continue to appear in Marketing Cloud audiences, potentially receiving sends.

**When it occurs:** Affects any org with record deletion workflows — data cleanup processes, duplicate merges, GDPR/CCPA deletion requests. The GDPR/CCPA case is particularly serious: a data subject deletion request in Salesforce does not automatically propagate to Marketing Cloud via SDS.

**How to avoid:** For data subject deletion requests, Marketing Cloud must be treated as a separate system requiring its own deletion workflow. Use the Marketing Cloud Contact Delete process (Contact Builder > Contact Deletion) in addition to Salesforce record deletion. For routine record cleanup, schedule a SQL query activity in Automation Studio that cross-references the SDS DE against active Salesforce records and removes stale entries from the sendable DEs.
