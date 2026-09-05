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

## Anti-Pattern 2: Blaming Org-Wide MFA for a Blocked Integration User and Reaching for the Waiver First

**What the LLM generates:** "Your integration user is failing because the org enforces MFA and server-to-server flows can't complete an MFA challenge. Create a permission set with 'Waive Multi-Factor Authentication for Exempt Users' and assign it to the integration user."

**Why it happens:** MFA enforcement is the change the user just described, so it is the most available explanation, and "grant the waiver" is a satisfying one-step fix. The model never checks whether the setting is even in the code path for an API login.

**Correct pattern:**

```
Org-wide MFA enforcement is scoped to DIRECT UI LOGINS.
  SecuritySettings.enableMFADirectUILoginOptIn — "when logging in directly to
  the UI with their username and password"          (api_meta.txt L126248-126252)
An API Only User "can access Salesforce only via APIs, regardless of their
other permissions"                                  (api_meta.txt L121360-121363)
=> There is no UI login for the org MFA setting to challenge.
=> The waiver is NOT a prerequisite for a working integration user.

Diagnose in this order instead. Read LoginHistory.Status on the failing row,
filtering only on UserId and LoginTime (Status is not filterable), then match:

  restricted / untrusted IP   -> Profile.loginIpRanges, plus the connected app's
                                 ipRelaxation (ENFORCE is what makes it apply)
  outside permitted hours     -> Profile.loginHours for that weekday
  session-level requirement   -> ProfileSessionSetting.requiredSessionLevel
                                 = HIGH_ASSURANCE, or a connected-app
                                 RaiseSessionLevel policy. "For flows without a
                                 user approval step, API logins with the High
                                 Assurance session security level are blocked."
                                                    (api_meta.txt L35826-35836)

Grant the waiver only for an account genuinely exempt from the org's MFA
policy — i.e. one that really does log in through the UI.
```

**Detection hint:** Any answer that proposes an MFA waiver for an API-only user without first asking what `LoginHistory.Status` says, or that describes JWT bearer flow as valuable because it "avoids MFA" rather than because it transmits no password.

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
- Subject to the profile's password policy, so an expiry setting can lock the
  integration out on a schedule nobody is watching
- Salesforce plans to restrict this flow further in future releases

Preferred: OAuth JWT Bearer Flow
- Uses certificate pair (no credentials transmitted, nothing to rotate or leak)
- No password policy can expire it
- Caveat: it has no user approval step, so a HIGH_ASSURANCE session level on the
  profile or a RaiseSessionLevel connected-app policy blocks it outright
  (api_meta.txt L35826-35836)

Setup: Connected app > Use digital signatures > Upload public certificate
Integration side: Generate signed JWT with private key, exchange for access token
```

**Detection hint:** Any recommendation of username-password OAuth for a production integration without mentioning JWT bearer flow as the preferred alternative.
