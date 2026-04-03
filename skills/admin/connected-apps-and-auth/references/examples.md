# Examples: Connected Apps and Auth

---

## Example: External System Calling Salesforce

**Scenario:** Middleware needs server-to-server API access to create and update Cases in Salesforce.

**Recommended pattern:**
- Connected App
- Client Credentials or JWT Bearer flow
- dedicated integration user
- minimal permission set for the Case operations required

**Why:** This keeps machine access separate from human credentials and supports controlled token lifecycle.

---

## Example: Salesforce Calling an External API

**Scenario:** A Flow-triggered Apex callout sends invoice data to a billing platform.

**Recommended pattern:**
- Named Credential
- External Credential / OAuth config
- `callout:` endpoint in Apex
- environment-specific credential records

**Why:** Endpoint and auth stay out of code, making promotion and rotation safer.

---

## Example: User-Delegated Third-Party App

**Scenario:** A productivity tool needs a salesperson to connect their own Salesforce account so actions respect that user's access.

**Recommended pattern:** OAuth Authorization Code flow with controlled scopes.

**Why:** User-delegated access is different from machine-to-machine integration and should preserve explicit user consent and user-level permissions.
