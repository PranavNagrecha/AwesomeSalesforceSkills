# LLM Anti-Patterns — FSC Deployment Patterns

Common mistakes AI coding assistants make when generating or advising on FSC Deployment Patterns.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending a Single-Wave FSC Deployment Without Prerequisite Checks

**What the LLM generates:** A deployment command or script that deploys all FSC metadata components in a single batch — record types, `IndustriesSettings`, `ParticipantRole` components, and sharing rules — without any pre-flight checks for Person Account enablement or OWD settings.

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
# Step 0: pre-flight — confirm Person Accounts enabled.
# RecordType.IsPersonType is visible only when the person account feature is enabled.
sf data query \
  --query "SELECT Id, DeveloperName FROM RecordType WHERE SobjectType='Account' AND IsPersonType=true" \
  --target-org production

# Step 1: deploy record types only
sf project deploy start \
  --metadata "RecordType" \
  --target-org production \
  --test-level RunSpecifiedTests --tests FSCRecordTypeTests

# Step 2: deploy IndustriesSettings (settings/Industries.settings) after record types are confirmed
sf project deploy start \
  --metadata "Settings:Industries" \
  --target-org production

# Step 3: deploy ParticipantRole components (participantRoles/*.participantRole)
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

**What the LLM generates:** Advice that deploying `IndustriesSettings` with "the CDS flag" is the complete solution, without naming the per-object flags, the OWD requirement, or the post-deploy sharing recalculation step.

```
# LLM-generated (incomplete)
"To enable Compliant Data Sharing, deploy IndustriesSettings metadata
with the CDS flag set to true. After deployment, Participant Roles will
control access to Financial Accounts."
```

**Why it happens:** LLMs compress multi-step processes into single-step answers when the intermediate steps are in different documentation areas. The OWD requirement is documented under Sharing Settings and the recalculation requirement in admin documentation — neither is linked from the `IndustriesSettings` reference. There is also no single CDS flag: the Metadata API guide lists one boolean per object (`enableCompliantDataSharingForAccount`, `...ForOpportunity`, `...ForInteraction`, `...ForInteractionSummary`, `...ForCustomObjects`), each defaulting to false.

**Correct pattern:**

```
CDS activation requires four steps in sequence:
1. Set OWDs for the CDS objects to Private or Public Read-Only
   (Setup > Sharing Settings) and wait for that recalculation to finish
2. Deploy IndustriesSettings with the enableCompliantDataSharingFor<Object>
   flag set to true for each object that needs CDS
3. Deploy ParticipantRole components whose parentObject is one of those objects
4. Run the CDS share recalculation for records that already existed
   (managed-package FSC: FinServ.FinancialAccountShareRecalcBatch —
   UNVERIFIED (2026-10-19): the class is not in the Summer '26 Apex Reference;
   confirm it exists in the org before scripting it)

Skipping step 1 means CDS entries are written but have no access
control effect. Skipping step 4 means pre-existing records are
invisible to users who should have access.
```

**Detection hint:** Any advice that mentions CDS activation without naming the per-object `enableCompliantDataSharingFor*` flag, the OWD setting, and the recalculation is incomplete. Flag answers that jump directly from "deploy IndustriesSettings" to "CDS is now active."

---

## Anti-Pattern 4: Assuming Person Account Enablement Can Be Scripted or Automated

**What the LLM generates:** A script, Metadata API call, or sf CLI command that attempts to enable Person Accounts programmatically as part of a deployment pipeline.

```bash
# LLM-generated (wrong — AccountSettings has no field that enables person accounts)
sf project deploy start \
  --metadata "AccountSettings" \
  --target-org sandbox \
  --test-level NoTestRun
```

Or advice that a scratch org feature flag is sufficient for all org types:
```json
{
  "features": ["PersonAccounts"]
}
```

**Why it happens:** LLMs know that many Salesforce features can be enabled via Settings metadata types and assume Person Accounts follows the same pattern. The scratch org definition file does support `PersonAccounts` as a feature, which LLMs correctly apply — but incorrectly generalize to sandboxes and production.

**Correct pattern:**

```
Person Account enablement:
- Scratch orgs: add "PersonAccounts" to the features array of the
  scratch org definition file
- Sandboxes and production: "Person accounts aren't enabled by default
  in Salesforce. To request person accounts, contact Salesforce."
  No Settings type turns it on; AccountSettings covers account teams,
  history tracking, the owner report, and similar options only.

Plan as if the change cannot be undone (UNVERIFIED (2026-10-19):
irreversibility is stated only in Salesforce Help, which could not be
fetched). Enable it once during org provisioning, not in pipeline runs.
```

**Detection hint:** Any pipeline step that deploys `AccountSettings` "to enable person accounts", or any non-scratch provisioning script that assumes person accounts appear without a request to Salesforce, should be flagged.

---

## Anti-Pattern 5: Treating ParticipantRole as Custom Metadata With Record Type References

**What the LLM generates:** A `ParticipantRole__mdt` custom metadata record under `customMetadata/`, or a post-deploy step that "validates the Participant Role record type references".

```xml
<!-- LLM-generated (wrong) — customMetadata/ParticipantRole.Advisor.md-meta.xml -->
<CustomMetadata xmlns="http://soap.sforce.com/2006/04/metadata">
  <label>Advisor</label>
  <values>
    <field>RecordTypeDeveloperName__c</field>
    <value>Household</value>
  </values>
</CustomMetadata>
```

**Why it happens:** Many FSC configuration objects really are custom metadata types, and "role" sounds like reference data, so the model pattern-matches to `__mdt`. The Summer '26 Metadata API guide documents `ParticipantRole` as its own type (API 50.0+), stored as `.participantRole` files in the `participantRoles` folder, with exactly four fields: `defaultAccessLevel` (required; `Edit`, `None`, or `Read`), `isActive`, `masterLabel` (required), and `parentObject` (required; Account, Opportunity, FinancialDeal, Interaction, InteractionSummary, Budget, IndividualApplication, FundingAward, FundingOpportunity, Team, or a custom object). There is no record type field to validate.

**Correct pattern:**

```xml
<!-- participantRoles/Advisor.participantRole -->
<ParticipantRole xmlns="http://soap.sforce.com/2006/04/metadata">
    <defaultAccessLevel>Read</defaultAccessLevel>
    <isActive>true</isActive>
    <masterLabel>Advisor</masterLabel>
    <parentObject>Account</parentObject>
</ParticipantRole>
```

After deploying, check that each role's `parentObject` has its `enableCompliantDataSharingFor*` flag set in `IndustriesSettings`, assign the role on a test record, confirm a share row is written for the expected user or group, and log in as that user.

**Detection hint:** `ParticipantRole` under `customMetadata/`, a `ParticipantRole__mdt` or `.md-meta.xml` file name, or any mention of a ParticipantRole "record type reference" is this anti-pattern. The skill's checker reports it as an ERROR.

---

## Anti-Pattern 6: Ignoring the OWD Recalculation Window When Sequencing CDS Deployment Steps

**What the LLM generates:** A deployment runbook that changes OWD settings and immediately proceeds to deploy `IndustriesSettings` and `ParticipantRole` metadata, or that "waits" by polling an object that does not track sharing recalculation.

```
# LLM-generated runbook (wrong — no recalculation gate, invented query)
Step 1: Set Account OWD to Private
Step 2: SELECT Id, Status FROM BackgroundOperation
        WHERE Type = 'SharingRecalculation' AND Status != 'Completed'
Step 3: Deploy IndustriesSettings (immediate)
Step 4: Deploy ParticipantRole components (immediate)
```

**Why it happens:** LLMs model OWD changes as instantaneous toggles and then invent a plausible polling query. `BackgroundOperation` is a real object, but its `Type` picklist (ApiCatalogPoller, ExternalObjectSync, MetadataChangesetOperation, Sweeper, and others) has no sharing-recalculation value, and its `Status` value is `Complete`, not `Completed` — so the query above returns nothing and the gate passes immediately.

**Correct pattern:**

```
Step 1: Set the CDS objects' OWDs to Private (or Public Read-Only)
Step 2: WAIT — the Security Implementation Guide says OWD recalculation
        runs asynchronously, sends a notification email when it completes,
        and can be monitored on Setup > Background Jobs.
        Do NOT proceed until that job shows complete.
Step 3: Deploy IndustriesSettings with the per-object CDS flags
Step 4: Deploy ParticipantRole components
Step 5: Run the CDS share recalculation for existing records
Step 6: Validate share rows and log in as a test user
```

**Detection hint:** Any CDS runbook with no explicit wait after an OWD change, or one that gates on a `BackgroundOperation` query, should be flagged.
