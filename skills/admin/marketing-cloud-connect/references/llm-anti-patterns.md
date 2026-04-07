# LLM Anti-Patterns — Marketing Cloud Connect

Common mistakes AI coding assistants make when generating or advising on Marketing Cloud Connect.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing MC Connect with MCAE (Pardot) Connector

**What the LLM generates:** Advice that mixes Marketing Cloud Connect configuration (managed package, synchronized data sources, connector user) with Marketing Cloud Account Engagement (MCAE/Pardot) setup steps. For example, suggesting "enable the Pardot Connector" when the user has a Marketing Cloud account, or referencing "Pardot campaigns" when the user is asking about MC Connect tracking sync.

**Why it happens:** Both products have "Marketing Cloud" in their name and both integrate with Salesforce CRM. Training data conflates them because many tutorials discuss both. LLMs also pattern-match on "marketing automation + Salesforce" and may blend the two setup paths.

**Correct pattern:**
```
MC Connect (this skill):
- Product: Marketing Cloud Engagement (Email Studio, Journey Builder, etc.)
- Integration: Managed package "Salesforce Marketing Cloud" (namespace: et4ae5)
- Connector: connector user + synchronized data sources

MCAE / Pardot (different skill):
- Product: Marketing Cloud Account Engagement
- Integration: Pardot connector, Salesforce-Pardot Connector user
- No "synchronized data sources" — uses Salesforce Connector sync instead
```

**Detection hint:** If the response mentions "Pardot", "pi.pardot.com", "Engagement Studio", or "Pardot connector" in the context of MC Connect setup, it is mixing the two products.

---

## Anti-Pattern 2: Advising Users to Send Directly to a Synchronized Data Extension

**What the LLM generates:** Instructions like "go to Email Studio, select the Contact SDS data extension as your send audience, and send." Or suggestions to mark the SDS DE as sendable by setting the `IsSendable` property in the DE configuration.

**Why it happens:** LLMs understand that SDS creates data extensions in Marketing Cloud, and pattern-match on "data extension → send audience." They are unaware that SDS DEs are system-managed as read-only and lack the subscriber relationship configuration required for direct sends.

**Correct pattern:**
```sql
-- Create a sendable DE via SQL query activity in Automation Studio:
SELECT
    c.ContactID AS SubscriberKey,
    c.Email,
    c.FirstName,
    c.LastName
FROM Contact_Salesforce c   -- SDS DE
WHERE c.Email IS NOT NULL
  AND c.HasOptedOutOfEmail = false

-- Write to a sendable target DE with SubscriberKey as the send relationship field.
-- Use this target DE as the send audience, not the SDS DE directly.
```

**Detection hint:** Any instruction that tells the user to select an SDS data extension (names ending in `_Salesforce` or prefixed with the SF org ID) directly as a send audience is incorrect.

---

## Anti-Pattern 3: Suggesting the Connector User Can Be a Community or Experience Cloud User

**What the LLM generates:** Suggestions like "create an Experience Cloud or Community user for the connector to reduce license costs" or "a portal user with API access will work as the connector user."

**Why it happens:** LLMs associate "integration users" with reduced-license options that Salesforce offers. Community/Experience Cloud licenses are cheaper, and LLMs may suggest them as a cost-saving measure without knowing that MC Connect specifically requires a standard internal Salesforce user.

**Correct pattern:**
```
Connector user requirements:
- User Type: Standard (internal Salesforce user)
- License: Salesforce (full platform license)
- NOT: Community User, External User, Partner Community User, Portal User
- Profile: Standard profile with API Enabled = true
- Permission Set: "Marketing Cloud" permission set (from MC Connect package)
```

**Detection hint:** Any suggestion of "community user", "experience cloud user", "portal user", "external user", or "reduced license" for the connector user is incorrect.

---

## Anti-Pattern 4: Treating Scope Configuration as a One-Time Setup Task

**What the LLM generates:** Instructions that set up scope during initial connection and do not mention ongoing scope maintenance. For example: "Configure scope to Org-Wide during setup, and you're done" — with no mention that adding a new Business Unit, refreshing a sandbox, or restructuring the org hierarchy requires scope re-evaluation.

**Why it happens:** LLMs describe scope as an initial configuration step (which it is), but miss that scope is independently configured per Business Unit in multi-BU accounts, and that the scope setting in Marketing Cloud and in the Salesforce org must remain aligned. This is a stateful operational concern, not a one-time setup.

**Correct pattern:**
```
Scope maintenance checklist (apply after any of these events):
- Adding a new Marketing Cloud Business Unit
- Refreshing a Salesforce sandbox connected to a MC sandbox
- Restructuring Salesforce territories or org hierarchy
- Migrating to a new Salesforce org
- Changing the connected MC account

Steps:
1. In each affected MC Business Unit: Setup > Salesforce Integration > verify scope
2. In Salesforce org: MC Connect > Configuration > verify scope
3. Run a test audience query in each BU and compare against SF record count
4. Document scope settings in configuration log with last-verified date
```

**Detection hint:** Any advice about scope that does not mention multi-BU considerations or ongoing maintenance after org/BU changes is incomplete.

---

## Anti-Pattern 5: Assuming Triggered Send Failures Are Visible in Salesforce

**What the LLM generates:** Debugging instructions that start with "check the Salesforce Flow error logs to see why the triggered send failed" — implying that MC-side failures will surface as Salesforce errors.

**Why it happens:** LLMs correctly understand that Salesforce Flows have fault paths and error handling. They assume the MC Connect action in Flow behaves like other Salesforce callout actions that propagate errors back to the calling Flow. In reality, the MC Connect triggered send action is fire-and-forget from the Flow's perspective.

**Correct pattern:**
```
Triggered send failure diagnosis path:

1. Salesforce side — confirm the Flow executed:
   Setup > Flows > [Flow name] > Debug > check execution history
   If Flow shows success: the Salesforce side completed; failure is in MC.

2. Marketing Cloud side — check triggered send logs:
   Marketing Cloud > Email Studio > Interactions > Triggered Sends
   > [Triggered Send Definition] > Activity tab
   Look for failed send records, error codes, or missing entries.

3. Common MC-side failure causes:
   - Triggered Send Definition is Paused or Inactive
   - Subscriber is globally unsubscribed or on suppression list (for commercial sends)
   - MC account send access suspended or IP under review
   - API rate limit hit

4. Set up MC-side alerting:
   Marketing Cloud > Setup > Notification Settings
   Configure send failure notifications to the marketing ops team.
```

**Detection hint:** Any debugging advice that relies solely on Salesforce logs and does not mention Marketing Cloud send logs is missing the primary failure investigation surface.

---

## Anti-Pattern 6: Recommending Manual Editing of SDS Data Extensions

**What the LLM generates:** Suggestions to manually add, edit, or delete rows in an SDS data extension in Marketing Cloud to fix data issues (e.g., "just delete the stale record from the SDS DE in Contact Builder").

**Why it happens:** LLMs understand that Marketing Cloud data extensions can be edited through the UI or via AMPscript/SSJS, and apply this general knowledge to SDS DEs without recognizing that SDS DEs are system-managed and overwritten on each sync cycle.

**Correct pattern:**
```
SDS DEs are system-managed. Manual edits will be overwritten on the next
15-minute sync cycle.

To fix data issues in SDS DEs:
- Incorrect or stale data → fix the source Salesforce record; wait for sync
- Missing fields → check the 250-field limit; remove unused fields from sync config
- Deleted records still appearing → use MC Contact Delete for GDPR/CCPA;
  for operational cleanup, filter them out in downstream SQL queries
- Schema mismatch → re-configure the synced object's field selection in
  MC Connect > Synchronized Data Sources, then refresh sync

Never manually modify SDS DE contents. Build all business logic in
downstream SQL query activities or Contact Builder relationships.
```

**Detection hint:** Any instruction to use Contact Builder UI, Data Extension editor, or AMPscript to modify rows in a data extension whose name corresponds to a Salesforce object (e.g., `Contact_Salesforce`, `Lead_Salesforce`) is incorrect.
