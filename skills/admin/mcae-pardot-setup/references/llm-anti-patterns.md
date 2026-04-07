# LLM Anti-Patterns — MCAE (Pardot) Setup

Common mistakes AI coding assistants make when generating or advising on MCAE (Pardot) setup.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating "Connector Is Created" as Equivalent to "Connector Is Active"

**What the LLM generates:** Instructions that say "a Salesforce connector is automatically set up when your business unit is provisioned — you can start syncing immediately." The LLM assumes provisioning = activation.

**Why it happens:** Training data likely includes Salesforce documentation describing the auto-creation of the connector, but the "Paused state" nuance is either underrepresented or the LLM elides it as a minor detail. The LLM pattern-matches to "setup complete" without capturing the manual resume step.

**Correct pattern:**

```text
A Salesforce v2 connector is auto-created when a new MCAE business unit is
provisioned, but it starts in a PAUSED state. No sync occurs until an MCAE
admin explicitly navigates to Account Engagement Settings > Connectors,
verifies the connector, and clicks Resume.

Verification step: after resuming, confirm the connector status reads "Active"
and test by creating a Lead in Salesforce and waiting 2–5 minutes for the
matching prospect to appear in MCAE.
```

**Detection hint:** Look for phrases like "automatically syncs," "sync begins after provisioning," or "connector is ready" without any mention of verifying or resuming the connector. Flag these as missing the Paused-state activation step.

---

## Anti-Pattern 2: Confusing MCAE (Account Engagement) with Marketing Cloud Engagement

**What the LLM generates:** Setup instructions that reference Journey Builder, Email Studio, Content Builder, Marketing Cloud Connect, or the Marketing Cloud data model (Contact Builder, Data Extensions) when the user asked about MCAE / Pardot / Account Engagement.

**Why it happens:** Both products share the "Marketing Cloud" brand prefix. LLMs frequently conflate "Marketing Cloud Account Engagement" (formerly Pardot, a B2B MAP) with "Marketing Cloud Engagement" (the email studio / journeys platform). They are architecturally distinct products with different connectors, different data models, different admin UIs, and different license types.

**Correct pattern:**

```text
Marketing Cloud Account Engagement (MCAE) / Pardot:
- Syncs via the Salesforce v2 connector (configured in Account Engagement Settings)
- Data model: Prospects, Lists, Campaigns, Automation Rules
- Admin UI: Account Engagement Lightning App (Salesforce Lightning tab)
- Users managed via Salesforce User Sync or MCAE user admin UI
- B2B marketing automation; no Journey Builder

Marketing Cloud Engagement:
- Connects via Marketing Cloud Connect (a separate managed package)
- Data model: Contacts, Data Extensions, Sendable Data Extensions
- Admin UI: Marketing Cloud app (separate login, mc.exacttarget.com)
- Users managed in Marketing Cloud user admin
- B2C / B2B email automation with Journey Builder
```

**Detection hint:** Watch for "Journey Builder," "Email Studio," "Data Extension," "Marketing Cloud Connect," "Synchronized Data Extension," or "Contact Builder" appearing in response to an MCAE/Pardot setup question. These are Marketing Cloud Engagement terms, not MCAE terms.

---

## Anti-Pattern 3: Recommending View All Data / Modify All Data on a Named Person's Account

**What the LLM generates:** Instructions like "give your Pardot connector user View All Data and Modify All Data permissions — you can use the existing admin account or any Salesforce user." The LLM correctly identifies the required permissions but fails to flag the service account requirement.

**Why it happens:** LLMs often focus on the permission list without modeling the operational risks of attaching org-wide data permissions to a named person's account. Operational risk (user departure, deactivation) is an inferential step that many LLMs skip in favor of the simpler "here's the permission" answer.

**Correct pattern:**

```text
The connector user MUST be a dedicated service account, not a named person's
Salesforce login. Required setup:

1. Create a Salesforce user record: e.g., mcae.connector@yourcompany.com
2. Assign a profile with: Marketing User (checkbox), View All Data,
   Modify All Data, API Enabled
3. Ensure this account is owned by the Salesforce admin team — not
   assigned to any individual's Salesforce license seat as their primary user
4. Document the account in the org's service account register with
   the approval date and owner

Reason: If the connector user is a named person who leaves the company,
Salesforce deactivation immediately breaks all MCAE sync. A service account
with a generic email and admin-team ownership avoids this failure mode.
```

**Detection hint:** Any instructions that say "use an existing Salesforce user" or "give your Salesforce admin user these permissions" for the connector user should be flagged. The correct answer always specifies a dedicated service account.

---

## Anti-Pattern 4: Recommending Enabling User Sync Without Pre-Migration Verification Steps

**What the LLM generates:** "To simplify user management, enable Salesforce User Sync in Account Engagement Settings. Map your Salesforce profiles to MCAE roles and turn it on — this will auto-provision users going forward." The LLM omits verification that existing MCAE users have matching Salesforce records, and does not mention irreversibility.

**Why it happens:** User Sync is genuinely a simplification for ongoing management. The LLM is optimizing for the "happy path" (new org, no existing users) and does not model the migration path where existing MCAE users may become orphaned. The irreversibility constraint is often absent from general "how to enable User Sync" documentation snippets that LLMs train on.

**Correct pattern:**

```text
Before enabling Salesforce User Sync:

1. Export all current MCAE users (Account Engagement Settings > Users).
2. For each MCAE user, confirm there is an active Salesforce user record
   with the same email address assigned to a profile that maps to an MCAE role.
3. For any MCAE user without a matching Salesforce record: either create
   the Salesforce record or deactivate the MCAE user before proceeding.
4. User Sync cannot be disabled through the UI after enablement.
   Rolling back requires a Salesforce Support case.
5. Perform enablement during a low-activity period with marketing ops
   and IT teams available to validate the result immediately.

Only after steps 1–4 are complete should you click "Enable Salesforce User Sync."
```

**Detection hint:** Look for User Sync enablement instructions that skip the "verify existing user match" step, or that do not mention irreversibility. Any answer that says "just enable it" without a pre-migration verification checklist is incomplete.

---

## Anti-Pattern 5: Claiming Field Sync Rules Default to "Use Most Recently Updated" for All Fields

**What the LLM generates:** "By default, MCAE uses the most recently updated value for all synced fields, so you don't need to configure conflict resolution." This understates the complexity and leads admins to skip field sync rule configuration.

**Why it happens:** "Use Most Recently Updated" is often cited in documentation as a common recommendation, and LLMs overgeneralize this into "it's the default." The actual defaults vary by field type, and some fields (especially CRM-authoritative system fields) may have different defaults or may need explicit override to avoid MCAE overwriting CRM data.

**Correct pattern:**

```text
Field sync rules must be explicitly reviewed and configured for each synced field.
Do not assume a safe default applies universally.

Recommended rule assignments:
- CRM-authoritative fields (Owner, Account lookup, Record Type, CRM IDs):
  → "Use Salesforce's Value" — CRM is the master for these
- MCAE-authoritative fields (Marketing Opt-Out, MCAE Score, MCAE Grade):
  → "Use Pardot's Value" — MCAE is the master for these
- Shared editable fields (First Name, Last Name, Company, Phone, Job Title):
  → "Use Most Recently Updated" — safest for fields either side can edit

Review the full field mapping in Account Engagement Settings > Connectors >
[Connector] > Field Mappings to confirm and set each rule explicitly.
```

**Detection hint:** Any statement like "the default sync rule handles conflicts automatically" or "you don't need to configure sync rules" should be flagged. Each field's sync rule is a deliberate data ownership decision that cannot be safely defaulted without business input.

---

## Anti-Pattern 6: Advising That Campaign Engagement Data Is Retroactively Written After Mapping Is Configured

**What the LLM generates:** "Don't worry if you didn't set up the Campaign Member Status mapping before your first send — MCAE will backfill the engagement data to Salesforce campaigns once you configure the mapping."

**Why it happens:** LLMs sometimes analogize to other Salesforce features that support retroactive data population (e.g., formula field recalculation, roll-up summaries). MCAE campaign sync does not work this way — engagement events that occurred before the mapping was configured are not retroactively written as Campaign Member records.

**Correct pattern:**

```text
Campaign Member records are written by MCAE at the time of engagement.
If Campaign Member Status mapping was not configured before a send:
- Those engagement events (opens, clicks, form fills) do NOT generate
  Campaign Member records in Salesforce retroactively.
- The data is not lost in MCAE (it exists as prospect activity), but it
  will not appear as Campaign Member records in Salesforce reports.

To recover from this situation:
1. Export prospect activities from MCAE for the affected campaign.
2. Manually create Campaign Member records in Salesforce via data load
   using the exported activity data as the source.

Prevention: Add "Salesforce campaign linked and Member Status values
configured" to every campaign pre-launch checklist.
```

**Detection hint:** Any claim that MCAE "backfills," "retroactively syncs," or "will catch up" on campaign engagement data after the campaign connector mapping is added should be flagged as incorrect.
