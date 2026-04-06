# LLM Anti-Patterns — Environment-Specific Value Injection

Common mistakes AI coding assistants make when generating or advising on environment-specific value injection for Salesforce. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Storing API Keys or Passwords Directly in Custom Metadata Records

**What the LLM generates:** "Create a Custom Metadata Type `OrgSettings__mdt` with a field `APIKey__c` (Text). Set the value per environment in the record and query it in Apex."

**Why it happens:** LLMs are trained on examples where Custom Metadata is used for configuration and correctly associate it with "per-org, deployable values." The distinction between config and secrets is underweighted in training data because most tutorial content skips secret management.

**Correct pattern:**

```
- Non-sensitive config (URLs, thresholds, flags) → Custom Metadata records
- Secrets (API keys, passwords, tokens, client secrets) → Named Credentials or External Credentials
  - Never store secrets in CMT fields, even in protected records
  - The platform provides no encryption-at-rest guarantee for CMT field values beyond standard org security
```

**Detection hint:** Any suggestion to create a CMT field named `APIKey`, `Password`, `Token`, `Secret`, `ClientSecret`, or `AccessToken` is a red flag.

---

## Anti-Pattern 2: Suggesting `replaceWithEnv` for Credential Values (Passwords, Tokens)

**What the LLM generates:** A `sfdx-project.json` replacements block that substitutes `${API_PASSWORD}` in a Named Credential XML with the actual password from a CI environment variable.

**Why it happens:** The `replaceWithEnv` mechanism is documented as the way to inject environment-specific values at deploy time. LLMs correctly identify the problem (secret must differ per env) but apply the wrong tool (string replacement makes the secret visible in the deployed org's metadata record, where it can be retrieved).

**Correct pattern:**

```
# sfdx-project.json replacements: use for non-sensitive URLs and config only
{
  "replacements": [
    {
      "filename": "namedCredentials/MyAPI.namedCredential",
      "stringToReplace": "${MY_API_ENDPOINT}",
      "replaceWithEnv": "MY_API_ENDPOINT"
    }
  ]
}

# For passwords/tokens: deploy the stub, then populate via Tooling API post-deploy
# The password never appears in any metadata file or deployment artifact
python3 scripts/populate_named_credentials.py \
  --instance-url $SF_INSTANCE_URL \
  --access-token $SF_ACCESS_TOKEN \
  --credential-name MyAPI \
  --password-env MY_API_PASSWORD
```

**Detection hint:** Any `replaceWithEnv` entry whose variable name contains `PASSWORD`, `TOKEN`, `SECRET`, `KEY`, or `CREDENTIAL` should be reviewed — those values should use post-deploy API population, not string replacement.

---

## Anti-Pattern 3: Hardcoding Per-Environment Values in Apex Using Org URL Detection

**What the LLM generates:**

```apex
public class ConfigService {
    private static final String SANDBOX_ENDPOINT = 'https://sandbox.api.example.com';
    private static final String PROD_ENDPOINT = 'https://api.example.com';

    public static String getEndpoint() {
        String baseUrl = URL.getSalesforceBaseUrl().toExternalForm();
        return baseUrl.contains('sandbox') ? SANDBOX_ENDPOINT : PROD_ENDPOINT;
    }
}
```

**Why it happens:** This pattern works and is simple. LLMs see it in codebases and reproduce it. The training signal emphasizes "it works" over "it creates maintenance debt and hard-coded assumptions."

**Correct pattern:**

```apex
// Use a Named Credential - Apex never hardcodes endpoint URLs
HttpRequest req = new HttpRequest();
req.setEndpoint('callout:ExternalAPI/v1/resource');
req.setMethod('GET');
Http http = new Http();
HttpResponse res = http.send(req);

// Or use Custom Metadata for non-secret config
OrgSettings__mdt settings = OrgSettings__mdt.getInstance('Default');
String routingQueue = settings.DefaultQueueApiName__c;
```

**Detection hint:** Any Apex that uses `URL.getSalesforceBaseUrl()` to branch endpoint behavior, or that contains both a `*_SANDBOX_*` and `*_PROD_*` constant for the same concept, is using this anti-pattern.

---

## Anti-Pattern 4: Recommending Change Sets for Named Credential Deployment Without Noting the String Replacement Gap

**What the LLM generates:** "Deploy the Named Credential using a change set. Add the `${PLACEHOLDER}` token to the callout URL and the system will substitute it." — or, more commonly, the LLM recommends a Named Credential deployment approach without mentioning that sfdx string replacement does not apply to change sets.

**Why it happens:** LLMs conflate "sfdx project deployment" with all Salesforce deployment mechanisms. The `replacements` key in `sfdx-project.json` is a CLI-only feature; its scope is not always clear from documentation summaries in training data.

**Correct pattern:**

```
String replacement (replaceWithEnv) ONLY applies to:
  - sf project deploy start
  - sf project deploy validate
  - sf project source push (scratch orgs)

String replacement does NOT apply to:
  - Change sets
  - sf package version create (2GP)
  - Metadata API direct calls
  - OmniStudio DataPack imports

For non-sfdx deployment paths:
  - Use Custom Metadata records for non-sensitive config (they deploy natively with any method)
  - Use post-deploy manual Setup entry or a Tooling API script for Named Credential credentials
  - Document the manual step in the deployment runbook
```

**Detection hint:** Any recommendation that includes both "change set" and "replaceWithEnv" in the same deployment plan.

---

## Anti-Pattern 5: Forgetting Post-Deploy Credential Population After Sandbox Refresh

**What the LLM generates:** A sandbox refresh runbook that deploys metadata (including Named Credential stubs) but has no step for populating Named Credential credentials. The runbook ends with "deploy the latest code from your CI pipeline" without noting that callouts will fail until credentials are entered.

**Why it happens:** Sandbox refresh and credential population are separate workflows. LLMs that know both independently often fail to compose them correctly because the gap — the period between deploy and working callouts — is rarely documented explicitly in training data.

**Correct pattern:**

```
Sandbox refresh post-deploy checklist must include:
  1. Verify deployment completed: sf project deploy report --job-id $JOB_ID
  2. Populate Named Credential credentials (automated or manual):
     - Option A: Run populate_named_credentials.py with sandbox-specific secrets
     - Option B: Setup > Named Credentials > Edit each credential > Enter password/token
  3. Validate callouts: run a smoke test script that exercises each Named Credential
     and asserts HTTP 200 (or the expected non-4xx status) before marking refresh complete
  4. Update Custom Metadata records if sandbox-specific values differ from the defaults
     deployed from source control
```

**Detection hint:** Any sandbox refresh runbook that includes a Named Credential deploy step but has no subsequent "validate Named Credential callouts" step.

---

## Anti-Pattern 6: Using the Legacy Named Credential Model (Pre-v57.0) in New Implementations

**What the LLM generates:** Named Credential XML that uses the single-object model with `<protocol>Password</protocol>` and `<Username>` and `<Password>` fields directly in the NamedCredential metadata type, or Tooling API scripts that PATCH `/tooling/sobjects/NamedCredential/{id}` to set a password field.

**Why it happens:** The pre-v57.0 Named Credential model is widely documented in older tutorials and Stack Overflow answers. LLMs are trained on this content and reproduce the legacy approach even when generating for a Spring '25 org.

**Correct pattern:**

```
As of API v57.0 (Summer '23+), use the split model:
  - ExternalCredential: holds authentication type, principal, and credential
  - NamedCredential: holds the callout base URL and references the ExternalCredential

Post-deploy credential population targets ExternalCredentialPrincipal, not NamedCredential:
  PATCH /services/data/v63.0/tooling/sobjects/ExternalCredentialPrincipal/{id}
  Body: {"Credentials": {"Password": "...", "Username": "..."}}

New implementations should use sourceApiVersion 57.0+ and the split model.
Legacy single-object Named Credentials still work but are the old model.
```

**Detection hint:** Named Credential XML containing `<protocol>Password</protocol>` with `<Username>` and `<Password>` as direct child elements, or Tooling API calls to `/tooling/sobjects/NamedCredential/{id}` that attempt to set password/token fields.
