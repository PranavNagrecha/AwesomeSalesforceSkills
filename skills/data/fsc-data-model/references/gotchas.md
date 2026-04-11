# Gotchas — FSC Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Native Roll-Up Summary Fields Do Not Aggregate FSC Financial Data

**What happens:** A developer creates a native ROLLUP summary field on Account expecting it to sum financial account balances across related `FinServ__FinancialAccount__c` records. The field returns zero or cannot be created, and household financial totals do not update when new financial accounts are added.

**When it occurs:** Any time someone tries to compute household financial aggregates (total assets, net worth, total balances) using standard Salesforce ROLLUP mechanics. Also occurs when an admin attempts to add a roll-up summary to the Account object targeting `FinServ__FinancialAccount__c`.

**How to avoid:** Use the pre-computed rollup fields on the household Account that are maintained by the FSC rollup engine: `FinServ__TotalAssets__c`, `FinServ__TotalLiabilities__c`, `FinServ__NetWorth__c`. Ensure the FSC rollup batch is scheduled in FSC Admin Settings. After bulk data loads that bypass triggers, manually trigger the rollup batch. Never attempt to replicate FSC rollup logic with native ROLLUP summary fields.

---

## Gotcha 2: FinServ__ Namespace Is Absent in Core FSC Orgs — All Object and Field Names Differ

**What happens:** Code, SOQL queries, Flow references, or metadata that use `FinServ__FinancialAccount__c`, `FinServ__FinancialHolding__c`, or any `FinServ__` prefix fail entirely in a Core FSC org with "sObject type not found" or "No such column" errors. This is not a permissions issue — the objects simply do not exist under those names.

**When it occurs:** When a developer writes code against managed-package FSC documentation or examples (which dominate search results and LLM training data) and deploys to a Core FSC org. It also occurs when a consultant trained on managed-package FSC joins a Core FSC project without checking the installed packages.

**How to avoid:** Before writing a single line of FSC SOQL or Apex, verify the deployment type: Setup > Installed Packages. If no "Financial Services Cloud" managed package is listed, the org is Core FSC. Use the standard (no-namespace) object names: `FinancialAccount`, `FinancialHolding`, `FinancialGoal`, `LifeEvent`. All namespace-prefixed references must be removed.

---

## Gotcha 3: Managed-Package Financial Account Ownership Is Limited to Two Parties

**What happens:** A bank needs to model a trust account with four beneficiaries or a joint investment account with three named owners. The developer discovers `FinServ__FinancialAccount__c` only has `FinServ__PrimaryOwner__c` and `FinServ__JointOwner__c` lookup fields. There is no supported way to add a third owner to the standard FSC managed-package object without building a custom junction object, which then falls outside the FSC rollup engine's scope.

**When it occurs:** Complex ownership scenarios: trusts, partnerships, custodial accounts with multiple co-owners, or any use case requiring more than two named individuals on a financial account record.

**How to avoid:** If multi-owner financial accounts are a core requirement, evaluate Core FSC — its `FinancialAccountParty` junction object supports unlimited owners with named roles (Primary Owner, Joint Owner, Beneficiary, Power of Attorney, Trustee). For existing managed-package orgs that cannot migrate, document the two-owner limitation and build custom junction objects carefully, noting that custom owners will not automatically participate in FSC rollup calculations.

---

## Gotcha 4: FSC Household Model Is Not the Same as NPSP Household Model

**What happens:** A consultant familiar with Nonprofit Success Pack (NPSP) applies NPSP household concepts to an FSC implementation. They look for `npe01__OOHousehold__c`, assume the household Account uses NPSP record types, or try to use NPSP rollup utilities (`npo02__HouseholdSoftCreditRollup__c`) to aggregate FSC financial data. None of this exists or works in FSC.

**When it occurs:** Any time a practitioner crosses FSC and NPSP projects, or when an LLM conflates the two because both use "household" terminology and both involve Salesforce Account-Contact structures.

**How to avoid:** In FSC, the household is a standard Business Account with RecordType `HouseHold`. Individual clients are Person Accounts. The link is `AccountContactRelation`. The rollup engine is FSC's own async batch framework. There is no NPSP object or rollup utility involved. Keep FSC and NPSP documentation separated; the two clouds are architecturally distinct.

---

## Gotcha 5: AccountContactRelation Soft-Deletion Breaks Household Membership Queries

**What happens:** A contact is "removed" from a household by deactivating the `AccountContactRelation` record (setting `IsActive = FALSE`) rather than deleting it. Queries that do not filter on `IsActive = TRUE` include the former member in household totals and reports, creating data quality issues in financial summaries.

**When it occurs:** When household membership management relies on ACR deactivation rather than deletion, and downstream queries omit the `IsActive = TRUE` filter. Particularly problematic in bulk reporting or rollup recalculation processes that iterate over all ACR records for a household.

**How to avoid:** Always include `AND IsActive = TRUE` when querying `AccountContactRelation` for active household membership. Establish a data governance rule: when a client leaves a household, decide whether to delete the ACR (permanent) or deactivate it (preserves history but requires consistent filtering). Document the convention in the org's data dictionary.
