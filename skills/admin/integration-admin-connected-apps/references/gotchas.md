# Gotchas — Integration Admin: Connected Apps

## Gotcha 1: Pre-Authorized Mode Blocks All Users Until Profile/Permission Set Assignment Is Made

**What happens:** After setting "Admin approved users are pre-authorized" in OAuth Policies, all OAuth authentication attempts — including the admin's — return a generic OAuth error such as `error=access_denied` or `error=invalid_grant`. No specific message indicates the profile assignment is missing.

**When it occurs:** Immediately after saving the "Admin approved users are pre-authorized" setting when no Profile or Permission Set has been assigned the connected app. Common when admins follow documentation steps in the wrong order (set policy before assignment).

**How to avoid:** Always complete the profile/permission set assignment in the same configuration session as setting pre-authorized mode. After saving the OAuth policy, immediately navigate to the Profile > Connected App Access or Permission Set > Assigned Apps and enable the connected app. Test authentication before considering the configuration complete.

---

## Gotcha 2: Uninstalled Connected Apps Blocked by Default (September 2025)

**What happens:** Integrations that were using a connected app that was subsequently uninstalled continue to fail silently with OAuth errors after September 2025. Previously, uninstalled connected app tokens continued to work. After the September 2025 policy change, Salesforce blocked uninstalled connected apps by default for most user contexts.

**When it occurs:** Any org that has connected apps that were installed from the AppExchange or a managed package and later uninstalled, but whose OAuth tokens are still being used by active integrations (ETL tools, middleware, browser extensions). Common in orgs that have been on Salesforce for several years with multiple integration generations.

**How to avoid:** Audit connected apps in Setup > Apps > Connected Apps > OAuth and Connected App Usage. Review which apps have active OAuth sessions. For any app still in active use that has been uninstalled, re-authorize the app or migrate the integration to a new connected app. Proactively run this audit quarterly to identify orphaned integrations before they fail.

---

## Gotcha 3: EventLogFile Requires Event Monitoring Add-On — Not Available in Standard Audit Trail

**What happens:** An admin tries to investigate connected app authentication issues using Setup > Security > Login History. Login History shows the integration user's login events but does not show OAuth token grants, refreshes, revocations, or the specific connected app used for each authentication. The admin cannot determine whether token issues are the cause of integration failures.

**When it occurs:** Any attempt to investigate OAuth token-level events using the standard Setup UI without the Event Monitoring add-on. Admins from orgs without this add-on often spend hours investigating the wrong place.

**How to avoid:** For thorough OAuth investigation, the Event Monitoring add-on is required. If the add-on is not available, partial information is available via: (a) the integration user's Session ID in Login History, (b) manually triggering a test authentication and checking for errors in the API response, and (c) enabling Field Audit Trail on the ConnectedApplication object if available. For production integrations with OAuth-sensitive flows, budget for the Event Monitoring add-on.
