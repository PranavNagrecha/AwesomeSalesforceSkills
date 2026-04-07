# Gotchas — Experience Cloud API Access

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Customer Community Users Cannot Call the REST or SOAP API — This Is a License Limit, Not a Permission Gap

**What happens:** A developer or admin grants "API Enabled" on the Customer Community user profile, creates a Connected App, and configures OAuth. The user still receives `INVALID_SESSION_ID` or `API_DISABLED_FOR_ORG` errors when attempting to call Salesforce REST or SOAP API endpoints. Escalating to Salesforce Support does not resolve it.

**When it occurs:** Any time a Customer Community (not Customer Community Plus) user attempts to call the Salesforce REST API, SOAP API, Bulk API, or Metadata API directly. The license does not include this entitlement and no configuration can add it.

**How to avoid:** Verify the license type before designing the integration. If the use case requires programmatic API access by the portal user's credential, the license must be Customer Community Plus or Partner Community. If a license upgrade is not possible, use a server-side mid-tier integration that calls Salesforce using a dedicated integration user's credential and filters results to the community user's allowed data scope. Document this as a known tradeoff.

---

## Gotcha 2: Guest Profile FLS Cannot Be Managed with Permission Sets

**What happens:** A practitioner adds a permission set to the guest user that grants read access to a set of fields, expecting the Apex class to now be able to query those fields. The Apex class still throws an exception or the fields return null because the guest profile's FLS for those fields is still restricted.

**When it occurs:** Whenever someone tries to grant guest users access to additional fields by assigning a permission set to the guest user record. Permission sets assigned to guest users can grant Apex class access and some object-level permissions in some configurations, but they do not override the field-level security defined directly on the guest user profile.

**How to avoid:** Always configure FLS for guest users directly on the guest user profile. Navigate to Setup > Users, find the guest user for the site (named `[Site Name] Guest User`), open the profile link, and set field permissions explicitly there. Do not rely on permission sets for field-level access for guest users. Use `Schema.sObjectType.Object.fields.FieldName.isAccessible()` in Apex to surface FLS errors early rather than silently returning null values.

---

## Gotcha 3: External OWDs Are Independent of Internal OWDs and Default to More Restrictive Settings

**What happens:** An object has a "Public Read/Write" internal OWD. A practitioner assumes this means external users can also read and write those records. External user API calls or Apex queries return zero records. The Sharing Debugger shows the user has no access.

**When it occurs:** Whenever the internal OWD and external OWD for an object are not explicitly aligned. External OWDs were introduced specifically to let admins keep data accessible internally while restricting it for external users. The platform does not inherit or mirror the internal OWD for the external row. Many objects default to "Private" for external access even when the internal OWD is open.

**How to avoid:** In Setup > Sharing Settings, explicitly review the "External Access" column for every object the integration or API call touches. Set the external OWD to the minimum needed (e.g., "Public Read Only" for catalog data). If record-level access is required (e.g., each user sees their own records), use Sharing Sets (Setup > Digital Experiences > Settings > Sharing Sets) mapped on a relationship like `User.AccountId = Object.AccountId`. Do not assume internal OWDs grant anything to external users.

---

## Gotcha 4: Apex Inheritance Can Silently Break Guest User Sharing Enforcement

**What happens:** A developer correctly declares the top-level Apex class `with sharing`. However, the class calls a helper utility class that is declared `without sharing` (a common pattern for reusable internal utilities). The guest user effectively runs in system context for any query or DML in the utility class, bypassing the guest profile restrictions.

**When it occurs:** When `with sharing` Apex calls `without sharing` Apex, the sharing mode switches to `without sharing` for the called class. This is expected Apex behavior for internal users but creates data exposure for guest-accessible entry points.

**How to avoid:** Audit the entire call chain for any Apex reachable by guest users. Every class in the chain that accesses data should be declared `with sharing`. If a utility class must be shared across internal and external contexts, create a separate `with sharing` version for the external path, or declare the utility `inherited sharing` and ensure the caller is `with sharing`. Test by calling the method as a guest user and verifying that records outside the guest profile's sharing are not returned.

---

## Gotcha 5: "API Enabled" System Permission Is Disabled by Default on All External Profiles

**What happens:** A Customer Community Plus or Partner Community user obtains an OAuth access token successfully (the login flow works) but receives `403 Forbidden` or `REQUEST_RUNNING_TOO_LONG` errors when calling REST API endpoints. The token is valid but API access is blocked.

**When it occurs:** The user's profile does not have the "API Enabled" system permission enabled. When Salesforce creates external profiles (Customer Community Plus User, Partner Community User, and custom clones of these), "API Enabled" is off by default — even though the license includes API entitlement.

**How to avoid:** After creating or cloning an external profile for Customer Community Plus or Partner Community users, explicitly enable "API Enabled" in Setup > Profiles > [Profile] > System Permissions. When using permission sets to manage this, assign a permission set that includes "API Enabled" to the relevant users. Confirm this is in place before beginning any OAuth or REST API integration work for external users.
