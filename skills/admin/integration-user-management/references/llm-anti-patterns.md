# LLM Anti-Patterns — Integration User Management

Common mistakes AI coding assistants make when advising on integration user setup.

## Anti-Pattern 1: Recommending Admin Profile for Integration Users

**What the LLM generates:** "For simplicity, assign the System Administrator profile to your integration user to ensure it has all necessary permissions and avoid permission errors during development."

**Why it happens:** Admin profile is the universal solution to permission problems in Salesforce. LLMs recommend it to avoid the complexity of permission set configuration.

**Correct pattern:**

```
NEVER assign admin profile to integration users.
- Enables interactive UI login (security risk)
- Violates least-privilege (all data accessible)
- Makes audit logs uninterpretable

Correct approach:
1. License: Salesforce Integration
2. Profile: Minimum Access - API Only Integrations (enforces API-only)
3. Permissions: Targeted permission sets for specific objects/fields only
4. When permission errors occur: add to the permission set, never change the profile
```

**Detection hint:** Any recommendation of System Administrator or "cloned admin" profile for an integration user.

---

## Anti-Pattern 2: Omitting MFA Waiver for New Integration Users in MFA-Enforced Orgs

**What the LLM generates:** "Create the integration user with the Salesforce Integration license and Minimum Access - API Only Integrations profile, then test authentication."

**Why it happens:** MFA waiver configuration is a separate, easily overlooked step that is not part of the basic user creation workflow.

**Correct pattern:**

```
In orgs with MFA enforcement enabled, ALSO:

After creating the integration user:
1. Check: Setup > Identity Verification > MFA for API Logins (is it Required?)
2. If required: grant MFA waiver to the integration user

Options:
A) Permission set with "Waive MFA for Exempt Users" permission
B) Use JWT bearer flow (certificate-based, inherently MFA-resistant — preferred)

Without this step in MFA-enforced orgs:
New integration users fail authentication on first attempt.
```

**Detection hint:** Any integration user creation workflow in an MFA-enforced org that does not mention MFA waiver configuration.

---

## Anti-Pattern 3: Using Login History UI for High-Frequency Integration Auditing

**What the LLM generates:** "To monitor your integration user's activity, go to Setup > Users > Login History and filter by the integration user."

**Why it happens:** Login History UI is the most visible audit tool. LLMs recommend it without knowing the 20,000-record display limit.

**Correct pattern:**

```
Setup > Login History UI: Limited to 20,000 most recent records.
High-frequency integrations exhaust this limit in hours/days.

For full audit history, use SOQL:
SELECT UserId, Status, LoginType, SourceIp, LoginTime, Application
FROM LoginHistory
WHERE UserId = '<integration_user_id>'
  AND LoginTime >= LAST_N_DAYS:30
ORDER BY LoginTime DESC

Available: 6 months retention, unlimited records via API
```

**Detection hint:** Any monitoring recommendation that only mentions the Setup UI for high-frequency integration users.

---

## Anti-Pattern 4: Sharing One Integration User Across Multiple Systems

**What the LLM generates:** "Create one integration user for all your Salesforce integrations. This simplifies user management and reduces license consumption."

**Why it happens:** Single user = simpler management appears to be an efficiency. LLMs may not recognize the operational and security problems this creates.

**Correct pattern:**

```
One integration user PER integration system (at minimum).
Reasons:
- Disabling one system's user doesn't break other integrations
- Audit logs are interpretable (which system made which call)
- Least-privilege is achievable (each user only has its system's permissions)
- Compromised credentials affect only one integration

Example naming: mulesoft_integration@company.com, informatica_etl@company.com
```

**Detection hint:** Any recommendation for a shared integration user across multiple systems.

---

## Anti-Pattern 5: Claiming Username-Password OAuth Is Sufficient for Production Integrations

**What the LLM generates:** "Use username-password OAuth flow for your integration — it's the simplest way to authenticate a server-to-server integration."

**Why it happens:** Username-password OAuth flow is the easiest to implement and the most common in beginner tutorials. LLMs may recommend it without flagging the security limitations.

**Correct pattern:**

```
Username-password OAuth flow limitations:
- Sends credentials over the network (risk if TLS is misconfigured)
- Requires MFA waiver in MFA-enforced orgs
- Salesforce plans to restrict this flow further in future releases

Preferred: OAuth JWT Bearer Flow
- Uses certificate pair (no credentials transmitted)
- Inherently MFA-resistant
- Works in all MFA enforcement configurations
- Required for some Salesforce-to-Salesforce integrations

Setup: Connected app > Use digital signatures > Upload public certificate
Integration side: Generate signed JWT with private key, exchange for access token
```

**Detection hint:** Any recommendation of username-password OAuth for a production integration without mentioning JWT bearer flow as the preferred alternative.
