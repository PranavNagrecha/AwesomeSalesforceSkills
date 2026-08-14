# LLM Anti-Patterns — MFA Enforcement Strategy

Common mistakes AI coding assistants make when generating or advising on MFA enforcement strategy for Salesforce.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: “Trusted IPs Mean Users Skip MFA”

**What the LLM generates:** “If users are on the corporate VPN or Trusted IP Ranges, Salesforce will not require MFA.”

**Why it happens:** Older forum posts conflated network location with second-factor requirements; models overfit to “IP trust equals auth strength.”

**Correct pattern:**

```
Trusted IP and network features address session or network policy; they are not a substitute for multi-factor authentication where Salesforce requires MFA for the relevant login path. Always verify current official Salesforce MFA and Session Security documentation for the edition in scope.
```

**Detection hint:** Phrases like “trusted IP bypasses MFA” or “office IP exempts MFA” in the answer.

---

## Anti-Pattern 2: “SSO Always Satisfies Salesforce MFA”

**What the LLM generates:** “You use Okta/Azure AD with MFA, so Salesforce MFA is automatically satisfied for every user.”

**Why it happens:** Models collapse “MFA somewhere” into “MFA everywhere” without modeling parallel Salesforce password login or API session paths.

**Correct pattern:**

```
SSO with MFA at the IdP can satisfy Salesforce MFA expectations for users who authenticate through that SSO path, when direct Salesforce login is not a realistic bypass. Under 2026 enforcement, the SSO path counts only when the IdP passes a standard-MFA or phishing-resistant-MFA signal to Salesforce via ACR or AMR (RFC 8176); an IdP that enforces MFA but sends no such claim still causes Salesforce to prompt users to register a verification method. Validate both IdP authentication strength and remaining Salesforce login channels against official Salesforce MFA and SSO documentation.
```

**Detection hint:** Absolute words (“always,” “automatically”) paired with “SSO” and “MFA” with no mention of direct login, the ACR/AMR claim, or user population scope.

---

## Anti-Pattern 3: Inventing Metadata Field Names for Org-Wide MFA

**What the LLM generates:** A fabricated `Security.settings-meta.xml` snippet with invented element names and boolean semantics not present in the Metadata API.

**Why it happens:** Assistants pattern-match on other settings files and hallucinate plausible camelCase tags.

**Correct pattern:**

```
Retrieve SecuritySettings via Metadata API and compare against the official SecuritySettings type reference. Describe settings at the level you have verified from retrieved metadata or Setup screenshots; flag uncertainty instead of fabricating XML.
```

**Detection hint:** Unusual element names with no Salesforce doc citation, or XML that mixes Profile and Settings types inconsistently.

---

## Anti-Pattern 4: Treating Every Integration User Like an Interactive Employee

**What the LLM generates:** “Assign the same MFA enforcement permission set to all integration users; they can approve push notifications in a shared mailbox.”

**Why it happens:** Over-generalization from human MFA rollout templates without modeling unattended automation.

**Correct pattern:**

```
Separate human MFA rollout from integration authentication modernization. Prefer OAuth flows and integration-user patterns documented for Salesforce APIs; document narrow exemptions only with owners, expiry, and compensating controls per official guidance.
```

**Detection hint:** Recommending Authenticator or SMS for “service account” or “batch user” without discussing OAuth/JWT or headless constraints.

---

## Anti-Pattern 5: Conflating Transaction Security “MFA” Actions with Org-Wide MFA

**What the LLM generates:** “Enable org-wide MFA by creating a Transaction Security Policy with type MultiFactorAuthentication.”

**Why it happens:** Both topics appear in security search results; the model merges policy-based step-up with org baseline MFA enforcement.

**Correct pattern:**

```
Org-wide MFA enforcement and per-event step-up (Transaction Security Policies) solve different problems. Use this skill for baseline MFA posture and SSO alignment; use transaction-security-policies for targeted enforcement on specific events or data access patterns.
```

**Detection hint:** Single solution referencing only `TransactionSecurityPolicy` XML when the user asked about org-wide MFA for all UI logins.

---

## Anti-Pattern 6: Recommending Salesforce Authenticator to Admins and Calling the Org Compliant

**What the LLM generates:** “Have your admins register Salesforce Authenticator (or Google/Microsoft Authenticator) and your org meets the MFA requirement.”

**Why it happens:** A decade of Salesforce guidance made Salesforce Authenticator *the* recommended verifier, so it dominates the training data. The 2026 phishing-resistant requirement for privileged users inverts that advice, and the model has no signal that the recommendation now fails for the population most likely to be asking.

**Correct pattern:**

```
Salesforce Authenticator and TOTP apps remain valid standard MFA, but they do not satisfy the phishing-resistant MFA requirement that applies to users with the System Administrator profile or the Modify All Data, View All Data, Customize Application, or Author Apex permission. That population needs a security key, a built-in authenticator (Touch ID, Windows Hello), a passkey, or certificate-based authentication. Enumerate it from effective permission assignments, not from the profile name.
```

**Detection hint:** Any answer that names Salesforce Authenticator or a TOTP app as sufficient for admins, or that scopes the privileged population by profile alone and never mentions the four permissions travelling on permission sets.

---

## Anti-Pattern 7: Stating a Specific 2026 MFA Enforcement Date as Settled Fact

**What the LLM generates:** A confident single date — “MFA is enforced in sandboxes on June 22, 2026” — often with a fabricated verbatim quotation attributed to a `help.salesforce.com` article.

**Why it happens:** `help.salesforce.com/s/articleView` serves a JavaScript shell with no article text, and returns the same contentless page for every article ID including invented ones. A fetching tool that cannot hold a session gets nothing back and reconstructs plausible dates instead of reporting the failure — which is why repeated passes over the same URL have produced mutually incompatible dates.

**Correct pattern:**

```
Two date sets have been published for the 2026 MFA and PRMFA waves and the schedule was revised at least once, so no specific date should be asserted from an unauthenticated source. Production enforcement is staggered by Release Group, so the announced start is not the org's date in any case. Direct the user to open the Salesforce Help articles signed in and read the schedule for their own Release Group.
```

**Detection hint:** A precise enforcement date paired with a quoted sentence attributed to a `help.salesforce.com` article ID, with no acknowledgement of the Release Group stagger or of the revised schedule.
