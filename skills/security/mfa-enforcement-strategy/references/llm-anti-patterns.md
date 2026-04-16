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
SSO with MFA at the IdP can satisfy Salesforce MFA expectations for users who authenticate through that SSO path, when direct Salesforce login is not a realistic bypass. Validate both IdP authentication strength and remaining Salesforce login channels against official Salesforce MFA and SSO documentation.
```

**Detection hint:** Absolute words (“always,” “automatically”) paired with “SSO” and “MFA” with no mention of direct login or user population scope.

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
