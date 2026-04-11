# Gotchas — FSC Document Generation

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: DocGen Runtime License Is Not Inherited from DocGen User

**What happens:** Automated DocGen API calls — from batch Apex, scheduled jobs, or Flow — fail with a permission error or silently return no output, even though the same template works correctly when triggered from the UI by a human user.

**When it occurs:** When the integration user or system context running the automated job has the `DocGen User` permission set license but not the `DocGen Runtime` permission set license. OmniStudio DocGen enforces separate licenses for interactive UI generation (DocGen User) and headless server-side API generation (DocGen Runtime). Interactive sandbox testing typically uses a developer's personal account, which has both; the integration user set up for production batch processing often has only one.

**How to avoid:** Audit all users configured to run automated DocGen jobs and confirm they have the `DocGen Runtime` permission set license explicitly assigned. Add a pre-deployment check that queries `PermissionSetLicenseAssign` for the integration user. Test batch generation with the actual integration user credentials in a full-copy sandbox before go-live, not just with a developer account.

---

## Gotcha 2: AuthorizationFormConsent Is Not Automatically Created by DocGen

**What happens:** DocGen generates and stores the PDF correctly, but there is no `AuthorizationFormConsent` record and no structured proof of delivery. Compliance officers cannot query FSC for disclosure delivery status, and the org fails a FINRA or GDPR audit because the machine-readable audit trail is absent.

**When it occurs:** When practitioners treat document generation as complete once the PDF is stored as a `ContentDocument`. OmniStudio DocGen has no built-in Disclosure and Compliance Hub integration — it generates and stores documents, but it does not automatically write `AuthorizationFormConsent`, `AuthorizationFormDataUse`, or any other compliance record. The integration must be explicitly coded in the OmniScript action, Apex class, or Flow that invokes DocGen.

**How to avoid:** Always treat the `AuthorizationFormConsent` write as a mandatory post-DocGen step in every FSC compliance document workflow. Include it in the OmniScript flow action sequence or the Apex service class that orchestrates DocGen calls. Write automated tests that assert the consent record exists with the correct `Status`, `ConsentGivenAt`, and parent `AuthorizationFormId` after every document generation event.

---

## Gotcha 3: The 1000 Documents/Hour DocGen API Cap Is Enforced Per Org, Not Per Job

**What happens:** A batch Apex job processing account statements appears to run successfully — no Apex exceptions, no job failures — but a large subset of documents is not generated. The PDF count attached to FinancialAccounts is lower than expected, and retry logic is absent because the job did not raise an error.

**When it occurs:** The DocGen server-side API enforces a hard cap of 1000 documents per hour at the org level. This cap applies to all DocGen activity across all jobs and users in the org simultaneously. If multiple batch jobs, OmniScripts, or Flow activations are generating documents concurrently, they share this quota. When the cap is reached, additional requests are rejected but the rejection may not surface as an Apex exception depending on how the callout response is handled. Because the cap is org-wide, a separate ad-hoc disclosure delivery run during the same hour can consume quota the nightly statement job was relying on.

**How to avoid:** Schedule nightly batch statement jobs during off-peak hours when other DocGen activity is minimal (late night/early morning). Implement explicit HTTP response code handling in the DocGen callout wrapper — a 429 or 503 response indicates rate limiting and should trigger an exponential back-off retry. Log the number of successful and failed document requests per batch execution to detect partial completions. If volume consistently approaches the cap, contact Salesforce to discuss entitlement increases.

---

## Gotcha 4: ContentDocument Sharing Model Blocks Portal Delivery

**What happens:** Account statements are generated successfully and stored as `ContentDocument` records on the `FinancialAccount`, but clients accessing the Experience Cloud portal cannot see them. The documents exist in Salesforce but are invisible to the portal user.

**When it occurs:** `ContentDocumentLink` records control visibility. When DocGen stores the PDF, it creates a `ContentDocumentLink` with `ShareType = 'I'` (Inferred) by default, which does not grant Experience Cloud guest or authenticated users access. The portal user's profile typically has no direct access to the `FinancialAccount` object or its related files unless a `ContentDistribution` record or an explicit `ContentDocumentLink` with `ShareType = 'V'` and `Visibility = 'AllUsers'` is created.

**How to avoid:** After DocGen generates the PDF, the post-generation Apex service must explicitly create a `ContentDocumentLink` with `ShareType = 'V'` and `Visibility = 'AllUsers'` (or `'SharedUsers'` if the portal uses authenticated sessions) linked to the portal-accessible parent record (often the `Contact` or `Account`, not the `FinancialAccount`). Test portal document visibility end-to-end with a real portal user session before go-live.

---

## Gotcha 5: DataRaptor Extract Field Paths Are Case-Sensitive and Break Silently

**What happens:** The DocGen template renders with blank merge fields or missing data sections even though the underlying records have the correct data populated. No error is thrown; the PDF is generated but incomplete.

**When it occurs:** OmniStudio DataRaptor Extract is strict about field API name casing and relationship path notation. A merge field path like `FinancialAccount.Owner.Name` will return blank if the correct path is `FinancialAccount.Owner__r.Name` (for a custom relationship) or if the DataRaptor output key casing does not exactly match the template merge field key. The silent failure mode is the danger: DocGen does not throw an error when a merge field key resolves to empty — it simply renders the field as blank.

**How to avoid:** Test the DataRaptor Extract independently using the OmniStudio Preview tool against multiple real records, including edge cases (missing related records, null fields). Verify every output key in the DataRaptor matches the merge field key in the Word template character-for-character, including case. Add required-field validation in the OmniScript or Apex layer to catch null data before invoking DocGen, rather than discovering blanks in the rendered PDF during user acceptance testing.
