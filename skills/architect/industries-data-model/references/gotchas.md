# Gotchas — Industries Data Model

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: InsurancePolicyParticipant Links to Account, Not Contact

**What happens:** Any Apex code or SOQL query that attempts to reference ContactId on InsurancePolicyParticipant fails. SOQL filters on ContactId silently return zero rows. Apex field assignments against a ContactId lookup throw an invalid field exception at runtime.

**When it occurs:** Whenever a developer models the policyholder or beneficiary relationship using Contact — the natural assumption from standard Sales Cloud — and writes integrations or page data providers accordingly.

**How to avoid:** Use AccountId exclusively on InsurancePolicyParticipant. Individual policyholders who would traditionally be Contacts must be modeled as Person Accounts (Account records with IsPersonAccount = true) in Insurance Cloud. Validate this pattern early in data model design and document it explicitly in integration specs before external system mapping begins.

---

## Gotcha 2: Communications Cloud Account Subtypes Are Record Types, Not Separate Objects

**What happens:** SOQL or reports that query Account without a RecordType.DeveloperName filter return all four account subtypes (Business, Consumer, Billing, Service) intermingled in a single result set. Pages show inflated account counts. Billing logic receives consumer or service account records. Aggregate queries produce totals that span all subtypes.

**When it occurs:** Any time a developer or admin writes a report, list view, SOQL query, or LWC data provider against Account in a Communications Cloud org without adding a record type filter. This is especially common when migrating queries from a standard Sales Cloud org where record type filtering on Account is not typically required.

**How to avoid:** Always add `WHERE RecordType.DeveloperName = 'Billing_Account'` (or the relevant subtype) to Account queries in Communications Cloud orgs. Use DeveloperName rather than Name because RecordType.Name is admin-editable and can drift between environments. Add a code review check that flags Account queries missing a RecordType filter in Communications Cloud orgs.

---

## Gotcha 3: InsurancePolicyCoverage Cannot Exist Without a Parent InsurancePolicy

**What happens:** Attempting to insert an InsurancePolicyCoverage record without a valid InsurancePolicyId raises a required field validation error. Data migration scripts that insert coverage records before their parent policy records will fail on every row.

**When it occurs:** During data migration from legacy policy administration systems where coverage lines and policies are loaded in separate files or batches. If coverage records are processed before their parent InsurancePolicy records are committed, the foreign key constraint fails.

**How to avoid:** Always load InsurancePolicy records first, capture the resulting Salesforce IDs, and use them as the InsurancePolicyId when inserting InsurancePolicyCoverage records. Use upsert with an external ID on InsurancePolicy as the parent anchor when running multi-pass data loads. Never attempt to create coverage records in a separate transaction that precedes policy record creation.

---

## Gotcha 4: Health Cloud Object API Names Differ from FHIR Resource Names

**What happens:** SOQL and Apex written using FHIR resource names as Salesforce object API names fail at compile time or query time. `Observation` is not a valid Salesforce object — the correct name is `CareObservation`. `Condition` is not valid — use `HealthCondition`. Relationship names in subqueries similarly follow the Salesforce naming convention, not the FHIR naming convention.

**When it occurs:** When developers with FHIR or HL7 background write Salesforce code using the FHIR resource vocabulary directly, or when LLM-generated code uses FHIR terminology without translating to the Salesforce object API names.

**How to avoid:** Always verify Salesforce object API names in Setup > Object Manager before writing SOQL or Apex. The canonical reference is the Health Cloud Object Reference at developer.salesforce.com. Map FHIR resource names to Salesforce API names in the integration design document before any code is written.

---

## Gotcha 5: Industries Objects Are License-Gated and Not Available in All Editions

**What happens:** Deploying metadata, running SOQL, or executing Apex that references Industries-specific objects (InsurancePolicy, CarePlan, ServicePoint, etc.) in an org without the corresponding Industries license fails. SOQL returns an "sObject type not found" error. Metadata deployments fail with "Unknown object type" during validation.

**When it occurs:** When sandbox orgs do not have the same Industries license as production, or when a developer uses a Developer Edition org to test code destined for a licensed Industries cloud org. Also occurs in CI/CD pipelines that validate against a non-licensed org.

**How to avoid:** Confirm Industries cloud license provisioning in every org where code will be deployed or tested. Check Setup > Company Information and Setup > Installed Packages. Ensure all CI/CD validation orgs are licensed scratch orgs or sandboxes with the correct Industries feature flags enabled. Use feature detection checks in Apex where cross-edition compatibility is needed.
