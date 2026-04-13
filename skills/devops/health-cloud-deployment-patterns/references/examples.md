# Examples — Health Cloud Deployment Patterns

## Example 1: Full Production Deployment of Health Cloud from Scratch

**Context:** A healthcare organization is going live with Health Cloud in a new production org. The implementation team has built custom flows, Apex classes (including a `CarePlanProcessorCallback` implementation), and permission sets in a developer sandbox. They need to move everything to production.

**Problem:** The team attempts to run `sf project deploy start` against production without installing the HealthCloudGA managed package first. The deployment fails with namespace resolution errors on all metadata that references `HealthCloudGA__` fields and objects. After installing the package, they deploy metadata successfully but discover care plan templates are missing and the Care Plan wizard does not work. Further investigation reveals the CarePlanProcessorCallback class was deployed but never registered in Care Plan Settings.

**Solution:**

```bash
# Step 1: Install Salesforce Industries Common Components (if required)
sf package install \
  --package 04t... \
  --target-org prod-alias \
  --wait 10

# Step 2: Install HealthCloudGA managed package
sf package install \
  --package 04t... \
  --target-org prod-alias \
  --wait 20

# Step 3: Assign Health Cloud PSLs (Setup UI or Data Loader)
# Setup > Users > [Each User] > Permission Set License Assignments
# Assign: Health Cloud for EHR, Health Cloud Platform, etc.

# Step 4: Deploy org-specific metadata
sf project deploy validate \
  --target-org prod-alias \
  --manifest manifest/package.xml \
  --test-level RunLocalTests

sf project deploy start \
  --target-org prod-alias \
  --manifest manifest/package.xml \
  --test-level RunLocalTests

# Step 5: Register CarePlanProcessorCallback in Setup UI (manual, no CLI equivalent)
# Setup > Health Cloud Setup > Care Plan Settings
# CarePlan Processor Callback: [Select your class] > Save

# Step 6: Create care plan templates via invocable action (no DML equivalent)
# Use Anonymous Apex or a setup flow that calls HealthCloud.CreateCarePlanTemplate
```

**Why it works:** The strict sequence respects the HealthCloudGA namespace dependency chain. Metadata validation requires the package to be present. CarePlanProcessorCallback registration and care plan template creation are post-deploy steps that cannot be expressed in deployable metadata — they must be documented in the deployment runbook and executed manually or via a setup script.

---

## Example 2: Sandbox Refresh and Health Cloud Reconfiguration

**Context:** An implementation team refreshes a full sandbox from production to create a UAT environment. After the refresh completes, the sandbox appears to have all the org-specific customizations, but Health Cloud features are broken: care plan templates are gone, the Care Plan wizard throws errors, and several users report "insufficient privileges" when accessing clinical records.

**Problem:** The sandbox refresh wiped the HealthCloudGA managed package installation, all PSL assignments, the CarePlanProcessorCallback registration, and care plan templates. These are not part of the sandbox refresh because the package is treated as a separate install artifact and the configuration registrations live in managed namespace Custom Metadata that does not transfer via sandbox copy.

**Solution:**

```bash
# After sandbox refresh completes:

# 1. Reinstall HealthCloudGA at same version as production
sf package installed list --target-org prod-alias
# Note the 04t... subscriber package version ID for HealthCloudGA

sf package install \
  --package 04t... \
  --target-org uat-sandbox-alias \
  --wait 20

# 2. Reassign PSLs to test users in sandbox
# Use Data Loader to query UserPackageLicense from production and re-insert in sandbox
# Or manually assign via Setup > Users for each test persona

# 3. Re-register CarePlanProcessorCallback
# Setup > Health Cloud Setup > Care Plan Settings > set callback class > Save

# 4. Recreate care plan templates
# Query from production:
sf data query \
  --query "SELECT Name, HealthCloudGA__Description__c FROM HealthCloudGA__CarePlanTemplate__c" \
  --target-org prod-alias \
  --result-format csv \
  > care_plan_templates.csv

# Recreate in sandbox via Anonymous Apex calling HealthCloud.CreateCarePlanTemplate
# or via Health Cloud Care Plan Templates Setup UI
```

**Why it works:** The sandbox reconfiguration runbook explicitly accounts for the non-metadata state that is lost on every sandbox refresh. Teams that document only their `sf project deploy` steps in the runbook will miss these reconfiguration steps every time a sandbox is refreshed.

---

## Example 3: HIPAA Pre-Go-Live Shield Encryption Configuration

**Context:** A Health Cloud org is ready for production go-live. The team has confirmed the signed BAA with Salesforce and is now configuring Shield Platform Encryption before the first PHI import.

**Problem:** The team configures encryption policies after a test data import to verify the setup. They discover that the existing test records are not encrypted by the newly activated policies — only records written after the policy activation are encrypted. To meet HIPAA technical safeguard requirements for encryption at rest, all PHI must be encrypted.

**Solution:**

```
Correct sequence:
1. Enable Shield Platform Encryption in Setup
2. Generate and activate a tenant secret (Setup > Platform Encryption > Tenant Secrets)
3. Define encryption policies for all PHI fields:
   - HealthCloudGA__EhrPatientMedication__c: medication name, dosage fields
   - HealthCloudGA__PatientHealthCondition__c: condition description fields
   - HealthCloudGA__CarePlanActivity__c: activity note fields
   - Contact: SSN custom field, date of birth, address fields with PHI
4. Activate encryption policies
5. ONLY THEN import any PHI data

If data was already imported before encryption was configured:
- Delete the unencrypted records
- Re-import after encryption policies are active
- Or work with Salesforce Support for a bulk encryption operation (not self-service)
```

**Why it works:** Shield Platform Encryption applies to new writes only. Configuring encryption after importing PHI leaves a compliance gap. The only compliant approach is to ensure policies are active before any PHI enters the org.

---

## Anti-Pattern: Deploying All Components in a Single sf project deploy

**What practitioners do:** Bundle the entire Health Cloud deployment — including custom objects, Apex, flows, permission sets, and care plan configuration — into a single `sf project deploy start` command, treating Health Cloud like any other Salesforce org.

**What goes wrong:** The deploy fails with namespace resolution errors because the HealthCloudGA managed package is not installed. Even after installing the package and rerunning, care plan templates and the CarePlanProcessorCallback registration are not captured in the deployment package, so the org is in a partially functional state after deploy with no clear error message indicating what is missing.

**Correct approach:** Use the sequential package-then-metadata pattern: install packages first, deploy metadata second, then execute a documented post-deploy checklist covering PSL assignment, callback registration, care plan template creation, and encryption configuration. The post-deploy checklist is a required deliverable for every Health Cloud deployment runbook.
