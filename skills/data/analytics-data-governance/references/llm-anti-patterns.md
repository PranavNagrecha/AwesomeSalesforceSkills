# LLM Anti-Patterns — Analytics Data Governance

Common mistakes AI coding assistants make when generating or advising on Analytics Data Governance in CRM Analytics.
These patterns help the consuming agent self-check its own output.

---

## Anti-Pattern 1: Assuming Salesforce Data Classification Propagates Automatically Into CRM Analytics Datasets

**What the LLM generates:**
> "Since you've already classified your Contact fields with Data Classification (SSN__c as Restricted, Salary__c as Confidential), those classifications will carry over when those fields are synced into your CRM Analytics dataset. You can view the classification in Data Manager under the dataset schema."

**Why it happens:** LLMs trained on Salesforce documentation conflate the CRM layer (where Data Classification is a real feature on field metadata) with CRM Analytics (a separate analytics engine with its own metadata model). The assumption that Salesforce features "propagate" across product boundaries is a common generalization failure. There is no documentation in Salesforce's official sources stating that this propagation occurs — the LLM infers it from analogy.

**Correct pattern:**
```
Salesforce Data Classification (field Sensitivity Level, Data Category,
Compliance Categorization) applies to sObject fields in the CRM layer only.

When those fields are ingested into CRM Analytics — via Dataflow, Recipe,
or External Data API — the resulting dataset columns carry NO inherited
classification metadata. There is no column-tagging system in CRM Analytics
that reflects source-field classification.

Required action: maintain a separate governance register mapping
dataset columns to source field classifications. Re-apply access
controls at the dataset layer (column exclusion, row-level predicates).
```

**Detection hint:** Any response that states classification "carries over," "propagates," "is inherited," or "is visible in Data Manager" for dataset columns should be flagged. Also flag references to a CRM Analytics Data Classification UI that does not exist.

---

## Anti-Pattern 2: Recommending Setup Audit Trail or Login History as a CRM Analytics Access Audit Mechanism

**What the LLM generates:**
> "To audit who accessed your CRM Analytics datasets, go to Setup > Audit Trail. This captures all user actions including analytics dashboard views. You can also check Login History to see which users were active."

**Why it happens:** Setup Audit Trail is a well-known Salesforce feature for capturing admin configuration changes. LLMs correctly know it exists but incorrectly generalize its scope to include runtime analytics data access. Login History records authentication events, not resource-level access. Both are frequently cited by LLMs as general-purpose audit tools when asked about Salesforce access logging.

**Correct pattern:**
```
Setup Audit Trail captures Salesforce org configuration changes
(metadata, settings, permission changes). It does NOT capture
CRM Analytics dataset access events (dashboard views, dataset queries).

Login History captures user authentication events. It does NOT
capture which CRM Analytics resources a user accessed.

CRM Analytics dataset access audit requires the Event Monitoring
add-on (license-gated). The relevant event types are:
- WaveInteraction: dashboard views, dataset queries
- WaveChange: dataset/dataflow/permission modifications

Access these via EventLogFile sObject (hourly CSV) or
WaveInteractionLog / WaveChangeLog ELO objects (Summer '24+,
~15 min latency).
```

**Detection hint:** Any response recommending Setup Audit Trail or Login History for CRM Analytics data access auditing is wrong. Flag and replace with Event Monitoring guidance.

---

## Anti-Pattern 3: Claiming Dataset Deletion Satisfies a Complete Erasure Requirement

**What the LLM generates:**
> "To comply with the GDPR right-to-erasure request, delete the dataset from Data Manager. Once deleted, the data is removed from CRM Analytics. You can confirm deletion by verifying the dataset no longer appears in the dataset list."

**Why it happens:** LLMs model dataset deletion as a complete operation based on the UI feedback (the dataset disappears from the list). They do not account for the CRM Analytics version history system, which is a non-obvious implementation detail not prominently documented in general Salesforce help content.

**Correct pattern:**
```
Deleting a CRM Analytics dataset removes the current version reference
but does NOT delete stored dataset versions.

Versions persist and remain accessible via:
GET /services/data/{version}/wave/datasets/{id}/versions

For a complete erasure:
1. List all versions via the versions endpoint
2. DELETE each version individually:
   DELETE /services/data/{version}/wave/datasets/{dataset_id}/versions/{version_id}
3. DELETE the dataset itself
4. Confirm zero versions remain by re-querying the versions endpoint

Include version count and deletion confirmation in the erasure record.
```

**Detection hint:** Any erasure guidance that mentions only deleting the dataset without referencing dataset versions is incomplete. Flag any response that says deletion is "confirmed" by the dataset no longer appearing in the UI.

---

## Anti-Pattern 4: Recommending Event Log Objects Without Checking Release and License Gating

**What the LLM generates:**
> "Use this SOQL query to get real-time CRM Analytics access logs:
> SELECT UserId, QueriedEntities, Timestamp FROM WaveInteractionLog WHERE Timestamp >= 2026-01-01T00:00:00Z"

**Why it happens:** Event Log Objects were introduced in Summer '24 and are well-documented in recent Salesforce release notes. LLMs trained on recent documentation default to recommending ELO because it is simpler (no CSV download, real-time) without checking the gating conditions. Many production orgs are on older releases or do not have the Event Monitoring add-on.

**Correct pattern:**
```
WaveInteractionLog and WaveChangeLog are Event Log Object (ELO) types
that require:
1. Org release: Summer '24 or later
2. License: Event Monitoring add-on (Shield or standalone)

Without both conditions, the SOQL query returns an error:
"Object type 'WaveInteractionLog' is not supported"

Before recommending ELOs, verify:
- Event Monitoring license: Setup > Company Information > Feature Licenses
- Org release: SELECT SystemModstamp FROM Organization (or check Setup > About)

Fallback for older orgs / without ELO:
SELECT Id, EventType, LogDate FROM EventLogFile
WHERE EventType IN ('WaveInteraction', 'WaveChange')
ORDER BY LogDate DESC
```

**Detection hint:** Any ELO query recommendation without a prerequisite check for the Event Monitoring license and Summer '24+ release should be flagged.

---

## Anti-Pattern 5: Using /wave/dataflows Endpoint Output Alone to Build a Complete Dataset Lineage Map

**What the LLM generates:**
> "To trace dataset lineage, call GET /services/data/v63.0/wave/dataflows. This returns all dataflows and their output datasets, giving you a complete picture of where each dataset comes from."

**Why it happens:** The `/wave/dataflows` endpoint is well-documented and the LLM correctly identifies it as relevant to lineage. However, the LLM ignores that CRM Analytics also has Recipes (a separate asset type with its own API endpoint and different schema), External Data API uploads (which have no producer metadata at all), and the need to parse the internal `.wdf` node graph to extract output dataset names from dataflows.

**Correct pattern:**
```
A complete CRM Analytics dataset lineage map requires querying
BOTH asset types:

1. Recipes: GET /wave/recipes
   → Parse recipe.outputDatasets[] for output dataset names

2. Dataflows: GET /wave/dataflows → GET /wave/dataflows/{id}
   → Parse definition.nodes for nodes where action is 'sfdcRegister'
     or parameters.dataset.name is present
   → Top-level /wave/dataflows list does NOT include node details

3. External Data API uploads: no producer metadata available via API.
   Track these separately in a governance register.

Orgs with a mix of recipes and dataflows (common in migrated orgs)
require both queries. Using only /wave/dataflows will produce an
incomplete lineage map that misses all recipe-produced datasets.
```

**Detection hint:** Any lineage recommendation that references only `/wave/dataflows` without also referencing `/wave/recipes` should be flagged. Also flag any claim that the top-level dataflows list response includes output dataset names (it does not — you must fetch each dataflow individually to parse the node graph).

---

## Anti-Pattern 6: Treating a Scheduled Recipe as a Guaranteed Retention Control

**What the LLM generates:**
> "Configure a daily recipe with a date filter to keep only the last 90 days of data. Schedule it to run nightly. This will automatically enforce your retention policy without any additional tooling."

**Why it happens:** The recipe approach is technically valid and is the recommended pattern. The LLM correctly describes the setup but omits the critical operational dependency: the retention guarantee is only as reliable as the recipe's successful execution. LLMs tend to describe features in their success-path mode without accounting for failure modes.

**Correct pattern:**
```
A scheduled recipe with a date filter enforces retention ONLY when
the recipe succeeds. A failed recipe run:
- Does NOT roll back the current dataset to a compliant state
- Does NOT delete out-of-window rows from the existing dataset version
- Does NOT trigger an automatic alert by default

Required compensating controls:
1. Configure recipe failure notifications (CRM Analytics admin alerts
   or REST API job status polling)
2. Treat a failed data aging recipe run as a retention SLA breach
3. Add a post-run assertion recipe or script to validate max(date_column)
   falls within the retention window
4. Document the monitoring and escalation process in the retention runbook

"Set and forget" scheduled recipe retention is not an acceptable
compliance architecture without these controls.
```

**Detection hint:** Any retention guidance that recommends only setting up the recipe schedule without addressing failure monitoring and SLA breach response should be flagged.
