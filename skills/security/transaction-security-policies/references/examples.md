# Examples — Transaction Security Policies

## Example 1: Block All Logins from Outside the United States

**Context:** A financial services org stores sensitive customer data and is required by internal compliance policy to restrict Salesforce access to logins originating within the United States. Existing IP whitelisting in profile-level Login IP Ranges is impractical because remote users legitimately travel and connect from different IPs. Geography-based blocking is more appropriate than IP-based blocking.

**Problem:** Without a Transaction Security Policy, Salesforce imposes no geography-based login restriction. A user who authenticates successfully from a foreign IP — whether compromised or traveling — gets full access. The security team only discovers the anomaly the next day via EventLogFile, after the fact.

**Solution:**

Configure a Transaction Security Policy on `LoginEvent` with a Country condition and a Block enforcement action.

Setup UI steps:
1. Setup > Security > Transaction Security Policies > New
2. Event Type: `Login`
3. Condition (Enhanced Condition Builder):
   - Field: `Country` | Operator: `Not Equal To` | Value: `US`
4. Action: Block
5. Block Message: "Access from outside the United States is restricted by your organization's security policy. Contact your administrator if you believe this is an error."
6. Add a secondary Notification action directed to the security admin user.
7. Set to Monitor mode. Validate match log for 5 business days.
8. Switch to Active.

Metadata API equivalent (after building in UI and retrieving):
```xml
<?xml version="1.0" encoding="UTF-8"?>
<TransactionSecurityPolicy xmlns="http://soap.sforce.com/2006/04/metadata">
    <action>
        <blockMessage>Access from outside the United States is restricted by your organization's security policy. Contact your administrator if you believe this is an error.</blockMessage>
        <type>Block</type>
    </action>
    <active>true</active>
    <apexPolicy>false</apexPolicy>
    <description>Block all logins from non-US countries</description>
    <developerName>Block_Non_US_Logins</developerName>
    <eventName>LoginEvent</eventName>
    <eventType>Login</eventType>
    <masterLabel>Block Non-US Logins</masterLabel>
</TransactionSecurityPolicy>
```

**Why it works:** `LoginEvent` is a policy-supported RTEM event type. The `Country` field is populated from geo-IP resolution at login time. The `Not Equal To` condition matches any country other than the US, triggering the block before the session is fully established. The Monitor period confirms no edge-case legitimate logins (e.g., a US-based user connecting through an overseas VPN exit node) are caught before enforcement goes live.

---

## Example 2: MFA Step-Up Challenge When Exporting a Sensitive Report

**Context:** An HR org has a report named "Active Employee Compensation" that is accessible to HR managers. The report contains salary and bonus information. The security team does not want to revoke access, but does want to ensure any export of this specific report triggers an identity re-verification step.

**Problem:** Without enforcement, an HR manager whose session is hijacked or whose credentials are stolen can silently export compensation data. Org-wide MFA on login does not help if the session is already established. A profile-level restriction would prevent all access, blocking legitimate use.

**Solution:**

Configure a Transaction Security Policy on `ReportEvent` with an MFA enforcement action.

Setup UI steps:
1. Setup > Security > Transaction Security Policies > New
2. Event Type: `Report`
3. Conditions (Enhanced Condition Builder):
   - Field: `Name` | Operator: `Contains` | Value: `Active Employee Compensation`
   - AND Field: `Operation` | Operator: `Equals` | Value: `Export`
4. Action: Multi-Factor Authentication
5. Add a Notification action to the HR data owner user.
6. Set to Monitor mode. Run a test export of the target report; verify the policy match appears in the log.
7. Switch to Active.

**Why it works:** `ReportEvent` supports Transaction Security Policy enforcement. The dual-condition (report name AND operation = Export) ensures the MFA challenge fires only on export attempts of the specific report — not on every time the report is simply viewed. Users who pass MFA proceed with the export; those who cannot complete MFA are blocked from downloading the data. This mirrors the Salesforce-recommended pattern for protecting sensitive data exports without revoking legitimate access.

---

## Example 3: Notify Admin When a Connected App Makes Excessive API Calls

**Context:** A third-party data integration connected app has been granted full API access. The org has seen occasional spikes in API consumption that push the daily limit. The admin wants to be alerted when this connected app's API calls exceed a threshold, without blocking the integration.

**Problem:** There is no native API usage alerting per connected app. API limit warnings appear in Setup, but only at the org level and only reactively after limits are nearly exhausted.

**Solution:**

Configure a Transaction Security Policy on `ApiEvent` with a Notification-only action.

Setup UI steps:
1. Setup > Security > Transaction Security Policies > New
2. Event Type: `ApiEvent`
3. Condition (Enhanced Condition Builder):
   - Field: `UserId` | Operator: `Equals` | Value: `[integration user Id]`
4. Action: Notification (no Block)
5. Recipients: integration admin user
6. Set to Monitor mode initially to calibrate how often the condition fires.
7. Add a `QueryRunTime` Greater Than threshold if further filtering is needed to target slow or bulk operations specifically.

**Why it works:** The Notification action does not block the integration, preserving business continuity. The condition targets the specific integration user rather than all API traffic, preventing alert fatigue. The policy owner receives near-real-time visibility into integration API behavior without needing a separate monitoring tool or external log aggregator.

---

## Anti-Pattern: Creating an Active Policy Without Monitor Mode Validation

**What practitioners do:** A practitioner creates a new Transaction Security Policy on `LoginEvent` to block logins from a foreign country. They set it directly to Active without testing. The policy goes live immediately.

**What goes wrong:** The `Country` field condition uses the full country name (`United States`) instead of the ISO code (`US`). The condition never matches because the field stores only ISO codes. The policy is silently ineffective — no logins are blocked, no error is shown. Alternatively, if the condition accidentally targets a broader set than intended (e.g., a report name substring that matches multiple reports), legitimate users are blocked at login.

**Correct approach:** Always create new policies in Monitor mode. Review the match log for at least one business cycle (3–5 days for login policies; 1–2 export cycles for report policies) before switching to Active enforcement. Confirm field value formats using the Salesforce Object Reference for the specific event type's field documentation.
