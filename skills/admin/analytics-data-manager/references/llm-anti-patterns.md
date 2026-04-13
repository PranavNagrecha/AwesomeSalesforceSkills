# LLM Anti-Patterns — Analytics Data Manager

Common mistakes AI coding assistants make when generating or advising on Analytics Data Manager.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Connected Objects as Queryable Datasets and Generating SAQL Against Them

**What the LLM generates:**
```
q = load "Account";
q = filter q by 'Industry' == "Technology";
q = group q by 'OwnerId';
q = foreach q generate 'OwnerId', count() as 'Count';
```
The LLM instructs the practitioner to use the connected object name "Account" directly as a SAQL dataset reference in a lens or dashboard step, after the admin reports that Account was enabled for sync in Data Manager.

**Why it happens:** LLMs conflate the two layers of the CRM Analytics pipeline. Training data shows SAQL queries against dataset names, and LLMs generalize that any object visible in Data Manager is queryable by its API name. The staging-layer vs. analytics-layer distinction is rarely explicit in training data.

**Correct pattern:**
```
Connected objects (staging layer) → Recipe or Dataflow → Named Dataset (analytics layer) → SAQL

# SAQL must reference the dataset name defined in the recipe Output node, NOT the connected object name.
# Example: if the recipe outputs to dataset name "AccountDS", use:
q = load "AccountDS";
```

**Detection hint:** If the LLM output uses `load "<SalesforceObjectAPIName>"` in SAQL or references a connected object name in a dashboard step without first specifying a recipe/dataflow that creates a named output dataset, the anti-pattern is present.

---

## Anti-Pattern 2: Configuring Remote Connections Inside Dataflow JSON or Recipe Nodes

**What the LLM generates:**
```json
{
  "type": "sfdcDigest",
  "parameters": {
    "object": "QUOTA_TARGETS",
    "connection": "Snowflake",
    "host": "org.snowflakecomputing.com",
    "database": "SALES_DB",
    "credentials": "username/password"
  }
}
```
The LLM attempts to define a Snowflake (or other external database) connection inline inside a dataflow JSON node or recipe transformation step.

**Why it happens:** LLMs familiar with dataflow JSON structure generalize from `sfdcDigest` parameters and assume connection details can be embedded in the transformation layer. The separation of remote connection configuration (Data Manager UI) from recipe/dataflow consumption is not prominent in typical training text.

**Correct pattern:**
```
Step 1: Configure the Snowflake connection in Data Manager > Connect > Remote Connections UI.
Step 2: Test the connection in Data Manager before creating any recipe references.
Step 3: In Recipe Builder, add an Input node and select the remote connection's tables
        — they appear as available connected objects once the remote connection is active.
# Credentials and host configuration are NEVER embedded in dataflow JSON or recipe nodes.
```

**Detection hint:** Any LLM output that includes connection credentials, host names, or database parameters inside a dataflow JSON node or recipe node configuration is wrong. Remote connection parameters belong exclusively in the Data Manager UI.

---

## Anti-Pattern 3: Claiming Incremental Sync Detects All Record Changes Reliably

**What the LLM generates:** "Incremental sync in CRM Analytics automatically detects any record that has changed in Salesforce since the last sync run, so your connected objects will always reflect the current state of your data."

**Why it happens:** LLMs generalize from change detection concepts across platforms. The specific limitation that CRM Analytics incremental sync depends exclusively on `LastModifiedDate` — and that related-object changes do not update this field on parent objects — is a nuanced platform constraint that is underrepresented in training data.

**Correct pattern:**
```
Incremental sync detects records where LastModifiedDate > last_sync_timestamp.

LIMITATION: If a parent record's effective data changes because a child record changed
(e.g., Account roll-up summary updated because an Opportunity closed), the parent
Account's LastModifiedDate is NOT updated by Salesforce. Incremental sync will NOT
include this Account in the next sync batch.

FIX: Schedule periodic full syncs for objects with cross-object formula fields
or roll-up summary fields. This is the only reliable remediation.
```

**Detection hint:** If the LLM output states that incremental sync "captures all changes" or "always reflects current data" without qualifying the `LastModifiedDate` dependency and its formula-field limitation, this anti-pattern is present. Search output for "always up to date," "captures every change," or "real-time incremental."

---

## Anti-Pattern 4: Advising That Sync Configuration Is Done Inside Analytics Studio Instead of Data Manager

**What the LLM generates:** "To enable the Account object for sync, open Analytics Studio, go to the Dataflow editor, add an sfdcDigest node for Account, and set `incremental: true` in the node parameters."

**Why it happens:** Older Salesforce Analytics documentation (pre-Data Manager unification) described sync configuration as part of dataflow JSON. LLMs trained on older documentation or documentation that mixes pre- and post-Data Manager terminology conflate the two surfaces.

**Correct pattern:**
```
Data sync configuration lives in Data Manager, not in Analytics Studio or dataflow JSON.

Navigation: Analytics Studio > Data Manager > Connect tab > [connection name] > Edit Connection
- Enable/disable objects for sync from this UI
- Set sync mode (Full or Incremental) per object
- Set sync schedule per connection

Dataflow JSON sfdcDigest nodes reference already-enabled connected objects;
they do not configure which objects are synced or how frequently.
```

**Detection hint:** If the LLM output tells the user to configure sync inside a dataflow node (`sfdcDigest`, `edgeMart`, `digest`) rather than in the Data Manager Connect tab, the anti-pattern is present. Also flag any reference to `incremental: true` as a dataflow JSON property controlling sync mode.

---

## Anti-Pattern 5: Advising That Remote Connection Setup Requires No IP Allowlisting

**What the LLM generates:** "Create a new Remote Connection in Data Manager, enter your Snowflake credentials, and click Test Connection. It should connect immediately."

**Why it happens:** LLMs default to the happy path of credential entry without surfacing the network layer requirement. IP allowlisting is a security infrastructure step that is external to Salesforce and is often omitted from documentation summaries used in training.

**Correct pattern:**
```
Before testing a remote connection to Snowflake, BigQuery, Redshift, or other external databases:

1. Obtain the list of CRM Analytics egress IP addresses for your org's instance.
   (Available in Salesforce Help: search "IP Addresses to Allowlist for CRM Analytics")
2. Add these IP ranges to the network policy or firewall allowlist of the external database:
   - Snowflake: add to Network Policy in Snowflake admin console
   - BigQuery: add to VPC Service Controls or project firewall rules
   - Redshift: add to the associated VPC security group inbound rules
3. Only after allowlisting is confirmed should you test the connection in Data Manager.

Without allowlisting, the connection test will time out or return an authentication error
that misleadingly suggests credential problems rather than network policy problems.
```

**Detection hint:** If the LLM output describes remote connection setup without mentioning IP allowlisting, egress IP ranges, or network policy configuration, it is incomplete and likely to lead the practitioner to a failed connection test that is difficult to diagnose. Search for "allowlist," "network policy," or "firewall" — their absence in a remote connection setup guide is a signal.

---

## Anti-Pattern 6: Assuming Data Manager Alerts on Sync Failures Automatically

**What the LLM generates:** "If your data sync fails, Salesforce will send you an email notification so you can investigate."

**Why it happens:** Many Salesforce platform tools (Process Builder failures, Apex exception emails) do automatically alert system admins. LLMs generalize this pattern to Data Manager, which does not have automatic failure alerting enabled by default.

**Correct pattern:**
```
Data Manager does NOT send automatic email alerts on sync failure unless
monitoring notifications have been explicitly configured.

To configure alerts:
1. In Data Manager, navigate to Monitor tab > Notification Settings.
2. Add email recipients and select failure conditions to trigger notifications.
3. Test by reviewing Monitor > Run History after the next sync to confirm
   the notification fires on a simulated or real failure.

Without explicit notification configuration, sync failures will accumulate silently
in the Monitor tab until an admin manually checks the run history.
```

**Detection hint:** If the LLM output asserts that sync failures are automatically communicated without noting the requirement to configure monitoring notifications explicitly, the claim is incorrect. Search output for "automatically notified," "email alert," or "Salesforce will alert."
