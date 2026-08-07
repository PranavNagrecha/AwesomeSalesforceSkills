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
1. Clock drift on the signing server (NTP sync). The documented tolerance is a
   3-minute buffer applied to `exp` — NOT a 60-second window on `iat`.
2. `exp` already in the past, or so far in the past that the 3-minute buffer
   cannot cover it. (`iat` is not a required claim for this flow: the required
   set is iss, sub, aud, exp.)
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

---

## Anti-Pattern: Inventing a 60-Second `iat` Window for the JWT Bearer Flow

**What the LLM generates:** "The assertion's `iat` and `exp` claims must satisfy `exp - iat <= 3 minutes`, and the JWT must reach Salesforce within 60 seconds of `iat`. Any clock skew beyond 60 seconds produces `invalid_grant`."

**Why it happens:** `iat` *is* a standard RFC 7519 claim and many JWT-issuing systems do enforce a freshness window on it, so the model transfers the general JWT idiom onto Salesforce's specific flow. The real "3 minutes" from the documentation is present in the answer — attached to the wrong pair of claims — which is what makes the whole sentence read as researched. The invented "60 seconds" is then stated with false precision, and precision is exactly what an engineer trusts when debugging.

**Why it costs time at the worst moment:** `invalid_grant` is Salesforce's catch-all JWT failure. An engineer told the threshold is 60 seconds will chase sub-minute NTP drift, conclude the clocks are fine because they are within 60 seconds, and never check the condition that actually failed — an `exp` outside the real 3-minute buffer, or a wrong `aud`, or a certificate mismatch.

**Correct pattern:**
```
Required claims for the Salesforce OAuth 2.0 JWT bearer flow:
    iss   the connected app's OAuth client_id
    sub   the username to authenticate as
    aud   the authorization server URL (https://login.salesforce.com, or
          https://test.salesforce.com for a sandbox)
    exp   expiry, seconds since 1970-01-01T00:00:00Z UTC

`iat` is NOT required and carries no documented freshness window.

Clock skew: "Salesforce allows a 3-minute buffer for clock skew." The buffer
applies to `exp`. Set exp a few minutes out, keep the signing host on NTP,
and log the exp you signed so drift is diagnosable.
```

**Detection hint:** any numeric constraint on `iat` in a Salesforce JWT context, and specifically the pairing of `60 seconds` with `iat`. Also flag `exp - iat <= 3 minutes` as an expression — the documented 3 minutes is a *tolerance applied to `exp`*, not a constraint on the interval between the two claims. Mechanically: a JWT signer whose only skew instrumentation logs `iat` is instrumenting the claim Salesforce does not check.
