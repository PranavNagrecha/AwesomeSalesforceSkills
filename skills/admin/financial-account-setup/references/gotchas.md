# Gotchas — Financial Account Setup

Non-obvious Salesforce FSC platform behaviors that cause real production problems.

## Gotcha 1: Household Balance Rollup Only Flows to the Primary Owner's Household

**What happens:** The FSC managed-package rollup engine writes aggregate account balances exclusively to the household of the account's Primary Owner (as defined by a `FinancialAccountRole` record with `Role = Primary Owner`). Joint Owners, Beneficiaries, and all other role types do not trigger a rollup to their own household records.

**When it occurs:** Any time a `FinancialAccountRole` with `Role = Joint Owner` is created for a person whose `FinServ__PrimaryGroup__c` differs from the Primary Owner's household. The Joint Owner's household balance summary will undercount their total assets under management. This typically surfaces when an advisor reports that a client's "total assets" figure is too low, and investigation reveals the client is a joint owner — not primary owner — on some accounts.

**How to avoid:** Before go-live, test the rollup explicitly with a scenario where a Joint Owner belongs to a different household. If cross-household rollup is a business requirement, implement a custom solution (scheduled Apex or Record-Triggered Flow) that writes to a separate custom field on the Joint Owner's household — do not attempt to write to the managed package's native rollup fields directly.

---

## Gotcha 2: Held-Away vs Internally Originated Accounts Require Different Permission and Field Designs

**What happens:** Held-away accounts (assets held at an external custodian, balance data entered manually or loaded via integration) must not be editable by advisors — only data operations staff or the integration process should update their balances. Without explicit permission enforcement, advisors can modify balance and holding fields, which creates compliance audit trail violations. The managed package does not ship a built-in permission distinction between held-away and originated account editing rights.

**When it occurs:** When the firm tracks both internally originated accounts and held-away accounts in the same FSC org without separate permission enforcement. An advisor who has edit access on `FinancialAccount` records for their originated accounts will also be able to edit held-away account balances unless a validation rule or record type restriction prevents it.

**How to avoid:** Implement one or both of the following on day one:
- A validation rule on `FinancialAccount` that checks `FinServ__HeldAway__c = true` (or a custom flag field) and blocks edits to balance fields unless the running user has a designated permission (e.g., a custom permission `CanEditHeldAwayBalances`).
- Separate record types for held-away and originated accounts, with the held-away record type's page layout using read-only field overrides for balance and holding fields.

---

## Gotcha 3: FinancialAccount Object API Name Differs Between Managed-Package and Core FSC

**What happens:** In managed-package FSC orgs (the deployment model used by most orgs that implemented FSC before Winter '23), the FinancialAccount object is a custom object with the namespace prefix `FinServ__FinancialAccount__c`. All related field API names also carry the `FinServ__` prefix. In Core FSC orgs (General Availability Winter '23+), `FinancialAccount` is a standard platform object with no namespace — fields are referenced as `Balance`, `PrimaryOwner`, etc.

**When it occurs:** When a developer writes Apex, SOQL, Flow formulas, or metadata (page layouts, validation rules) using one set of API names and deploys to an org using the other model. The failure mode varies: Apex fails at runtime with "field not found" errors; Flow validation may fail at activation; page layout deployments will error in the metadata API.

**How to avoid:** Before writing any code or metadata referencing FinancialAccount, confirm the packaging model:
- In Setup > Installed Packages: if "Financial Services Cloud" appears as a managed package with namespace `FinServ`, use the `FinServ__` prefix.
- In Setup > Object Manager: if `FinancialAccount` appears as a standard object (not a custom object ending in `__c`), use the Core FSC naming.
- Document this determination in the project's architecture decision record so that all contributors use consistent API names.

---

## Gotcha 4: FinancialAccountType Picklist Values Cannot Be Safely Deleted Once Used on Records

**What happens:** The `FinancialAccountType` picklist drives validation rules, page layout assignments (via record types), and reporting filters across the org. If a picklist value is deleted after it has been assigned to existing records, Salesforce replaces the deleted value with a blank in those records only if you choose to "replace" during the deletion wizard — but if existing records used the value, they may be left in an indeterminate state where the stored value no longer exists in the picklist definition. This can break validation rules that test for specific picklist values and produce blank fields in reports.

**When it occurs:** During org cleanup, when a project team decides to consolidate account type values (e.g., renaming "Individual IRA" to "Traditional IRA"). Deleting the old value instead of using the Replace function (which migrates existing records to the new value) is the common mistake.

**How to avoid:** Always use the Replace picklist value workflow in Setup instead of deleting. Navigate to the picklist field, click Edit next to the value to be removed, and use the "Replace" option to migrate all existing records to the new value before removing the old one. After replacement, run a report confirming zero records still hold the old value before finalizing the deletion.

---

## Gotcha 5: FSC Rollup Batch Must Be Run After Initial Data Load — It Does Not Run Automatically on Record Insert

**What happens:** When financial accounts are bulk-loaded via Data Loader or an integration (common during initial org population or annual data refresh), household rollup fields are not updated immediately. The FSC rollup calculation is performed by the FSC Rollup Batch job, not by a trigger on `FinancialAccount` insert. After a large data load, household records may show stale or zero balance figures until the batch runs.

**When it occurs:** After any bulk insert or update of `FinancialAccount` records outside of the standard FSC UI (which triggers a recalculation for the records touched in that session). This is most acute during initial data migration, annual account balance updates loaded via API, and after running Data Loader to create large volumes of new accounts.

**How to avoid:** After bulk data loads, immediately trigger the FSC rollup recalculation from the FSC Admin app (Setup > Financial Services > Run Account Rollup) or schedule the rollup batch to run immediately after the load window. In sandboxes, always run the rollup batch manually before validating rollup-dependent UAT scenarios.
