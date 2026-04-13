# LLM Anti-Patterns — Integration User Management

Common mistakes AI coding assistants make when generating or advising on Integration User Management.
These patterns help the consuming agent self-check its own output.

### Anti-Pattern 1: Recommending System Administrator Profile for Integration Users

**What LLMs do:** When asked to set up an integration user, LLMs frequently recommend assigning the System Administrator profile or cloning it, citing "simplicity" or "avoiding permission issues." They may frame this as a temporary step that can be tightened later.

**Why:** Training data contains many tutorials and Stack Exchange answers that use admin profiles as a quick fix. LLMs pattern-match to "integration needs to work" and surface the most permissive solution. The long-term security implications are not represented in the training signal.

**Correct approach:**
```
Profile: Minimum Access - API Only Integrations
(paired with Salesforce Integration user license)

Then layer permissions via targeted permission sets:
- Create one permission set per integration boundary
- Assign the Salesforce API Integration PSL to each permission set
- Grant only the object/field/DML permissions the integration requires
```

**Detection:** If the generated setup steps mention "System Administrator profile," "clone the admin profile," or "grant all permissions for now" — flag and reject. Integration users must always use the Minimum Access - API Only Integrations profile.

---

### Anti-Pattern 2: Assuming the MFA Waiver Is Automatic for Integration License Users

**What LLMs do:** LLMs frequently state or imply that the Salesforce Integration user license automatically exempts users from org-wide MFA enforcement. They skip the MFA waiver assignment step entirely, or mention it only as an optional note.

**Why:** The exemption behavior is nuanced — existing integration users before MFA enforcement may retain their access, creating the false impression that no action is needed. LLMs generalize this to all integration users, including new ones.

**Correct approach:**
```
If org-wide MFA is enforced:
1. Create a dedicated permission set: "Integration MFA Waiver"
2. In System Permissions, enable:
   "Multi-Factor Authentication for API Logins" exemption
3. Assign this permission set to every integration user
4. Document: user, date, approver, business justification
5. Verify via Login History after first login
```

**Detection:** If the generated workflow for integration user setup omits any mention of MFA waiver or states the Salesforce Integration license "automatically bypasses MFA" — this is incorrect. Explicitly check that MFA waiver assignment is included as a numbered step.

---

### Anti-Pattern 3: Recommending Username-Password OAuth Flow for Integration Users

**What LLMs do:** LLMs often suggest the OAuth username-password flow as the easiest way to configure API access for integration users. They generate sample code using `grant_type=password` with embedded credentials.

**Why:** Username-password flow requires less configuration than client credentials and is heavily represented in older API tutorials. LLMs trained on this material surface it as the default, despite Salesforce deprecating the flow and recommending against it for server-to-server integrations.

**Correct approach:**
```
Use OAuth 2.0 Client Credentials Flow:
1. Create a Connected App with "Enable Client Credentials Flow" checked
2. Set "Run As" to the dedicated integration user (not an admin)
3. Grant the connected app to the integration user via Connected App Policies
4. Authenticate using:
   POST /services/oauth2/token
   grant_type=client_credentials
   client_id=<consumer key>
   client_secret=<consumer secret>
```

**Detection:** If generated code or steps include `grant_type=password` or transmit a username and password in the token request body — flag and reject. Client credentials flow is the correct pattern for server-to-server integrations.

---

### Anti-Pattern 4: Using a Single Shared Integration User for Multiple Integrations

**What LLMs do:** To simplify setup, LLMs often recommend one integration user with a broad permission set that covers all integrations. They may describe this as "the integration service account" and grant it permissions across multiple objects and domains.

**Why:** LLMs model simplicity as reducing the number of entities. A single user with one permission set appears simpler than multiple users with separate permission sets. The operational and security consequences of consolidation are not reflected in typical training examples.

**Correct approach:**
```
One user per logical integration boundary:
- mulesoft-erp@company.sf.prod  → reads Accounts, writes Order__c
- dataloader-finance@company.sf.prod → reads Opportunity, writes Revenue__c
- external-portal@company.sf.prod → reads/writes Contact, Case

Each user:
- Has its own dedicated permission set
- Can be disabled, rotated, or audited independently
- Has a clean LoginHistory audit trail
```

**Detection:** If the generated setup uses a single username for multiple named integrations, or if a permission set grants CRUD to more than 4-5 unrelated objects — probe whether the design conflates multiple integrations into one identity.

---

### Anti-Pattern 5: Relying Solely on the Login History UI for Audit Coverage

**What LLMs do:** LLMs recommend Setup > Login History as the complete solution for integration user monitoring. They describe it as showing "all login activity" without disclosing the 20,000-record UI cap or the 6-month window limitation.

**Why:** The Login History page is the most discoverable UI surface for login monitoring. LLMs surface it as the canonical answer without representing the platform limits that make it insufficient for high-volume integration monitoring.

**Correct approach:**
```
For durable audit coverage, query LoginHistory via SOQL:

SELECT Id, UserId, LoginTime, Status, LoginType,
       Application, Browser, SourceIp
FROM LoginHistory
WHERE UserId = '<integration_user_id>'
  AND LoginTime >= LAST_N_DAYS:30
ORDER BY LoginTime DESC

Or schedule a weekly Salesforce Report export to an external log store.
For high-volume orgs, evaluate Event Monitoring (if licensed) for
queryable, durable login event history without the 20k-record cap.
```

**Detection:** If the recommended monitoring approach mentions only the Setup > Login History UI and does not reference SOQL queries against LoginHistory, scheduled exports, or Event Monitoring — flag as incomplete. The UI cap must be acknowledged and a durable alternative must be provided.
