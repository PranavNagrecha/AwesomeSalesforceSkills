# LLM Anti-Patterns — FSC Deployment Patterns

Common mistakes AI coding assistants make when generating or advising on FSC Deployment Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Single-Wave FSC Deployment Without Prerequisite Checks

**What the LLM generates:** A deployment command or script that deploys all FSC metadata components in a single batch — record types, IndustriesSettings, Participant Role custom metadata, and sharing rules — without any pre-flight checks for Person Account enablement or OWD settings.

```bash
# LLM-generated (wrong)
sf project deploy start \
  --source-dir force-app/main/default \
  --target-org production \
  --test-level RunLocalTests
```

**Why it happens:** LLMs are trained on generic Salesforce deployment patterns where a single-wave deploy is the standard. FSC-specific prerequisites are not prominent in generic DevOps documentation, so the LLM applies the general pattern to an FSC context without accounting for FSC's hard sequential dependencies.

**Correct pattern:**

```bash
# Step 0: pre-flight — confirm Person Accounts enabled
sf data query \
  --query "SELECT Id FROM RecordType WHERE SObjectType='Account' AND DeveloperName='PersonAccount'" \
  --target-org production

# Step 1: deploy record types only
sf project deploy start \
  --metadata "RecordType" \
  --target-org production \
  --test-level RunSpecifiedTests --tests FSCRecordTypeTests

# Step 2: deploy IndustriesSettings only after record types confirmed
sf project deploy start \
  --metadata "IndustriesSettings" \
  --target-org production

# Step 3: deploy Participant Role custom metadata
sf project deploy start \
  --metadata "ParticipantRole" \
  --target-org production
```

**Detection hint:** Any FSC deployment advice that uses `--source-dir` with the full source directory in a single command, or that does not mention Person Account verification as a prerequisite, is applying the generic pattern incorrectly.

---

## Anti-Pattern 2: Using FinServ__-Prefixed API Names for Platform-Native Core FSC Orgs

**What the LLM generates:** Metadata XML, SOQL queries, or Apex code that uses `FinServ__`-prefixed API names when the target org is a platform-native Core FSC org (Winter '23+).

```xml
<!-- LLM-generated (wrong for platform-native Core FSC) -->
<types>
  <members>FinServ__FinancialAccount__c</members>
  <name>CustomObject</name>
</types>
```

```apex
// LLM-generated (wrong for platform-native Core FSC)
List<FinServ__FinancialAccount__c> accounts = [
  SELECT Id, FinServ__Balance__c FROM FinServ__FinancialAccount__c
];
```

**Why it happens:** The majority of FSC documentation, community content, and training data predates the Winter '23 platform-native model. LLMs have far more exposure to `FinServ__`-prefixed patterns and default to them even when the user is working in a Core FSC environment.

**Correct pattern:**

```xml
<!-- Platform-native Core FSC: no namespace prefix -->
<types>
  <members>FinancialAccount</members>
  <name>CustomObject</name>
</types>
```

```apex
// Platform-native Core FSC
List<FinancialAccount> accounts = [
  SELECT Id, Balance FROM FinancialAccount
];
```

**Detection hint:** Any code or metadata containing `FinServ__` should be flagged if the user has stated they are on Core FSC or Winter '23+ platform-native FSC. Ask the user to confirm which FSC model they are on before generating API names.

---

## Anti-Pattern 3: Treating CDS Activation as Sufficient Without OWD and Recalculation Steps

**What the LLM generates:** Advice that deploying `IndustriesSettings` to activate CDS is the complete solution, without mentioning OWD requirements or the post-deploy sharing recalculation step.

```
# LLM-generated (incomplete)
"To enable Compliant Data Sharing, deploy IndustriesSettings metadata 
with the CDS flag set to true. After deployment, Participant Roles will 
control access to Financial Accounts."
```

**Why it happens:** LLMs compress multi-step processes into single-step answers when the intermediate steps are in different documentation areas. The OWD requirement is documented under Sharing Settings, and the recalculation requirement is in admin documentation — neither is prominently linked from the IndustriesSettings metadata reference that LLMs are more likely to surface.

**Correct pattern:**

```
CDS activation requires four steps in sequence:
1. Set OWDs for Account, Opportunity, and Financial Deal to Private 
   or Public Read-Only (Setup > Sharing Settings)
2. Deploy IndustriesSettings with CDS flags enabled
3. Deploy Participant Role custom metadata records
4. Trigger sharing recalculation batch for existing records
   (FinServ.FinancialAccountShareRecalcBatch in managed-package FSC)

Skipping step 1 means CDS entries are written but have no access 
control effect. Skipping step 4 means pre-existing records are 
invisible to users who should have access.
```

**Detection hint:** Any advice that mentions CDS activation without also mentioning OWD settings and sharing recalculation is incomplete. Flag answers that jump directly from "deploy IndustriesSettings" to "CDS is now active."

---

## Anti-Pattern 4: Assuming Person Account Enablement Can Be Scripted or Automated

**What the LLM generates:** A script, Metadata API call, or sf CLI command that attempts to enable Person Accounts programmatically as part of a deployment pipeline.

```bash
# LLM-generated (wrong — Person Accounts cannot be enabled via Metadata API)
sf project deploy start \
  --metadata "AccountSettings" \
  --target-org sandbox \
  --test-level NoTestRun
```

Or advice that a scratch org feature flag is sufficient for all org types:
```json
// LLM-generated (incomplete — only works for scratch orgs)
{
  "features": ["PersonAccounts"]
}
```

**Why it happens:** LLMs know that many Salesforce features can be enabled via Settings metadata types and assume Person Accounts follows the same pattern. The scratch org definition file does support Person Accounts as a feature flag, which LLMs correctly apply — but incorrectly generalize to non-scratch orgs.

**Correct pattern:**

```
Person Account enablement:
- Scratch orgs: add "features": ["PersonAccounts"] to scratch org definition JSON
- Sandboxes: Enable via Setup > Account Settings (requires admin access; 
  cannot be scripted via Metadata API)
- Production: May require a Salesforce support case depending on org age 
  and configuration

This change is IRREVERSIBLE. It cannot be undone once applied. 
Plan org provisioning accordingly — enable it once during initial setup, 
not as part of recurring pipeline runs.
```

**Detection hint:** Any pipeline or script that includes PersonAccount or AccountSettings in a Metadata API deployment targeting a non-scratch org should be flagged. Person Account enablement is a one-time manual step.

---

## Anti-Pattern 5: Not Validating Participant Role Custom Metadata Cross-References After Deploy

**What the LLM generates:** A deployment plan that includes Participant Role custom metadata but has no post-deploy validation step to confirm the custom metadata's record type references resolve correctly in the target org.

```
# LLM-generated deployment plan (incomplete)
1. Deploy record types
2. Deploy IndustriesSettings  
3. Deploy Participant Role custom metadata
4. Done — CDS is now configured
```

**Why it happens:** LLMs follow a "deploy succeeds = configuration is correct" assumption that is generally valid for most metadata types. Custom metadata is an exception — it deploys successfully even when its cross-reference fields contain values that do not match any record in the target org. The LLM has no training signal that Participant Role custom metadata requires a runtime validation step separate from the deploy success signal.

**Correct pattern:**

```
After deploying Participant Role custom metadata:

1. Query the target org for Account record type developer names:
   SELECT DeveloperName FROM RecordType WHERE SObjectType = 'Account'
   
2. Compare against the record type names referenced in the deployed 
   Participant Role custom metadata records.
   
3. Assign a Participant Role to a test Financial Account record:
   - Confirm a FinancialAccountShare row is created
   - Confirm RowCause = 'ParticipantRole'
   - Confirm the user/group listed has the expected access level
   
4. Log in as the test user and confirm Financial Account record visibility.

If step 3 produces no share-table rows, the Participant Role record type 
reference is broken — fix the custom metadata and redeploy.
```

**Detection hint:** Any FSC deployment plan that ends at "deploy Participant Role custom metadata" without a share-table verification step is incomplete. The deploy success signal alone is not sufficient validation for this metadata type.

---

## Anti-Pattern 6: Ignoring the OWD Recalculation Window When Sequencing CDS Deployment Steps

**What the LLM generates:** A deployment runbook that changes OWD settings and immediately proceeds to deploy IndustriesSettings and Participant Role metadata, without accounting for the time required for the platform to complete the OWD-triggered sharing recalculation.

```
# LLM-generated runbook (wrong — no recalculation gate)
Step 1: Set Account OWD to Private
Step 2: Deploy IndustriesSettings (immediate)
Step 3: Deploy Participant Role custom metadata (immediate)
Step 4: Validate CDS
```

**Why it happens:** LLMs model OWD changes as instantaneous configuration toggles. The platform-level sharing recalculation job that an OWD change triggers is an asynchronous background process that can take hours in large orgs — this operational behavior is not prominent in conceptual documentation that LLMs are trained on.

**Correct pattern:**

```
Step 1: Set Account, Opportunity, and Financial Deal OWDs to Private
Step 2: WAIT — monitor sharing recalculation completion:
   - Setup > Sharing Settings > check for active background jobs
   - Or query: SELECT Id, Status FROM BackgroundOperation 
     WHERE Type = 'SharingRecalculation' AND Status != 'Completed'
   - Do NOT proceed until all recalculation jobs are Completed
Step 3: Deploy IndustriesSettings
Step 4: Deploy Participant Role custom metadata
Step 5: Trigger FSC-specific CDS recalculation batch
Step 6: Validate share-table rows and user access
```

**Detection hint:** Any FSC CDS deployment runbook that does not include an explicit wait-and-check step after OWD changes should be flagged as potentially unsafe for large production orgs.
