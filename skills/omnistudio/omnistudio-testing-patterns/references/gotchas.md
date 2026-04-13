# Gotchas — OmniStudio Testing Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: OmniScript Preview Silently Skips Navigation Actions

**What happens:** Navigation Action steps (Save, Navigate, Cancel) are excluded from OmniScript Preview execution. The designer renders the form and evaluates conditional logic but does not fire any Navigation Actions. No error or warning is shown — the Preview simply moves past those steps as if they completed successfully.

**When it occurs:** Any OmniScript that uses a Navigation Action step to save data to Salesforce, navigate to a record, or cancel the flow. This is extremely common — most production OmniScripts have at least one Save step.

**How to avoid:** After completing OmniScript Preview, always deploy to a sandbox and execute the full OmniScript as a user with the target profile. Explicitly trigger each Navigation Action step and confirm the expected record is created/updated or navigation occurs. Document which Navigation Actions could not be validated in Preview and ensure they are covered in user-level sandbox testing before production deployment.

---

## Gotcha 2: IP Test Execution vlcStatus `warning` Does Not Abort the Procedure

**What happens:** When an Integration Procedure step returns `vlcStatus: "warning"`, execution continues to the next step. The step's output may be partially populated or empty depending on what the step was doing when it encountered the warning condition. Downstream steps that consume the warning step's output receive null or default values without any error signal.

**When it occurs:** Commonly happens with conditional HTTP callout steps where a remote service returns a non-fatal status code (like 204 No Content or a business-rule warning) that the IP interprets as `warning`. Also occurs in DataRaptor steps where a field mapping finds no matching records.

**How to avoid:** During IP Test Execution, treat any non-`success` vlcStatus as a failure during the testing phase. Inspect the full response JSON for the step and verify that downstream steps produce expected values even if an upstream step returned a warning. Do not rely on the OmniScript's generic error surface to catch warning-induced data corruption — always review the IP test response JSON directly.

---

## Gotcha 3: UTAM Page Objects Are Not Interchangeable Between Package Runtime and Standard Runtime

**What happens:** OmniStudio Package Runtime (managed package installation) and Standard/Core Runtime (native Salesforce metadata) render OmniScript HTML with different DOM structures and component namespaces. UTAM page objects compiled for Package Runtime HTML will fail to locate elements in Standard Runtime orgs, and vice versa.

**When it occurs:** When a team builds UTAM tests against a Package Runtime sandbox and then the org is migrated to Standard Runtime (a common upgrade path Salesforce is encouraging). Also occurs when a team copies UTAM tests from a Package Runtime community repo without checking their org runtime.

**How to avoid:** Before building or running UTAM tests, confirm the org runtime by checking Setup > OmniStudio Settings. If the org uses Package Runtime, use the Vlocity UTAM page objects. If the org uses Standard Runtime, use the Salesforce-native OmniStudio UTAM page objects from the appropriate npm package. Document the runtime type in the test suite README so future engineers do not inherit the wrong page objects after a runtime migration.

---

## Gotcha 4: DataRaptor Preview Does Not Test Permissions — It Uses Admin Context

**What happens:** DataRaptor Extract Preview retrieves records using the admin user's context, which bypasses FLS, OWD sharing, and record-level visibility rules. A DataRaptor that returns all expected fields in Preview may return null values for restricted fields when executed by a non-admin user in production.

**When it occurs:** Any DataRaptor that reads fields that have Field-Level Security restrictions on the target profile, or that reads records that are not visible to the target user under sharing rules. Common in Healthcare, Financial Services, or community-facing deployments with strict permission sets.

**How to avoid:** After DataRaptor Preview passes, execute the Integration Procedure or OmniScript that uses the DataRaptor as the target user in a deployed sandbox. Specifically check the output values for FLS-restricted fields — they will appear as null if the user lacks read permission on that field. Fix by adding the field to the target user's Field-Level Security setting, not by changing the DataRaptor mapping.
