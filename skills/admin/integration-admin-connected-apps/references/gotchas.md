# Gotchas — Integration Admin: Connected Apps

## Gotcha 1: Pre-Authorized Mode Blocks All Users Until Profile/Permission Set Assignment Is Made

**What happens:** After setting "Admin approved users are pre-authorized" in OAuth Policies, all OAuth authentication attempts — including the admin's — return a generic OAuth error such as `error=access_denied` or `error=invalid_grant`. No specific message indicates the profile assignment is missing.

**When it occurs:** Immediately after saving the "Admin approved users are pre-authorized" setting when no Profile or Permission Set has been assigned the connected app. Common when admins follow documentation steps in the wrong order (set policy before assignment).

**How to avoid:** Always complete the profile/permission set assignment in the same configuration session as setting pre-authorized mode. After saving the OAuth policy, immediately navigate to the Profile > Connected App Access or Permission Set > Assigned Apps and enable the connected app. Test authentication before considering the configuration complete.

---

## Gotcha 2: Uninstalled Connected Apps Blocked by Default (September 2025)

**What happens:** Integrations that were using a connected app that was subsequently uninstalled continue to fail silently with OAuth errors after September 2025. Previously, uninstalled connected app tokens continued to work. After the September 2025 policy change, Salesforce blocked uninstalled connected apps by default for most user contexts.

**When it occurs:** Any org that has connected apps that were installed from the AppExchange or a managed package and later uninstalled, but whose OAuth tokens are still being used by active integrations (ETL tools, middleware, browser extensions). Common in orgs that have been on Salesforce for several years with multiple integration generations.

**How to avoid:** Audit connected apps in Setup > Apps > Connected Apps > OAuth and Connected App Usage. Review which apps have active OAuth sessions. For any app still in active use that has been uninstalled, re-authorize the app or migrate the integration to a new connected app. Proactively run this audit quarterly to identify orphaned integrations before they fail. Note that the historical override for this — the Use Any API Client permission — no longer works for uninstalled apps in orgs with API Access Control enabled; see Gotcha 4.

---

## Gotcha 3: EventLogFile Requires Event Monitoring Add-On — Not Available in Standard Audit Trail

**What happens:** An admin tries to investigate connected app authentication issues using Setup > Security > Login History. Login History shows the integration user's login events but does not show OAuth token grants, refreshes, revocations, or the specific connected app used for each authentication. The admin cannot determine whether token issues are the cause of integration failures.

**When it occurs:** Any attempt to investigate OAuth token-level events using the standard Setup UI without the Event Monitoring add-on. Admins from orgs without this add-on often spend hours investigating the wrong place.

**How to avoid:** For thorough OAuth investigation, the Event Monitoring add-on is required. If the add-on is not available, partial information is available via: (a) the integration user's Session ID in Login History, (b) manually triggering a test authentication and checking for errors in the API response, and (c) enabling Field Audit Trail on the ConnectedApplication object if available. For production integrations with OAuth-sensitive flows, budget for the Event Monitoring add-on.

---

## Gotcha 4: "Use Any API Client" No Longer Self-Authorizes Uninstalled Apps (Week of December 8, 2025)

**What happens:** A user holds **Use Any API Client** — for years the blanket override for connected-app restrictions — and still cannot complete OAuth authorization for an app that is not installed in the org. Salesforce "is changing the behavior of the 'Use Any API Client' permission so that users with this permission are restricted from self-authorizing uninstalled connected apps," "Starting the week of December 8, 2025." The permission's other capabilities are untouched, so it still looks correct in a permission-set audit.

**When it occurs:** Salesforce publishes the resulting behavior only for orgs that have the API Access Control preference **"For admin-approved users, limit API access to only allowlisted connected apps"** enabled, and says nothing about orgs where that preference is off. Do not read that silence as "nothing to do": uninstalled connected apps are blocked by default for most users under the September 2025 policy (Gotcha 2) independently of this preference, so confirm behavior in a sandbox rather than assuming the old override still works. Published behavior for preference-enabled orgs:

| Use Any API Client | Approve Uninstalled Connected Apps | Self-authorize an uninstalled app |
|---|---|---|
| TRUE | FALSE | Blocked — this is the change |
| TRUE | TRUE | Allowed |
| FALSE | TRUE | Allowed |
| FALSE | FALSE | Blocked |

Only *new* authorization requests are blocked: "The existing active sessions of uninstalled connected apps remain unaffected." The failure therefore surfaces later, when a client re-authorizes, not on the day of the change.

**How to avoid:** Install and allowlist the connected app in the org — that is the remedy Salesforce directs admins to. Reserve **Approve Uninstalled Connected Apps** (introduced September 2025) for the few admins or developers who must test an app before installing it; Salesforce states it "should only be assigned to highly trusted users, such as administrators and those involved in managing or testing connected app integrations." This is a dated security enforcement, not a versioned feature, so it applies regardless of the org's release and will not appear in a seasonal release-notes diff.
