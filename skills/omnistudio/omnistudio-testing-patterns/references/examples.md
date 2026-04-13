# Examples — OmniStudio Testing Patterns

## Example 1: Debugging a Failing Integration Procedure Step

**Context:** A loan origination OmniScript calls a multi-step Integration Procedure that retrieves applicant credit data from an external system via a Named Credential. In UAT, the OmniScript shows "Integration Procedure Error" without detail when an agent submits the application form.

**Problem:** The error surface in the OmniScript is generic — it does not indicate which of the eight IP steps failed. Developers attempt to reproduce by running the full OmniScript as admin and cannot replicate the error.

**Solution:**

Open the Integration Procedure designer. Navigate to each step in order and use the Test Execution tab. Supply the input JSON that would reach each step (use a known-good UAT payload). For the step calling the Named Credential:

```json
{
  "ApplicantId": "001XXXXXXXXXXXXXXX",
  "SSN": "REDACTED",
  "BureauEndpoint": "prod"
}
```

Execute the step. The response shows:

```json
{
  "vlcStatus": "error",
  "errorMessage": "Named credential 'CreditBureau_Prod' is not accessible for this user",
  "responseTime": 0
}
```

The Named Credential permission assignment was missing from the permission set used by the integration-user profile running the IP in UAT. Admin Preview masked this because admin users have implicit access.

**Why it works:** IP Test Execution evaluates Named Credentials at execution time using the designer's admin context, but the error message is specific enough to identify the permission gap. Deploy a fix to the permission set and retest in deployed UAT as the target profile.

---

## Example 2: DataRaptor Transform Producing Empty Output

**Context:** An OmniScript collects policy renewal data and uses a DataRaptor Transform to reformat JSON fields before passing them to an Integration Procedure HTTP callout. The IP receives blank values for the transformed fields in production.

**Problem:** The OmniScript Preview shows the correct values in the rendered fields, but after submission the IP step logs show blank transformed data. The bug is in the DataRaptor Transform mapping but is invisible in OmniScript Preview because Preview does not execute DataRaptor Transforms — it only renders the OmniScript form.

**Solution:**

Open the DataRaptor Transform in the designer. Navigate to the Preview tab. Enter the JSON that the OmniScript would pass:

```json
{
  "PolicyNumber": "POL-2025-0012",
  "RenewalDate": "2025-08-01",
  "PremiumAmount": 1250.00
}
```

Run the Preview. The output shows `PremiumAmount` as null. Inspect the formula in the Transform mapping — the field path uses `PremiumAmt` (truncated) instead of `PremiumAmount`. Fix the field path, re-run Preview to confirm, then save and re-test the Integration Procedure.

**Why it works:** DataRaptor Preview isolates the Transform from the full OmniScript, exposing field path errors that would otherwise require a full deployed run to detect.

---

## Anti-Pattern: Treating OmniScript Preview as Final Sign-Off

**What practitioners do:** Teams run OmniScript Preview in the designer, confirm the form renders correctly with all fields visible and validation logic working, and mark the component ready for production.

**What goes wrong:** Preview runs as the admin user, which bypasses FLS, object permissions, and Experience Cloud guest-user profiles. Navigation Actions (Save, Navigate, Cancel steps) are silently skipped. In production, community guest users see blank fields due to FLS restrictions the admin Preview never hit. Save Navigation Actions fail because the guest user lacks create/edit permission on the target object.

**Correct approach:** Use Preview as a first-pass structural validator only. After Preview, deploy to a sandbox and manually execute the OmniScript as a user with the production target profile. Specifically test each Navigation Action step. For Experience Cloud deployments, create a guest-user test session or use Login-As on a restricted profile. Never mark a component ready for production based on Preview alone.
