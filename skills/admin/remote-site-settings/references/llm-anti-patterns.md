# LLM Anti-Patterns — Remote Site Settings and CSP Trusted Sites

Common mistakes AI coding assistants make when advising on Remote Site Settings.

## Anti-Pattern 1: Recommending CSP Trusted Sites to Fix Apex Callout Failures

**What the LLM generates:** "To allow Salesforce to call the external API, go to Setup > Security > CSP Trusted Sites and add your API's URL with the 'connect-src' directive enabled."

**Why it happens:** "CSP Trusted Sites" sounds like the relevant setting for allowing any kind of trusted external connection. The distinction between server-side Apex callouts and browser-side Lightning component resource loading is not widely understood.

**Correct pattern:**

```
Apex Http.send() to a raw URL → Remote Site Settings (Setup Quick Find)
Apex callout to callout:<NamedCredential> → no Remote Site Setting needed
Lightning component fetch/XHR → Trusted URL (CspTrustedSite, formerly
  CSP Trusted Sites) with isApplicableToConnectSrc
```

Grounding: apexdev 264 L34758-34762 (registration required; named credential exempt), api_meta 264 L41578-41582 and L41687 (Trusted URL, connect-src). UNVERIFIED (2026-10-21): the commonly quoted exception text "CalloutException: Unauthorized endpoint, please check Setup>Security>Remote Site Settings" — not in the corpus.

**Detection hint:** Any recommendation to add a URL to CSP Trusted Sites in response to an Apex callout error.

---

## Anti-Pattern 2: Assuming Remote Site Settings Are Automatically Included in Change Sets

**What the LLM generates:** "Deploy your Apex callout class and trigger via Change Set. Salesforce will automatically include the required Remote Site Settings as dependencies."

**Why it happens:** Change Sets offer dependency detection for some component types, and the model assumes it covers callout endpoints. UNVERIFIED (2026-10-21): Change Set dependency behaviour is Help-only — treat every Remote Site Setting as a manual add.

**Correct pattern:**

```
Add Remote Site Settings to the Change Set explicitly (auto-inclusion UNVERIFIED).
Steps to include them (UI labels UNVERIFIED, Help-only):
1. In the Change Set, click "Add"
2. Set Component Type to "Remote Site Setting"  
3. Add each required Remote Site Setting
4. Upload the Change Set
5. Deploy to production

Checklist rule: Every Change Set containing Apex callout code 
must explicitly include the dependent Remote Site Settings.
```

**Detection hint:** Any claim that Change Sets automatically include Remote Site Settings or that "Salesforce detects callout dependencies."

---

## Anti-Pattern 3: Using HTTP Instead of HTTPS in Remote Site Setting URL

**What the LLM generates:** A Remote Site Setting configuration example with `http://api.example.com` when the actual API uses `https://`.

**Why it happens:** LLMs may generate examples with HTTP because it's shorter and requires less formatting, or because the training example used HTTP. HTTP vs. HTTPS is easy to overlook in a URL.

**Correct pattern:**

```
Register the URL with the same scheme the Apex callout uses.

Best practice:
1. Copy the exact URL from the Apex code
2. Paste it directly into the Remote Site Setting URL field
3. Do not type from memory
4. Verify with System.debug(req.getEndpoint()) on the HttpRequest the
   code actually sends, after setEndpoint() has run
```

UNVERIFIED (2026-10-21): that `https://` and `http://` registrations are matched separately — the corpus does not describe URL matching.

**Detection hint:** Any Remote Site Setting URL using HTTP for an API that should use HTTPS.

---

## Anti-Pattern 4: Recommending disableProtocolSecurity for HTTPS Endpoints

**What the LLM generates:** "If you're having trouble with the callout, try setting 'Disable Protocol Security' to true in the Remote Site Setting to bypass SSL/TLS issues."

**Why it happens:** LLMs recommend permissive security settings as a troubleshooting shortcut when the root cause is unknown. The field has nothing to do with certificates: when true, "code within Salesforce can pass data from an HTTPS session to an HTTP session, and vice versa. Only set to true if you understand the security implications" (api_meta 264 L106516-106521).

**Correct pattern:**

```
disableProtocolSecurity: false (the field is Required, so always write it).
true only when code must exchange data between an HTTPS session and an
HTTP site, with the security implication signed off.
It does not disable or relax certificate validation.

If a callout fails due to SSL/TLS errors:
1. Verify the external service's certificate is valid and not expired
2. Confirm the certificate chain is complete (intermediate CAs included)
3. Contact the external service owner to fix their certificate
Do NOT work around it with disableProtocolSecurity in production.
```

**Detection hint:** Any recommendation to set `disableProtocolSecurity: true` for a production HTTPS endpoint.

---

## Anti-Pattern 5: Confusing Named Credentials With Remote Site Settings

**What the LLM generates:** "To call the external API from Apex, create a Named Credential AND a Remote Site Setting for the same URL."

**Why it happens:** Both Named Credentials and Remote Site Settings control external endpoint access. LLMs may recommend both out of caution, not knowing that Named Credentials manage their own URL allowlist internally.

**Correct pattern:**

```
When using Named Credentials for callouts:
- Named Credentials manage the URL allowlist internally
- A separate Remote Site Setting is NOT required for the Named Credential's endpoint
- The Apex callout uses the Named Credential reference (callout:NamedCredentialName/path)
  instead of a raw URL

When NOT using Named Credentials (raw URL in Apex):
- Remote Site Setting IS required for every external URL called

Named Credentials = URL allowlist + credential storage (preferred for authenticated callouts)
Remote Site Settings = URL allowlist only (for unauthenticated or manually managed callouts)
```

Grounding: "If the callout specifies a named credential as the endpoint, you don't need to configure remote site settings" (apexdev 264 L34761); the `callout:WeatherAPI/current` form appears at apexdev 264 L14799.

**Detection hint:** Any recommendation to create both a Named Credential AND a Remote Site Setting for the same endpoint when Named Credentials are in use.
