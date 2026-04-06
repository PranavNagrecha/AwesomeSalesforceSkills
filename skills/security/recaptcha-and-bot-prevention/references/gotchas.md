# Gotchas — reCAPTCHA and Bot Prevention

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Enabling the reCAPTCHA Toggle Breaks Existing Deployed Forms

**What happens:** After enabling "Require reCAPTCHA Verification" in Web-to-Case or Web-to-Lead settings, all previously deployed HTML forms that lack the reCAPTCHA widget stop working. Submissions are silently dropped by Salesforce — no error is returned to the user, and no Case or Lead is created.

**When it occurs:** Every time the toggle is enabled without regenerating and redeploying the HTML snippet. This catches teams who enable the setting "just to be safe" without coordinating with the team that manages the external website.

**How to avoid:** Treat enabling the reCAPTCHA toggle as a two-step deployment: (1) enable in Setup and regenerate the HTML, (2) deploy the new HTML to all external sites simultaneously. Communicate the change to every team that embeds the form. Test from an incognito browser after deployment.

---

## Gotcha 2: reCAPTCHA Tokens Expire After 120 Seconds

**What happens:** The reCAPTCHA token generated client-side is valid for only 2 minutes. If a user takes longer than 2 minutes to complete the form after the token is generated, the server-side verification call to Google returns `timeout-or-duplicate` and the submission fails.

**When it occurs:** Long forms with many fields, forms that generate the token on page load instead of on submit, or slow Apex processing chains that delay the verification callout.

**How to avoid:** Generate the reCAPTCHA token at the moment of form submission, not on page load. For reCAPTCHA v3, call `grecaptcha.execute()` inside the submit handler immediately before the Apex callout. For v2 invisible, trigger `grecaptcha.execute()` on submit and wait for the callback before proceeding.

---

## Gotcha 3: CSP Trusted Sites Must Include Both google.com and gstatic.com

**What happens:** The reCAPTCHA JavaScript library is loaded from `https://www.google.com/recaptcha/api.js`, but it dynamically fetches additional resources from `https://www.gstatic.com`. If only `google.com` is added to CSP Trusted Sites, the initial script loads but the widget fails to render. There is no visible error in the UI — the CAPTCHA area is simply blank.

**When it occurs:** Every custom reCAPTCHA implementation in Experience Cloud where the developer adds only the primary domain to CSP.

**How to avoid:** Add both `https://www.google.com` and `https://www.gstatic.com` as CSP Trusted Sites with the "Allow site for scripts" directive. Also add `https://www.google.com` as a Remote Site Setting for the server-side verification callout (this is separate from CSP).

---

## Gotcha 4: reCAPTCHA v3 Score Threshold Is Not One-Size-Fits-All

**What happens:** Teams deploy reCAPTCHA v3 with the default score threshold of 0.5 and never adjust it. Some orgs find that 0.5 is too permissive (bots still get through), while others find it too strict (legitimate users on VPNs or older browsers score below 0.5 and are blocked).

**When it occurs:** After initial deployment when real traffic patterns differ from testing patterns. Mobile users and users behind corporate proxies frequently score lower than expected.

**How to avoid:** Log the reCAPTCHA score for every submission for the first 2-4 weeks without hard-blocking below a threshold. Analyze the score distribution to find the natural separation point between human and bot traffic. Set the threshold based on observed data, not the Google-suggested default.

---

## Gotcha 5: Sandbox Orgs Do Not Have Separate reCAPTCHA Keys By Default

**What happens:** If you use the same reCAPTCHA keys in production and sandbox, test submissions from sandbox count against your Google reCAPTCHA analytics and can skew your score distribution data. Worse, if you use test keys in production by mistake, reCAPTCHA always returns success, providing zero protection.

**When it occurs:** During sandbox refresh or when promoting configurations from sandbox to production without environment-specific key management.

**How to avoid:** Register separate reCAPTCHA site key pairs for each environment in the Google Admin Console. Store keys in Custom Metadata Type records so they can be set independently per org. Verify after every sandbox refresh that the keys are pointing to the correct environment-specific values.
