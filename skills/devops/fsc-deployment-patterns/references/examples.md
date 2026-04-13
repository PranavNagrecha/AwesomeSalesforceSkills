# Examples — FSC Deployment Patterns

## Example 1: Managed-Package FSC Org Pipeline Breaks After Migration to Core FSC

**Context:** A wealth management firm built its Salesforce DevOps pipeline on a managed-package FSC org. Over two years, the pipeline accumulated hundreds of metadata artifacts referencing `FinServ__`-prefixed API names. When the firm was upgraded to platform-native Core FSC (Winter '23), the DevOps team attempted to deploy the existing pipeline to the new production org.

**Problem:** Every deployment wave failed immediately with "Component not found" errors across dozens of metadata types. The sf CLI output listed individual component failures without indicating a systemic namespace root cause. The team spent several hours checking API versions, package versions, and scratch org definitions before identifying that the namespace was the issue.

**Solution:**

Step 1 — Audit the source package for namespace contamination:
```python
# stdlib-only namespace audit (run against exported metadata directory)
import os, re
from pathlib import Path

FINSVC_PATTERN = re.compile(r'FinServ__\w+')
manifest_dir = Path('force-app/main/default')

findings = {}
for f in manifest_dir.rglob('*.xml'):
    text = f.read_text(encoding='utf-8', errors='ignore')
    matches = FINSVC_PATTERN.findall(text)
    if matches:
        findings[str(f)] = list(set(matches))

for path, names in findings.items():
    print(f"{path}: {names}")
```

Step 2 — Rewrite namespace-qualified names to platform-native equivalents. Example substitutions:

| Managed-Package API Name | Platform-Native API Name |
|---|---|
| `FinServ__FinancialAccount__c` | `FinancialAccount` |
| `FinServ__Financial_Account__c.FinServ__Balance__c` | `FinancialAccount.Balance` |
| `FinServ__ParticipantRole__mdt` | `ParticipantRole` |
| `FinServ__Household__c` | `Account` (with Household record type) |

Step 3 — Validate rewritten package against the target org before deploying:
```bash
sf project deploy validate \
  --source-dir force-app/main/default \
  --target-org prod-core-fsc \
  --test-level RunLocalTests
```

**Why it works:** Platform-native Core FSC exposes FSC objects as standard platform objects with no namespace. The Metadata API resolves metadata by API name — if the API name in the package does not match any object in the target, the component is reported as not found. The namespace audit script surfaces all contaminated names in a single pass, allowing a systematic rewrite rather than a component-by-component fix.

---

## Example 2: CDS Share Table Empty After IndustriesSettings Deployment

**Context:** A retail banking team deployed `IndustriesSettings` metadata to a production org to activate Compliant Data Sharing for Financial Accounts. The deploy succeeded with no errors. Relationship Managers then reported they could not see Financial Account records belonging to their clients, even though Participant Role assignments were in place.

**Problem:** The share table (`FinancialAccountShare` in managed-package orgs, or the platform-native equivalent) contained no rows after the deployment. CDS appeared activated in Setup but was not enforcing or granting access.

**Solution:**

Step 1 — Verify OWD settings are restrictive enough for CDS to be meaningful:
```
Setup > Sharing Settings
  Account OWD: Private          ✓ (required)
  Opportunity OWD: Private      ✓ (required)
  Financial Deal OWD: Private   ✓ (required)
```

If any of these were Public Read/Write, update them to Private before proceeding. OWD changes require a sharing recalculation, which Salesforce triggers automatically but can take time in large orgs.

Step 2 — Trigger CDS sharing recalculation for existing records. In managed-package orgs:
```apex
// Managed-package FSC: trigger share recalc via Apex
Database.executeBatch(
    new FinServ.FinancialAccountShareRecalcBatch(),
    200
);
```

In platform-native Core FSC, trigger through the Industries Shared Activities recalculation mechanism or via the Setup > Sharing Settings > Recalculate button for the affected object.

Step 3 — Verify share-table rows were created:
```sql
-- Managed-package FSC
SELECT Id, ParentId, UserOrGroupId, RowCause, FinancialAccountAccessLevel
FROM FinancialAccountShare
WHERE ParentId = '<test_financial_account_id>'
  AND RowCause = 'ParticipantRole'
```

Step 4 — Confirm a test Relationship Manager can see the record:
```bash
sf org open --target-org prod --path /lightning/r/FinancialAccount/<id>/view
# Log in as Relationship Manager test user and confirm record visibility
```

**Why it works:** CDS does not retroactively populate share-table rows for records that existed before CDS was activated. The `IndustriesSettings` deployment enables the sharing engine for future record operations but does not run a recalculation job automatically. The batch job explicitly recalculates shares for all existing records, ensuring pre-existing Financial Accounts get the correct share-table entries.

---

## Anti-Pattern: Deploying Household Record Types Before Enabling Person Accounts

**What practitioners do:** A developer exports the full metadata package from an FSC sandbox (where Person Accounts were already enabled) and deploys the entire package to a fresh developer org or a new sandbox in a single wave, assuming all components will land in the correct order.

**What goes wrong:** The deployment fails immediately on the `RecordType` metadata for Household Account record types. The error reads something like: `Entity of type RecordType named Household not found` or a reference resolution error. Because the error appears in the middle of a large batch deployment, developers often interpret it as a missing dependency on another metadata component rather than a missing org configuration.

**Correct approach:** Before deploying any FSC metadata to a target org, explicitly verify Person Account status:

```bash
# Check if PersonAccount record type exists (proxy for PA enablement)
sf data query \
  --query "SELECT Id, DeveloperName FROM RecordType WHERE SObjectType = 'Account' AND DeveloperName = 'PersonAccount'" \
  --target-org <alias>
```

If the query returns zero rows, Person Accounts are not enabled. Enable them via Setup > Account Settings > Allow users to relate a contact to multiple accounts (or equivalent), or file a Salesforce support case for production orgs. Only after this returns the PersonAccount record type should any FSC metadata deployment proceed.
