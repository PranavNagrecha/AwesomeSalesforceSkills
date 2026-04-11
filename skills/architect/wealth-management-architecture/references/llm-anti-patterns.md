# LLM Anti-Patterns — Wealth Management Architecture

Common mistakes AI coding assistants make when generating or advising on Wealth Management Architecture.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming All FSC Features Are Active After License Assignment

**What the LLM generates:** Advice or code that references `enableWealthManagementAIPref`-gated components (AI insights, portfolio analysis widgets) without first checking whether the flag is deployed. Or instructions that say "go to Setup > Financial Services > Wealth Management AI to enable it" when no such Setup path exists.

**Why it happens:** LLMs pattern-match to standard Salesforce feature activation flows where most features are enabled via Setup UI toggles. They also treat FSC as a monolithic product where all features are available after license assignment, rather than a composable platform where each capability requires explicit IndustriesSettings deployment.

**Correct pattern:**

```bash
# Step 1: Retrieve current IndustriesSettings to check flag state
sf project retrieve start --metadata "IndustriesSettings" --target-org <alias>

# Step 2: Check the retrieved XML for enableWealthManagementAIPref
# Step 3: If not set to true, add it and redeploy
```

```xml
<IndustriesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableWealthManagementAIPref>true</enableWealthManagementAIPref>
</IndustriesSettings>
```

**Detection hint:** Look for advice that skips IndustriesSettings metadata and jumps directly to "configure the component" or "enable in Setup." If the metadata deployment step is absent, the guidance is incomplete.

---

## Anti-Pattern 2: Treating Compliant Data Sharing as a Single Global Toggle

**What the LLM generates:** Instructions that say "enable Compliant Data Sharing in FSC settings" as a single one-time action, without mentioning that it must be enabled per object type, and without mentioning the sharing recalculation requirement for existing records.

**Why it happens:** LLMs generalize from other Salesforce data visibility features (like org-wide defaults or territory management) that have a global on/off switch. They also lack awareness that activating CDS without running the recalculation batch creates an immediate data visibility blackout.

**Correct pattern:**

```
Compliant Data Sharing must be enabled independently for each object:
- Account
- Opportunity
- Interaction
- Interaction Summary
- Each custom object requiring access control

For each object activation sequence:
1. Enable CDS on the object in Setup > Compliant Data Sharing > Object Activation
2. Immediately queue sharing recalculation batch for that object
3. Confirm Share record count before ending maintenance window
```

**Detection hint:** If the advice says "enable CDS" without specifying which object types and without including a sharing recalculation step, it is incomplete and will cause production data visibility loss.

---

## Anti-Pattern 3: Using REST Composite API for Custodian Data Loads

**What the LLM generates:** Code that builds `FinServ__FinancialAccountTransaction__c` records using the REST Composite API or standard `insert` DML in a loop, treating the custodian feed as a normal record creation task.

**Why it happens:** REST Composite API is well-documented and familiar. LLMs default to it for record creation tasks because it appears in training data far more frequently than Bulk API 2.0 ingest job patterns. The failure mode (governor limit exhaustion at scale) is not visible in small test scenarios.

**Correct pattern:**

```python
# Use Bulk API 2.0 ingest for custodian feeds
import requests

# Create ingest job
job_response = requests.post(
    f"{instance_url}/services/data/v63.0/jobs/ingest/",
    headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
    json={
        "object": "FinServ__FinancialAccountTransaction__c",
        "operation": "upsert",
        "externalIdFieldName": "FinServ__ExternalId__c",
        "contentType": "CSV"
    }
)
job_id = job_response.json()["id"]
# Upload CSV batches, close job, poll for completion
```

**Detection hint:** Any code that uses `requests.post` to `/composite/` or calls `insert` in a loop for custodian transaction records is the wrong pattern for production-scale feeds.

---

## Anti-Pattern 4: Scoping Scoring Framework Without Verifying CRM Plus License

**What the LLM generates:** Architecture recommendations that include advisor analytics dashboards with client health scores, referral opportunity scores, and engagement scores — referencing `FinServ__ScoringRecord__c` or the Scoring Framework configuration objects — without flagging the CRM Plus license dependency.

**Why it happens:** LLMs describe FSC capability sets from documentation that lists features without consistently surfacing license-tier requirements. The Scoring Framework limitation is a commercial constraint, not a technical one, and commercial constraints are underrepresented in technical training data.

**Correct pattern:**

```
Before scoping advisor analytics with scoring:
1. Verify User Licenses in Setup > Company Information
2. Confirm "CRM Plus" appears in the license list
3. If CRM Plus is absent, the Scoring Framework objects do not exist
   and any Flow/Apex referencing them will fail at runtime

SOQL to verify:
SELECT Name FROM UserLicense WHERE Name LIKE '%CRM Plus%'
```

**Detection hint:** Any architecture recommendation that includes scoring-based advisor analytics without a CRM Plus license verification step is incomplete and risks a blocked deployment.

---

## Anti-Pattern 5: Assuming Bulk API 2.0 Ingest Triggers FSC Rollup Recalculation

**What the LLM generates:** Integration design that loads transaction records via Bulk API 2.0 and then immediately reads the parent `FinServ__FinancialAccount__c` Net Worth field, assuming it has been updated by the load. Or runbooks that do not include a post-load rollup recalculation step.

**Why it happens:** LLMs correctly understand that DML-based record inserts trigger Apex triggers and rollup rules. They incorrectly extrapolate this to Bulk API 2.0, which bypasses trigger execution. The distinction is technically accurate but counterintuitive for practitioners who expect consistent platform behavior regardless of the write path.

**Correct pattern:**

```apex
// After Bulk API 2.0 ingest job completes, explicitly trigger rollup recalculation
// Option 1: Fire a Platform Event that a rollup trigger subscribes to
EventBus.publish(new FinServ__RollupRecalculationEvent__e(
    ObjectApiName__c = 'FinServ__FinancialAccount__c'
));

// Option 2: Schedule a batch job that touches the parent records to force rollup
// Option 3: Use FSC invocable rollup recalculation action from a scheduled Flow
```

**Detection hint:** Any integration design that loads records via Bulk API 2.0 and does not include an explicit post-load rollup recalculation step will produce stale portfolio totals in advisor dashboards.

---

## Anti-Pattern 6: Deploying IndustriesSettings Without Retrieving First

**What the LLM generates:** A deploy command that pushes a new `Industries.settings-meta.xml` with only the target flags set, without first retrieving the current state of the file. This overwrites all currently active IndustriesSettings flags with only what is in the new file, potentially disabling features that were already active in production.

**Why it happens:** LLMs generate deployment steps from generic Metadata API patterns where deploying a new file is safe. They do not account for the fact that `IndustriesSettings` is a singleton — deploying a partial file replaces the entire singleton, setting all unlisted flags to their default (often `false`).

**Correct pattern:**

```bash
# Always retrieve before deploying IndustriesSettings
sf project retrieve start --metadata "IndustriesSettings" --target-org <alias>

# Edit the retrieved file to add only the new flags
# Then deploy the complete file
sf project deploy start \
  --source-dir force-app/main/default/settings/Industries.settings-meta.xml \
  --target-org <alias>
```

**Detection hint:** Any deployment instruction for `IndustriesSettings` that does not include a retrieve step first is incomplete and risks disabling existing FSC features.
