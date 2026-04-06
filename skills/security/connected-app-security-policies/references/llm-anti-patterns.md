# LLM Anti-Patterns — Connected App Security Policies

Common mistakes AI coding assistants make when generating or advising on Connected App Security Policies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending PKCE While Leaving "Require Secret" Enabled

**What the LLM generates:** Advice to enable PKCE on a Connected App for a public client, with no mention that "Require Secret for Web Server Flow" must be disabled simultaneously.

**Why it happens:** Training data contains many OAuth guides that treat PKCE and client secrets as independent options. The Salesforce-specific constraint that they are mutually exclusive is a platform nuance not present in generic OAuth documentation.

**Correct pattern:**

```
To enable PKCE on a Salesforce Connected App:
1. Check "Require Proof Key for Code Exchange (PKCE)..."
2. UNCHECK "Require Secret for Web Server Flow"
Both checkboxes must never be enabled simultaneously.
```

**Detection hint:** Look for any response that says "enable PKCE" without also saying "disable Require Secret" or "uncheck Require Secret."

---

## Anti-Pattern 2: Claiming Client Secret Rotation Has a Grace Period

**What the LLM generates:** Guidance that advises rotating the consumer secret and then updating consumers "within a few minutes" or states that both old and new secrets work during a transition window.

**Why it happens:** Some identity platforms (Auth0, Azure AD) do support dual-secret grace periods during rotation. LLMs trained on mixed identity platform documentation apply this behavior incorrectly to Salesforce ECA (API v65+).

**Correct pattern:**

```
In the ECA model (default from API v65 / Spring '25):
- Secret rotation is instant and permanent.
- The old secret is invalid the moment rotation completes.
- Update all consumers BEFORE or SIMULTANEOUSLY with rotation.
- There is no grace period or overlap window.
```

**Detection hint:** Any mention of "grace period," "transition window," "both secrets valid," or "update consumers within X minutes of rotation."

---

## Anti-Pattern 3: Treating "Switch to High Assurance" as MFA Enforcement

**What the LLM generates:** Advice to set High Assurance policy to "Switch to High Assurance" as a way to enforce MFA for Connected App access.

**Why it happens:** The label sounds like an enforcement action. LLMs interpret "Switch to High Assurance" as "force users to switch to high assurance," inferring a blocking behavior that does not exist.

**Correct pattern:**

```
"Switch to High Assurance" prompts but does not block.
To enforce MFA and deny low-assurance access, set policy to "Blocked."
"Switch to High Assurance" is only appropriate during a time-bounded migration.
```

**Detection hint:** Any response recommending "Switch to High Assurance" as a security hardening measure without noting it is non-blocking.

---

## Anti-Pattern 4: Attributing invalid_grant in JWT Bearer to Wrong Causes First

**What the LLM generates:** Troubleshooting guidance for `invalid_grant` in JWT Bearer that focuses first on certificate thumbprint mismatches, scope errors, or missing permissions — without considering clock drift.

**Why it happens:** `invalid_grant` is a generic OAuth error shared by many failure modes. LLMs tend to surface the most commonly documented causes first, which are credential-related rather than timing-related. Clock drift is less commonly documented in OAuth troubleshooting guides.

**Correct pattern:**

```
When JWT Bearer returns invalid_grant, check in this order:
1. Clock drift on the signing server (NTP sync; 60-second window)
2. JWT TTL > 3 minutes (exp - iat must be ≤ 3 minutes)
3. Wrong audience (aud must be the Salesforce login URL)
4. Certificate thumbprint or key mismatch
5. Permission set / profile API access
```

**Detection hint:** Any `invalid_grant` troubleshooting response that does not mention clock drift or NTP in the first two steps.

---

## Anti-Pattern 5: Assuming IP Relaxation on Connected App Does Not Override Profile Ranges

**What the LLM generates:** Advice that says "profile IP ranges always apply regardless of Connected App settings" or that IP relaxation on the Connected App is only additive to profile-level restrictions.

**Why it happens:** Profile IP ranges are the more frequently discussed and more visible IP control in Salesforce. LLMs learn from documentation that emphasizes profile-level controls and do not clearly state that Connected App IP relaxation can override them for OAuth flows.

**Correct pattern:**

```
Connected App IP Relaxation overrides profile Login IP Ranges for OAuth token grants.
Setting ipRelaxation=relaxIpRanges on a Connected App bypasses the authenticating
user's profile IP range restrictions for requests through that app.
Audit Connected App IP relaxation separately from profile IP range audits.
```

**Detection hint:** Any response claiming profile IP ranges are "always enforced" or that Connected App IP relaxation is subordinate to profile restrictions.

---

## Anti-Pattern 6: Generating Metadata With Deprecated oauthPolicy Fields

**What the LLM generates:** ConnectedApp metadata XML that uses legacy field names or omits the `oauthPolicy` block entirely, relying on UI-only defaults.

**Why it happens:** Earlier Salesforce API versions had different field names or did not expose all policy fields in metadata. LLMs trained on older documentation reproduce stale field names.

**Correct pattern:**

```xml
<oauthPolicy>
    <ipRelaxation>enforceIpRanges</ipRelaxation>
    <refreshTokenPolicy>zero</refreshTokenPolicy>
</oauthPolicy>
```

Use the current Metadata API ConnectedApp reference (v63+) to confirm field names. Always retrieve the ConnectedApp metadata from the target org after deployment and verify policy fields are present and correct.

**Detection hint:** ConnectedApp metadata XML that does not include an `<oauthPolicy>` block when IP or session policies are being configured.
