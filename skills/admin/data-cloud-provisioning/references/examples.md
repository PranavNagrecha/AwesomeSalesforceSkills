# Examples — Data Cloud Provisioning

## Example 1: Net-New Data Cloud Tenant with Ingestion API Source

**Context:** A retailer has purchased Data Cloud and wants to stream clickstream data from their e-commerce platform into Data Cloud using the Ingestion API. Their Data Cloud tenant is being provisioned for the first time in a Dedicated Home Org.

**Problem:** The Salesforce admin attempts to register the Ingestion API source in Data Cloud Setup immediately after enabling Data 360. The "Authenticate" step in the source registration wizard fails with a generic "connection failed" error, and the admin cannot identify why.

**Solution:**

The admin must create a Connected App with the `cdp_ingest_api` OAuth scope **before** attempting source registration. The Connected App does not need to be used directly by the admin — it authorizes the external e-commerce platform to push data.

Steps:
1. Go to Setup > App Manager > New Connected App.
2. Enable OAuth Settings. Add callback URL (can be `https://login.salesforce.com/services/oauth2/callback` for initial setup).
3. Add OAuth scopes: `Manage user data via APIs (api)` and `Access and manage your data cloud ingestion API data (cdp_ingest_api)`.
4. Save and note the Consumer Key and Consumer Secret.
5. Return to Data Cloud > Data Streams > New > Ingestion API and complete source registration — authentication now succeeds.

```
Connected App OAuth Scopes (minimum required):
  - api
  - cdp_ingest_api

Scope label in UI: "Access and manage your data cloud ingestion API data"
```

**Why it works:** The `cdp_ingest_api` scope is a Data Cloud-specific OAuth scope that authorizes a calling application to write to the Ingestion API endpoint. Without it, the OAuth handshake during source registration cannot obtain the correct access token, causing the connection test to fail regardless of network or IP configuration.

---

## Example 2: Marketing Team Blocked from Creating Activation Targets

**Context:** A financial services firm is provisioning Data Cloud to power personalized email campaigns through Marketing Cloud. The marketing operations lead has been given the "Data Cloud Admin" permission set because the IT team assumed it was the highest level of access.

**Problem:** The marketing operations lead navigates to Data Cloud > Activation Targets > New but the "New" button is greyed out and the screen shows no option to create a target. The user has Data Cloud Admin — a name that implies full access — but cannot create Activation Targets.

**Solution:**

Remove the Data Cloud Admin permission set and replace it with Data Cloud Marketing Admin (or add Data Cloud Marketing Manager if the user does not need full admin access).

```
Incorrect assignment:
  User: Marketing Ops Lead
  Permission Set: Data Cloud Admin  ← does NOT include Activation Target creation

Correct assignment:
  User: Marketing Ops Lead
  Permission Set: Data Cloud Marketing Admin  ← includes Activation Target creation
  OR
  Permission Set: Data Cloud Marketing Manager  ← includes Activation Target creation
```

Steps:
1. Go to Setup > Users > find the user.
2. Click "Permission Set Assignments."
3. Remove "Data Cloud Admin."
4. Add "Data Cloud Marketing Admin" (or "Data Cloud Marketing Manager" if full admin access is not needed).
5. User navigates back to Activation Targets — "New" button is now active.

**Why it works:** Salesforce designed the Data Cloud permission set model to separate platform administration from marketing operations. Activation Target creation is considered a marketing operations capability, not a platform admin capability. The naming is counterintuitive, but the capability split is documented in the Assign a Data Space Permission Set help article.

---

## Anti-Pattern: Choosing Existing Org Without Documenting the Tradeoff

**What practitioners do:** Under time pressure, the team enables Data Cloud in an existing Sales Cloud org to avoid provisioning a new org. No documentation is created about the org model choice.

**What goes wrong:** Months later, the business wants real-time segment refresh driven by live CRM opportunity data — a feature only available in the Dedicated Home Org model. The technical team discovers there is no migration path; moving to Dedicated Home Org requires provisioning a new tenant, rebuilding all data streams, and re-establishing all data connections from scratch. This is treated as an unplanned project.

**Correct approach:** Before provisioning, present the org model decision as an architectural milestone. Document in the project record that the existing-org model was chosen and that Dedicated Home Org-only features (real-time CRM streams, full Salesforce-native activation) will not be available. Get explicit sign-off from a stakeholder who understands the permanent nature of the choice. If the business requirements are unclear, defer enablement until they are confirmed rather than defaulting to the simpler option.
