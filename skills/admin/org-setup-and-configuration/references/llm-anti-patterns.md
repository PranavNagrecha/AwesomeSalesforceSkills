# LLM Anti-Patterns — Org Setup and Configuration

Common mistakes AI coding assistants make when generating or advising on Salesforce org-wide setup and platform configuration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Suggesting MFA exemptions instead of proper MFA enrollment

**What the LLM generates:** "If users are having trouble with MFA, add their IP addresses to the trusted IP ranges to bypass MFA."

**Why it happens:** LLMs solve MFA friction by bypassing it. Trusted IP ranges skip identity verification (email/SMS challenges), but they do NOT exempt users from MFA if MFA is enforced at the org level. Since February 2022, Salesforce contractually requires MFA for all direct UI logins. Adding trusted IPs does not satisfy the MFA requirement.

**Correct pattern:**

```
MFA enforcement is required, not optional:
1. Enable MFA: Setup → Identity → Multi-Factor Authentication.
   Or: enable via the "Multi-Factor Authentication for Direct UI Logins"
   permission on all user profiles.
2. Supported MFA methods:
   - Salesforce Authenticator app (recommended).
   - TOTP authenticator apps (Google Authenticator, Authy).
   - Security keys (FIDO U2F/WebAuthn).
3. Trusted IP ranges skip email/SMS identity challenges but
   do NOT replace MFA.
4. SSO with IdP-level MFA satisfies the requirement
   (MFA is at the IdP, not Salesforce directly).
5. For users with MFA issues: help them re-register their
   authenticator, do not bypass MFA.
```

**Detection hint:** If the output suggests trusted IP ranges or other mechanisms to "bypass" or "skip" MFA, it is undermining a contractual requirement. Search for `bypass MFA`, `skip MFA`, or `exempt` combined with MFA.

---

## Anti-Pattern 2: Deploying My Domain without understanding the impact on existing integrations

**What the LLM generates:** "Go to Setup → My Domain, enter your domain name, and deploy it to users."

**Why it happens:** LLMs describe My Domain deployment as a simple rename. Deploying My Domain changes the org's login URL and API endpoints. Existing integrations, bookmarks, SSO configurations, and CORS settings that reference the old instance URL (e.g., na123.salesforce.com) will break.

**Correct pattern:**

```
My Domain deployment checklist:
1. Register the My Domain name (Setup → My Domain).
2. BEFORE deploying to users:
   a. Inventory all integrations using the org's instance URL.
   b. Update SSO/SAML configurations to use the My Domain URL.
   c. Update Connected App callback URLs.
   d. Update CORS allowed origins.
   e. Notify users that bookmarks will change.
   f. Update any hardcoded URLs in Apex, Visualforce, or LWC.
3. Test the My Domain URL in a sandbox first.
4. Deploy to users during a maintenance window.
5. After deployment: the old instance URL redirects for a period,
   but integrations should be updated to the My Domain URL.
```

**Detection hint:** If the output deploys My Domain without mentioning integration impact, SSO updates, or URL changes, the deployment is under-planned. Search for `integration`, `SSO`, or `URL` in the My Domain deployment steps.

---

## Anti-Pattern 3: Setting password policies that are too aggressive or too lenient

**What the LLM generates:** "Set passwords to expire every 30 days with a minimum length of 8 characters."

**Why it happens:** LLMs apply generic password policy advice without considering Salesforce-specific settings and current NIST guidance. NIST SP 800-63B recommends against frequent forced rotation (it leads to weaker passwords). A 30-day expiration causes user fatigue. Conversely, some LLMs set no expiration at all.

**Correct pattern:**

```
Balanced password policy (aligned with NIST 800-63B):
1. Minimum length: 12+ characters (stronger than 8).
2. Password expiration: 90-180 days (or never, if MFA is enforced).
   Avoid 30-day rotation — it encourages weak patterns.
3. Password complexity: require letters + numbers + special characters,
   OR use a longer minimum length without complexity rules.
4. Lockout: 5 failed attempts, lockout for 15-30 minutes.
5. Password history: remember last 12 passwords.
6. Configure at: Setup → Security → Password Policies.
7. Factor in that MFA is the primary security control —
   password policy is the secondary layer.
```

**Detection hint:** If the output sets password expiration to 30 days or less, or sets minimum length below 10, the policy may be counterproductive. Check the expiration interval and minimum length values.

---

## Anti-Pattern 4: Adding overly broad trusted IP ranges

**What the LLM generates:** "Add 0.0.0.0 to 255.255.255.255 as a trusted IP range to prevent login challenges for all users."

**Why it happens:** LLMs solve login friction by trusting all IPs. This effectively disables IP-based identity verification, which is a security control that detects logins from unknown locations. Trusted IP ranges should be limited to known corporate networks, VPN ranges, and specific office locations.

**Correct pattern:**

```
Trusted IP range configuration:
1. Setup → Security → Network Access.
2. Add ONLY known, controlled network ranges:
   - Corporate office IP ranges.
   - VPN exit point IP ranges.
   - Managed service provider IP ranges.
3. Do NOT trust:
   - 0.0.0.0/0 (all IPs — defeats the purpose).
   - Broad ISP ranges (residential users share these).
4. For remote workers without VPN:
   - Accept the login challenge (email/SMS verification).
   - Or enforce MFA (which supersedes IP-based challenges).
5. Document each trusted range with a description of what
   network it represents and when it was added.
```

**Detection hint:** If the output adds a range broader than /16 (65,536 IPs) or includes 0.0.0.0, the range is too broad. Check the IP range width.

---

## Anti-Pattern 5: Forgetting to add external domains to CSP Trusted Sites

**What the LLM generates:** "Embed the external JavaScript library on your Lightning page. It will load automatically."

**Why it happens:** LLMs focus on the component code and forget the Content Security Policy (CSP) enforcement in Lightning Experience. Lightning pages block external resources (scripts, images, fonts, iframes) unless the domain is added to CSP Trusted Sites in Setup. Missing CSP entries cause silent loading failures with no visible error to the user.

**Correct pattern:**

```
CSP Trusted Sites configuration:
1. Setup → Security → CSP Trusted Sites → New.
2. Enter the external domain (e.g., cdn.example.com).
3. Select the CSP directive:
   - script-src: for JavaScript files.
   - img-src: for images.
   - font-src: for web fonts.
   - frame-src: for iframes.
   - connect-src: for XHR/fetch API calls.
   - style-src: for external CSS.
4. Enable for the appropriate context (Lightning Experience, Communities, or both).
5. Test the page after adding the trusted site.
6. For LWC/Aura components making callouts: the endpoint domain must
   also be in Remote Site Settings or Named Credentials.
```

**Detection hint:** If the output references loading external resources on a Lightning page without mentioning CSP Trusted Sites, the resource will be blocked. Search for `CSP Trusted Sites` or `Content Security Policy` when external domains are referenced.
