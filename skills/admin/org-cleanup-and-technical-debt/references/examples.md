# Examples — Org Cleanup And Technical Debt

## Example 1: Bulk Field Cleanup Using Metadata Retrieve and Usage Analysis

**Context:** An Enterprise Edition org has 487 custom fields on the Account object, approaching the 500-field limit. The admin needs to free up slots for a new integration project.

**Problem:** Without systematic usage analysis, the admin risks deleting fields that are referenced by Flows, validation rules, or Apex — causing runtime errors that do not surface until a user triggers the affected automation.

**Solution:**

```bash
# Step 1: Retrieve all custom field metadata for Account
sf project retrieve start --metadata CustomField:Account.*

# Step 2: For each field, check data population
# Run this SOQL for each candidate field:
SELECT COUNT(Id) FROM Account WHERE Custom_Field__c != null

# Step 3: Search the retrieved metadata for references
grep -r "Custom_Field__c" force-app/main/default/
# Check: flows/, triggers/, classes/, validationRules/, reports/

# Step 4: Build destructiveChanges.xml for safe-to-delete fields
```

```xml
<!-- destructiveChanges.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.Legacy_Source__c</members>
        <members>Account.Old_Region_Code__c</members>
        <members>Account.Temp_Migration_Flag__c</members>
        <name>CustomField</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Step 5: Deploy destructive changes to sandbox first
sf project deploy start --manifest package.xml \
  --post-destructive-changes destructiveChanges.xml \
  --target-org my-sandbox

# Step 6: Run all tests in sandbox
sf apex run test --target-org my-sandbox --test-level RunLocalTests --wait 30
```

**Why it works:** The metadata text search catches references that Setup's "Where Is This Used?" misses, particularly Apex string references and Flow formula expressions. Testing in sandbox before production ensures broken references surface before they affect users.

---

## Example 2: Flow Version Pruning When Approaching the 2,000-Version Limit

**Context:** An org has 1,847 total Flow versions across 200+ Flows. The admin cannot create new Flows until versions are cleaned up.

**Problem:** Each Flow save creates a new version. Over years of iterative development, Flows accumulate dozens of inactive versions that serve no purpose but consume the org-wide version count.

**Solution:**

```text
Step 1: Go to Setup > Flows
Step 2: For each Flow, click the Flow name to open version history
Step 3: Identify the active version and the most recent inactive version (keep as rollback reference)
Step 4: Delete all older inactive versions one by one

For bulk cleanup using Tooling API:
```

```bash
# Query all inactive Flow versions
sf data query --query "SELECT Id, Definition.DeveloperName, VersionNumber, Status \
  FROM Flow WHERE Status = 'Obsolete' ORDER BY Definition.DeveloperName, VersionNumber" \
  --target-org my-org --use-tooling-api

# Delete specific inactive versions (by Id)
sf data delete record --sobject Flow --record-id 301xx0000000001 --use-tooling-api --target-org my-org
```

**Why it works:** Keeping one rollback version per Flow provides a safety net. Deleting through the Tooling API enables bulk operations that would take hours manually in Setup.

---

## Example 3: Deactivating Legacy Workflow Rules Safely

**Context:** An org has 45 active Workflow Rules on the Case object. Record-Triggered Flows have been built to replace them, but the old rules are still firing alongside the new Flows.

**Problem:** Both the Workflow Rules and the replacement Flows execute on the same trigger events, causing duplicate emails, double field updates, and unpredictable field values.

**Solution:**

```text
Step 1: Export full Workflow Rule list from Setup > Workflow Rules
Step 2: Map each rule to its replacement Flow (confirm trigger event, criteria, and actions match)
Step 3: In sandbox, deactivate all 45 Workflow Rules
Step 4: Check Setup > Time-Based Workflow — flush any queued time-dependent actions
Step 5: Run full regression testing on Case creation, update, and escalation paths
Step 6: If stable after 2 weeks, deactivate in production
Step 7: After another 2-week observation period, delete the deactivated rules
```

**Why it works:** The two-phase approach (deactivate then delete) provides a rollback window. Checking the time-based workflow queue prevents orphaned actions from firing unexpectedly after deactivation.

---

## Anti-Pattern: Deleting Fields Directly in Production Without Reference Checking

**What practitioners do:** Admin sees a field with no data populated and deletes it directly in production through Setup, assuming "no data = not used."

**What goes wrong:** The field is referenced in a Flow formula expression (`{!$Record.Custom_Field__c} != null`). The Flow continues to compile, but at runtime the formula evaluates to an error, causing the Flow to fail for every record that triggers it. Because the Flow was not recompiled after the field deletion, the error only surfaces when a user triggers the Flow — potentially days later.

**Correct approach:** Always search all metadata (Flows, Apex, validation rules, reports, page layouts) for references to a field before deleting it. Test the deletion in a sandbox and run all Apex tests and critical Flows before promoting to production.
