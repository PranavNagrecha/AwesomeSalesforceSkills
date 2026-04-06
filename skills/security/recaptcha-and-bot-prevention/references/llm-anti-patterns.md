# LLM Anti-Patterns — reCAPTCHA and Bot Prevention

Common mistakes AI coding assistants make when generating or advising on reCAPTCHA and Bot Prevention.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Hardcoding the reCAPTCHA Secret Key in Apex

**What the LLM generates:**

```apex
private static final String SECRET_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe';
```

**Why it happens:** Training data from tutorials and Stack Overflow answers frequently inline the secret key for brevity. LLMs replicate this pattern because it appears in thousands of examples.

**Correct pattern:**

```apex
// Retrieve from Custom Metadata — never hardcode
Recaptcha_Config__mdt config = Recaptcha_Config__mdt.getInstance('Default');
String secretKey = config.Secret_Key__c;
```

**Detection hint:** Search for string literals matching the pattern `6L[a-zA-Z0-9_-]{38}` in Apex files, or any assignment of a `SECRET` or `secret` variable to a string literal.

---

## Anti-Pattern 2: Client-Side-Only reCAPTCHA Verification

**What the LLM generates:**

```javascript
// LWC controller
grecaptcha.execute(siteKey, {action: 'submit'}).then(function(token) {
    if (token) {
        // Token exists, so user is verified — proceed to create record
        createCase({subject: this.subject, description: this.description});
    }
});
```

**Why it happens:** LLMs conflate "token was generated" with "user was verified." The presence of a token only means the reCAPTCHA script ran; it says nothing about the score or validity. Verification requires a server-side call to Google.

**Correct pattern:**

```javascript
// LWC: pass token to Apex for server-side verification
grecaptcha.execute(siteKey, {action: 'submit'}).then((token) => {
    submitWithVerification({recaptchaToken: token, subject: this.subject, description: this.description});
});
// Apex: verify token against Google API before any DML
```

**Detection hint:** Look for `createCase`, `createLead`, `insert`, or any DML call in the same client-side block as `grecaptcha.execute` without an intervening Apex server call.

---

## Anti-Pattern 3: Suggesting reCAPTCHA v2 for Headless Identity

**What the LLM generates:** "Configure reCAPTCHA v2 checkbox in your Headless Identity Settings to protect registration."

**Why it happens:** reCAPTCHA v2 is more commonly discussed in training data. LLMs default to recommending v2 because it has broader general-purpose documentation. Headless Identity's v3-only requirement is a Salesforce-specific constraint not widely represented.

**Correct pattern:**

```text
Headless Identity requires reCAPTCHA v3 exclusively. Register a v3 site key in the
Google Admin Console and configure it in Setup > Identity > Headless Identity Settings.
reCAPTCHA v2 tokens will be rejected with a generic 400 error.
```

**Detection hint:** Any mention of "reCAPTCHA v2" in the same paragraph or code block as "Headless Identity" or "headless registration."

---

## Anti-Pattern 4: Missing CSP Trusted Site for gstatic.com

**What the LLM generates:** "Add https://www.google.com to your CSP Trusted Sites to enable reCAPTCHA on your Experience Cloud site."

**Why it happens:** The primary reCAPTCHA script URL is on google.com, so LLMs recommend only that domain. The reCAPTCHA library dynamically loads additional resources from gstatic.com, which is not mentioned in most tutorials.

**Correct pattern:**

```text
Add BOTH of these as CSP Trusted Sites with "Allow site for scripts" enabled:
  1. https://www.google.com
  2. https://www.gstatic.com

Also add https://www.google.com as a Remote Site Setting for the server-side
verification callout (this is separate from CSP and serves a different purpose).
```

**Detection hint:** Instructions that mention CSP Trusted Sites with only `google.com` and no mention of `gstatic.com`.

---

## Anti-Pattern 5: Generating reCAPTCHA Token on Page Load Instead of Submit

**What the LLM generates:**

```javascript
connectedCallback() {
    // Generate token when page loads
    grecaptcha.ready(() => {
        grecaptcha.execute(siteKey, {action: 'pageload'}).then((token) => {
            this.recaptchaToken = token;
        });
    });
}
```

**Why it happens:** LLMs place initialization logic in lifecycle hooks like `connectedCallback` or `ngOnInit` by default. This pattern works for analytics tokens but fails for form protection because reCAPTCHA tokens expire after 120 seconds.

**Correct pattern:**

```javascript
handleSubmit() {
    // Generate token at the moment of submission — tokens expire in 120 seconds
    grecaptcha.ready(() => {
        grecaptcha.execute(siteKey, {action: 'submit'}).then((token) => {
            this.verifyAndSubmit(token);
        });
    });
}
```

**Detection hint:** `grecaptcha.execute` called inside `connectedCallback`, `renderedCallback`, `ngOnInit`, `componentDidMount`, or any lifecycle/init method rather than a submit handler.

---

## Anti-Pattern 6: Omitting Error Handling for the Google Verification Callout

**What the LLM generates:**

```apex
HttpResponse res = new Http().send(req);
Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
Boolean success = (Boolean) result.get('success');
// Proceed based on success flag only
```

**Why it happens:** LLMs generate the "happy path" and skip HTTP error handling, callout timeout scenarios, and malformed response parsing. In production, the Google API can return 5xx errors, and the Apex HTTP callout can time out.

**Correct pattern:**

```apex
HttpResponse res = new Http().send(req);
if (res.getStatusCode() != 200) {
    // Log the failure and decide: block submission or allow with reduced confidence
    System.debug(LoggingLevel.ERROR, 'reCAPTCHA API returned ' + res.getStatusCode());
    throw new AuraHandledException('Verification service temporarily unavailable. Please try again.');
}
Map<String, Object> result = (Map<String, Object>) JSON.deserializeUntyped(res.getBody());
if (result == null || !result.containsKey('success')) {
    throw new AuraHandledException('Invalid verification response.');
}
```

**Detection hint:** `new Http().send(req)` followed immediately by `JSON.deserializeUntyped(res.getBody())` without a status code check.
