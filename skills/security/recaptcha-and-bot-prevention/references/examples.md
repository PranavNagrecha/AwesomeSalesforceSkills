# Examples — reCAPTCHA and Bot Prevention

## Example 1: Server-Side reCAPTCHA v3 Verification for Experience Cloud LWC Form

**Context:** An Experience Cloud site has a custom LWC contact-us form accessible to guest users. Bots are submitting hundreds of spam cases per day.

**Problem:** Without server-side reCAPTCHA verification, any HTTP POST with valid field data creates a Case. The LWC has no built-in reCAPTCHA toggle because it is a custom component, not the standard Web-to-Case form.

**Solution:**

```apex
public with sharing class RecaptchaVerificationService {

    private static final String RECAPTCHA_VERIFY_URL = 'https://www.google.com/recaptcha/api/siteverify';
    private static final Decimal MINIMUM_SCORE = 0.5;

    @AuraEnabled
    public static Id submitContactForm(String recaptchaToken, String subject, String description) {
        if (String.isBlank(recaptchaToken)) {
            throw new AuraHandledException('reCAPTCHA token is required.');
        }

        // Retrieve the secret key from Custom Metadata — never hardcode
        Recaptcha_Config__mdt config = Recaptcha_Config__mdt.getInstance('Default');
        String secretKey = config.Secret_Key__c;

        HttpRequest req = new HttpRequest();
        req.setEndpoint(RECAPTCHA_VERIFY_URL);
        req.setMethod('POST');
        req.setHeader('Content-Type', 'application/x-www-form-urlencoded');
        req.setBody('secret=' + EncodingUtil.urlEncode(secretKey, 'UTF-8')
                   + '&response=' + EncodingUtil.urlEncode(recaptchaToken, 'UTF-8'));

        HttpResponse res = new Http().send(req);

        if (res.getStatusCode() != 200) {
            throw new AuraHandledException('reCAPTCHA verification service unavailable.');
        }

        Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
        Boolean success = (Boolean) result.get('success');
        Decimal score = (Decimal) result.get('score');

        if (!success || score == null || score < MINIMUM_SCORE) {
            throw new AuraHandledException('Verification failed. Please try again.');
        }

        Case c = new Case(Subject = subject, Description = description, Origin = 'Web');
        insert c;
        return c.Id;
    }
}
```

**Why it works:** The token is verified server-side against Google before any DML occurs. The secret key lives in Custom Metadata, not in source code. The v3 score threshold rejects low-confidence submissions without requiring an interactive challenge from legitimate users.

---

## Example 2: Enabling Built-In reCAPTCHA for Web-to-Lead with Redeployment

**Context:** A marketing team uses the standard Salesforce Web-to-Lead HTML form embedded on a WordPress landing page. The form was generated months ago and deployed without reCAPTCHA. Spam leads have been increasing.

**Problem:** The team enables "Require reCAPTCHA Verification" in Setup but does not regenerate the HTML. Existing form submissions begin failing silently because Salesforce now expects a reCAPTCHA response parameter that the old HTML never sends.

**Solution:**

```text
Step 1: Setup > Web-to-Lead > check "Require reCAPTCHA Verification"
Step 2: Click "Generate Web-to-Lead Form" to produce a new HTML snippet
Step 3: Copy the new HTML — it now includes the reCAPTCHA script tag and widget div
Step 4: Replace the old form HTML on the WordPress page with the new snippet
Step 5: Test from an incognito browser to confirm the reCAPTCHA checkbox appears
Step 6: Submit a test lead and verify it appears in Salesforce
```

**Why it works:** The reCAPTCHA verification is enforced server-side by Salesforce. Without the widget in the HTML, the form cannot produce the required token, and Salesforce silently drops the submission. Regenerating the snippet is the mandatory step that teams miss.

---

## Example 3: Headless Identity reCAPTCHA v3 Configuration

**Context:** A fintech company uses Salesforce Headless Identity for passwordless registration in their mobile app. They need to enable reCAPTCHA v3 to comply with their security policy before launch.

**Problem:** The team initially configures a reCAPTCHA v2 key in Headless Identity Settings. Registration API calls fail with a generic 400 error that does not indicate a version mismatch.

**Solution:**

```text
Step 1: Go to Google reCAPTCHA Admin Console
Step 2: Create a NEW site key — select "reCAPTCHA v3" (NOT v2 checkbox or v2 invisible)
Step 3: Add your mobile app's domain (or use the package name for Android / bundle ID for iOS)
Step 4: Copy the v3 site key and secret key
Step 5: In Salesforce Setup > Identity > Headless Identity Settings:
        - Paste the v3 site key into "reCAPTCHA Site Key"
        - Paste the v3 secret key into "reCAPTCHA Secret Key"
        - Set score threshold to 0.5 (adjust after observing real traffic)
Step 6: In your mobile app, integrate the reCAPTCHA v3 SDK and pass the token
        in the X-Recaptcha-Token header on every Headless Identity API call
Step 7: Test registration — a valid v3 token should return 200; missing or invalid tokens return 400
```

**Why it works:** Headless Identity exclusively supports reCAPTCHA v3. The score-based approach avoids user-facing challenges in a mobile context where checkbox or image CAPTCHA would break the UX.

---

## Anti-Pattern: Hardcoding reCAPTCHA Secret Key in Apex

**What practitioners do:** Store the Google reCAPTCHA secret key directly in an Apex constant (`private static final String SECRET = 'xxxx...'`) for simplicity.

**What goes wrong:** The secret key is visible in version-controlled source code, accessible to any developer with repo access, and exposed in the Salesforce metadata API. If the key is compromised, attackers can forge verification responses. Rotating the key requires a code deployment.

**Correct approach:** Store the secret key in a Custom Metadata Type record (e.g., `Recaptcha_Config__mdt`) or a Named Credential. These can be updated without code deployments, support environment-specific values across sandboxes, and are not exposed in source control.
