# Gotchas — Experience Cloud Search Customization

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: LWR Search Component Not Usable in Aura Sites (and Vice Versa)

**What happens:** The LWC-based `Search Bar` and `Search Results` components (designed for LWR sites) are not available in Aura-template sites. The Aura `Search` component is not supported on LWR pages. If the wrong component type is placed, Experience Builder may allow the save, but the component either does not render or renders broken at runtime with no explicit error message surfaced to the site builder.

**When it occurs:** Any time a developer or admin drags a search component onto a page without first confirming the site template type. This happens frequently when a site is migrated from Aura to LWR or when a developer works across multiple sites with different template types.

**How to avoid:** Before placing any search component, confirm the site template type in Experience Builder > Settings > General. For LWR sites: use `Search Bar` (header) + `Search Results` (results page). For Aura sites: use the `Search` component. These are the only supported combinations. Do not attempt to share search component configurations between sites of different template types.

---

## Gotcha 2: Guest Search Limited by Secure Guest User Record Access Regardless of FLS or OWD

**What happens:** When the org-level "Secure Guest User Record Access" setting is enabled (Setup > Sharing Settings), guest users can only see records they explicitly own or that are shared with the Guest User via a sharing rule or sharing set. This overrides the object-level OWD for guest users. An object with OWD set to "Public Read Only" is still inaccessible to guests unless a sharing rule or sharing set explicitly grants access.

**When it occurs:** Any time a practitioner configures guest user search access based on object permissions and OWD settings alone, without accounting for this org-level setting. The setting has been Salesforce's recommended default since Winter '21 and is being enforced in new orgs by default. It silently returns zero search results for affected objects — no error is thrown, and the search response looks identical to "no matching records."

**How to avoid:** Before configuring guest search, check Setup > Sharing Settings > Secure Guest User Record Access. If the setting is enabled, create explicit sharing rules (criteria-based or manual) or a Guest User sharing set for each object that guests should be able to search. Test always as an actual guest (incognito browser) rather than as an admin in Experience Builder preview, which bypasses this setting entirely.

---

## Gotcha 3: Federated Search Requires the External Endpoint to Handle Salesforce's Outbound Callout

**What happens:** Federated search does not use Apex to make the callout to the external endpoint. Salesforce's search infrastructure makes the outbound HTTP POST directly to the registered endpoint URL. This means standard Apex governor limits, Remote Site Settings, and Named Credential configurations in the standard Apex callout path do not apply in the same way. The external endpoint must be reachable from Salesforce's outbound IP ranges, and if the endpoint requires authentication, it must be configured in the federated search source setup, not in an Apex Remote Site entry.

**When it occurs:** When an administrator or developer sets up federated search to a behind-firewall or VPN-protected endpoint and expects standard Remote Site Settings to authorize the connection, or when they expect to be able to use a Named Credential configured for Apex callouts. The federated callout fails silently — external results are simply absent from the result set — and the endpoint never receives the request.

**How to avoid:** Ensure the external endpoint is publicly reachable from Salesforce's known outbound IP ranges (documented in Salesforce Help > Salesforce IP Addresses and Domains to Allow). If the endpoint requires authentication, configure it through the federated search source configuration in Setup (not via a standard Apex Named Credential). Test connectivity independently before enabling the source in Search Manager.

---

## Gotcha 4: Object Missing from Search Manager Returns Zero Results With No Error

**What happens:** If an object is not included in the site's Search Manager scope, search queries against that object return zero results with no error message. The search response is structurally identical to a query that found no matching records, making this indistinguishable from a permissions problem or an actual absence of data.

**When it occurs:** When an admin adds a new object to the org but forgets to add it to the site's Search Manager, or when an object is removed from scope during a configuration cleanup and the removal goes unnoticed. It also occurs when "Allow Search" is not enabled on the object, which prevents it from being available in Search Manager at all.

**How to avoid:** After any Search Manager change, run a test search for a known record of each object type that should be searchable. Verify results appear. If an object does not appear in Search Manager's available list, check Setup > Object Manager > [Object] > Search Layouts to confirm "Allow Search" is enabled and that at least one field is in the search layout.

---

## Gotcha 5: Admin Experience Builder Preview Bypasses Guest Sharing

**What happens:** When a Salesforce admin tests search in Experience Builder's preview mode, the preview runs under the admin's credentials, not the Guest User. All sharing restrictions, OWD values, and the Secure Guest User Record Access setting are bypassed. Articles and records that appear correctly in admin preview can be completely invisible to actual guest users visiting the live site.

**When it occurs:** Any time search is validated only through Experience Builder preview without also testing in an incognito browser session against the actual site URL. This is one of the most common causes of "it works in preview but not on the live site" reports.

**How to avoid:** Always validate guest user search behavior by opening an incognito (private) browser window and navigating to the site's public URL. This forces the session to run as the Guest User and correctly applies all sharing restrictions. Admin preview is useful for layout and component checks; it is not a valid substitute for guest access testing.
