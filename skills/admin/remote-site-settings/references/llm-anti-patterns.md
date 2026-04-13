# LLM Anti-Patterns — Remote Site Settings and CSP Trusted Sites

Common mistakes AI coding assistants make when advising on Remote Site Settings.

## Anti-Pattern 1: Recommending CSP Trusted Sites to Fix Apex Callout Failures

**What the LLM generates:** "To allow Salesforce to call the external API, go to Setup > Security > CSP Trusted Sites and add your API's URL with the 'connect-src' directive enabled."

**Why it happens:** "CSP Trusted Sites" sounds like the relevant setting for allowing any kind of trusted external connection. The distinction between server-side Apex callouts and browser-side Lightning component resource loading is not widely understood.

**Correct pattern:**

```
Apex Http.send() callouts → Remote Site Settings (Setup > Security > Remote Site Settings)
Lightning component fetch/XHR → CSP Trusted Sites (Setup > Security > CSP Trusted Sites)

The error message for a failing Apex callout is:
"CalloutException: Unauthorized endpoint, please check Setup>Security>Remote Site Settings"
The fix location is in the error message itself — always follow it.
```

**Detection hint:** Any recommendation to add a URL to CSP Trusted Sites in response to an Apex callout error.

---

## Anti-Pattern 2: Assuming Remote Site Settings Are Automatically Included in Change Sets

**What the LLM generates:** "Deploy your Apex callout class and trigger via Change Set. Salesforce will automatically include the required Remote Site Settings as dependencies."

**Why it happens:** Change Sets do automatic dependency detection for some component types (e.g., Apex classes referenced by other classes). Remote Site Settings are NOT included in this automatic dependency detection.

**Correct pattern:**

```
Remote Site Settings are NOT automatically included in Change Sets.
Steps to include them:
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
Remote Site Setting URL must EXACTLY match the protocol in the Apex callout.

https://api.example.com ≠ http://api.example.com (different entries)

Best practice:
1. Copy the exact URL from the Apex code
2. Paste it directly into the Remote Site Setting URL field
3. Do not type from memory
4. Verify with: System.debug(new HttpRequest().getEndpoint()) in anonymous Apex
```

**Detection hint:** Any Remote Site Setting URL using HTTP for an API that should use HTTPS.

---

## Anti-Pattern 4: Recommending disableProtocolSecurity for HTTPS Endpoints

**What the LLM generates:** "If you're having trouble with the callout, try setting 'Disable Protocol Security' to true in the Remote Site Setting to bypass SSL/TLS issues."

**Why it happens:** LLMs recommend permissive security settings as a troubleshooting shortcut when the root cause is unknown. `disableProtocolSecurity` is designed for non-HTTPS or self-signed certificate scenarios, not as a general callout troubleshooting tool.

**Correct pattern:**

```
disableProtocolSecurity: false for standard HTTPS endpoints (required for production).
disableProtocolSecurity: true ONLY for:
- HTTP (non-HTTPS) endpoints
- Endpoints with self-signed certificates (development/sandbox only)
Never enable for production HTTPS endpoints — this disables TLS validation.

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

**Detection hint:** Any recommendation to create both a Named Credential AND a Remote Site Setting for the same endpoint when Named Credentials are in use.
