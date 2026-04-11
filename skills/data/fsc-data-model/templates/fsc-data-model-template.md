# FSC Data Model — Work Template

Use this template when designing, querying, or troubleshooting the FSC data model.

## Scope

**Skill:** `data/fsc-data-model`

**Request summary:** (fill in what the user asked for)

---

## Step 1: Confirm FSC Deployment Type

**How confirmed:** [ ] Checked Setup > Installed Packages  [ ] Confirmed via SOQL query on `InstalledSubscriberPackage`

**Org type:**
- [ ] **Managed-package FSC** — "Financial Services Cloud" or "Salesforce Industries" package is installed. All FSC object and field API names carry the `FinServ__` prefix.
- [ ] **Core FSC (platform-native)** — No managed package installed. FSC objects are standard Salesforce objects with no namespace prefix (e.g., `FinancialAccount`, `FinancialHolding`).

**Package version (if managed-package):** _______________

---

## Step 2: Data Model Reference — Key Objects

Fill in the API names for this org type. Cross out the column that does not apply.

| Concept | Managed-Package API Name | Core FSC API Name | In Use? |
|---|---|---|---|
| Financial Account | `FinServ__FinancialAccount__c` | `FinancialAccount` | [ ] |
| Financial Account Ownership | `FinServ__PrimaryOwner__c` + `FinServ__JointOwner__c` (fields on FA) | `FinancialAccountParty` (junction object) | [ ] |
| Financial Holding | `FinServ__FinancialHolding__c` | `FinancialHolding` | [ ] |
| Assets & Liabilities | `FinServ__AssetsAndLiabilities__c` | `AssetsAndLiabilities` | [ ] |
| Financial Goal | `FinServ__FinancialGoal__c` | `FinancialGoal` | [ ] |
| Life Event | `FinServ__LifeEvent__c` | `LifeEvent` | [ ] |
| Client-Contact Relationship | `FinServ__ContactContactRelation__c` | Standard `ContactContactRelation` | [ ] |
| Account-Account Relationship | `FinServ__AccountAccountRelation__c` | Standard `AccountAccountRelation` | [ ] |
| Household Membership | `AccountContactRelation` (standard, both deployment types) | `AccountContactRelation` | [ ] |

---

## Step 3: Household Relationship Model

**Household Account ID:** _______________

**Household RecordType DeveloperName:** `HouseHold` (confirm exact value in this org)

**Client representation:** [ ] Person Accounts enabled  [ ] Contact-only (non-Person Account)

**Household member query:**

```soql
SELECT ContactId, Contact.Name, Roles, IsActive
FROM AccountContactRelation
WHERE AccountId = '[HOUSEHOLD_ACCOUNT_ID]'
AND IsActive = TRUE
```

**Member contact IDs returned:** (record here after running query)

---

## Step 4: Financial Account Ownership Query

**For managed-package orgs:**

```soql
SELECT Id, Name, FinServ__FinancialAccountType__c, FinServ__Balance__c,
       FinServ__Status__c
FROM FinServ__FinancialAccount__c
WHERE FinServ__PrimaryOwner__c = '[CONTACT_ID]'
   OR FinServ__JointOwner__c = '[CONTACT_ID]'
```

**For Core FSC orgs:**

```soql
SELECT FinancialAccountId, FinancialAccount.Name, FinancialAccount.Balance, Role
FROM FinancialAccountParty
WHERE RelatedPersonId = '[CONTACT_ID]'
```

**Results / notes:** (record account count and any unexpected gaps)

---

## Step 5: Household Financial Rollup Verification

**Rollup fields to verify on household Account:**

| Field API Name (Managed-Package) | Field API Name (Core FSC) | Current Value | Expected? |
|---|---|---|---|
| `FinServ__TotalAssets__c` | `TotalAssets` | | [ ] |
| `FinServ__TotalLiabilities__c` | `TotalLiabilities` | | [ ] |
| `FinServ__NetWorth__c` | `NetWorth` | | [ ] |

**Rollup batch last run:** (check FSC Admin Settings or Scheduled Jobs)

**Action needed:**
- [ ] Rollup batch is current — no action required
- [ ] Rollup batch is stale — trigger recalculation from FSC Admin Settings
- [ ] Rollup configuration is missing account types — update Rollup Configuration in FSC Admin Settings

---

## Step 6: SOQL / Apex Namespace Audit

Before finalizing any code or configuration, verify:

- [ ] All object API names use the correct namespace for this org type
- [ ] No `FinServ__` prefix in Core FSC code; no missing `FinServ__` prefix in managed-package code
- [ ] All `AccountContactRelation` queries include `AND IsActive = TRUE`
- [ ] Financial account ownership queries include both owner paths (Primary + Joint for managed; FinancialAccountParty for Core)
- [ ] No native ROLLUP summary fields targeting FSC financial objects

---

## Notes

(Record any deviations from standard patterns, org-specific quirks, or open questions here.)
