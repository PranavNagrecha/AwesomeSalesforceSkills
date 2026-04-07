# Gotchas — Household Model Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: `Rollups__c` Picklist Values Are Not Auto-Seeded for All Object Types in Existing Orgs

**What happens:** Household rollup fields for Cases, Insurance Policies, or Opportunities remain at zero or do not update, even though related records exist and ACR membership is correctly configured. No error is thrown.

**When it occurs:** In FSC orgs provisioned before certain FSC release milestones. When FSC adds rollup support for a new object type in a release, new orgs provisioned after that release receive the corresponding `Rollups__c` picklist value automatically. Orgs that already existed do not receive the new value — the admin must add it manually. This commonly surfaces when Insurance Cloud or CPQ is enabled in an existing FSC org.

**How to avoid:** Always audit the `Rollups__c` picklist values as a first step when setting up or troubleshooting household rollups. Navigate to Setup > Object Manager > Account > Fields & Relationships > Rollups__c > Values. Compare against the list of object types that should be aggregated. Add any missing values manually, then run the batch rollup job to recalculate.

---

## Gotcha 2: `FinServ__IncludeInGroup__c` Defaults to False When ACR Records Are Created Programmatically

**What happens:** Household members appear in the household relationship panel, but their financial accounts, opportunities, or other related records are not included in any household rollup totals. The household rollup fields stay at zero or only reflect members whose ACR was created through the FSC UI.

**When it occurs:** When ACR records are created via Data Loader, Apex insert, or Flow without explicitly setting `FinServ__IncludeInGroup__c = true`. The field has no required constraint and its default value in programmatic contexts is `false`. The FSC UI typically sets this field during the "Add to Group" interaction, but programmatic paths do not replicate that behavior automatically.

**How to avoid:** Always include `FinServ__IncludeInGroup__c = true` in any programmatic ACR creation path. Add it to Data Loader import templates, Apex insert blocks, and Flow Create Record elements. When auditing an existing org, query for ACR records where this field is `false` and determine whether the exclusion was intentional.

---

## Gotcha 3: ACR Requires `PersonContactId`, Not the Person Account's `Account.Id`

**What happens:** Apex code or a data import that sets `AccountContactRelation.ContactId` to a Person Account's `Account.Id` either throws a DML error or silently creates an invalid ACR record that does not participate in FSC rollups.

**When it occurs:** Person Accounts are unusual because they are both an Account and a Contact. The `Id` field on the SObject returns the Account Id. However, the ACR junction requires a Contact Id in its `ContactId` field. For Person Accounts, the underlying Contact's Id is stored in `Account.PersonContactId` — a separate, non-obvious field. Developers unfamiliar with Person Account internals routinely use `Id` where `PersonContactId` is required.

**How to avoid:** When creating ACR records for Person Account members in Apex, always query and use `PersonContactId`:
```apex
Account pa = [SELECT Id, PersonContactId FROM Account WHERE Id = :personAccountId LIMIT 1];
AccountContactRelation acr = new AccountContactRelation(
    AccountId = householdId,
    ContactId = pa.PersonContactId, // Correct — use PersonContactId, not Id
    FinServ__PrimaryGroup__c = true,
    FinServ__Primary__c = false,
    FinServ__IncludeInGroup__c = true
);
```
In Data Loader, export the Person Account records with `PersonContactId` included and use that column as the `ContactId` value in ACR imports.

---

## Gotcha 4: FSC and NPSP Rollup Engines Conflict When Both Packages Are Installed

**What happens:** Household rollup fields (`TotalAssets`, `TotalLiabilities`, etc.) contain inconsistent or wrong values. In some cases, values oscillate between two different amounts on successive page refreshes or after unrelated record saves. DML exceptions may appear in debug logs referencing conflicting trigger updates on the Account object.

**When it occurs:** When both NPSP and FSC managed packages are installed in the same org. NPSP installs its own triggers on Contact and Account that recalculate household aggregations using its direct-lookup model. FSC installs separate triggers on ACR that recalculate using its ACR-based model. Both trigger chains may update the same rollup fields on the Household Account, and the last write wins — which is non-deterministic.

**How to avoid:** Do not install NPSP in an FSC org. If both packages are present, the only supported remediation is to work with Salesforce to migrate to a single model. If an org needs both nonprofit and financial services functionality, use the FSC model (as FSC is built on the Salesforce Platform's standard data model) and replicate any NPSP-specific nonprofit features with standard Salesforce capabilities or dedicated FSC nonprofit extensions.

---

## Gotcha 5: `FinServ__Primary__c = true` Must Be Unique per Household, But the Platform Does Not Enforce It

**What happens:** Multiple ACR records for the same household have `FinServ__Primary__c = true`. FSC display components that rely on identifying the primary member (such as household summary panels and some standard FSC Lightning components) may show the wrong member or display inconsistently.

**When it occurs:** When ACR records are created in bulk without deduplication logic for the primary member flag. The platform does not enforce uniqueness on `FinServ__Primary__c` — there is no unique constraint or validation rule out of the box. Bulk imports or Flows that always set the flag to `true` will create multiple "primary" members per household without error.

**How to avoid:** Add a before-insert/before-update validation rule or Apex trigger to enforce that only one ACR per Household Account can have `FinServ__Primary__c = true`. Alternatively, use a Process or Flow with explicit logic to unset the flag on existing ACRs before setting it on the new record. Include this uniqueness check in any data migration run book for FSC orgs.
