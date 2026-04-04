# Gotchas — Network Security and Trusted IPs

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Sandbox IP Ranges Are Not Preserved After a Full Sandbox Refresh

**What happens:** After a full sandbox refresh from production, all Trusted IP Ranges (Setup > Security > Network Access) and all profile-level Login IP Ranges are wiped and replaced with the production org's values at the time of refresh. Any IP ranges added directly to the sandbox after it was originally created are lost.

**When it occurs:** Every time a full sandbox refresh is performed. Partial refreshes follow the same behavior. This catches teams who have spent weeks configuring sandbox-specific IP ranges for their QA network or CI/CD pipeline and assumed those settings would persist.

**How to avoid:** Before triggering a sandbox refresh, export all Trusted IP Ranges and profile Login IP Range settings to a document or configuration template. After the refresh completes, re-enter them. Better: use the work template in this skill's `templates/` directory to maintain a live record of all IP ranges, so re-entry is mechanical. Also note: production IP ranges now appear in the sandbox immediately after refresh — if production ranges are overly broad or lock out sandbox users on different networks, you will need to adjust them in the sandbox immediately post-refresh.

---

## Gotcha 2: CSP Trusted Sites scope includes subpaths but the Origin must match exactly — no path matching

**What happens:** A CSP Trusted Site entry with Site URL `https://cdn.example.com` covers all resources served from that origin (any path under `https://cdn.example.com/...`). However, if a resource is served from a *subdomain* — `https://static.cdn.example.com` — it is treated as a completely different origin and is not covered by the `https://cdn.example.com` entry.

**When it occurs:** When a third-party CDN serves resources from multiple subdomains. For example, a charting library may load its main script from `https://cdn.chartjs.org` but load locale files from `https://cdn2.chartjs.org`. Developers add the first origin and are surprised to see CSP errors for resources from the second origin.

**How to avoid:** Open the browser Developer Tools console while the Lightning component loads. Read all CSP violation messages — each blocked origin will appear as a separate error. Add a separate CSP Trusted Site entry for each distinct origin that appears in violation errors. Do not assume adding a parent domain covers its subdomains — it does not in CSP. Each subdomain is its own origin and requires its own entry.

---

## Gotcha 3: IPv6 Ranges in Trusted IP Ranges Must Use Full Expanded Form — CIDR Notation Is Not Accepted in the UI

**What happens:** When adding an IPv6 trusted IP range through the Setup UI, Salesforce requires a Start IP Address and End IP Address in full expanded IPv6 form (e.g., `2001:0db8:0000:0000:0000:0000:0000:0001`). CIDR notation (e.g., `2001:db8::/32`) is not accepted, and abbreviated IPv6 forms with `::` may be rejected or behave inconsistently depending on the API version used.

**When it occurs:** When an organization has IPv6 egress addresses (common with modern ISPs and cloud providers) and an admin tries to add those ranges using CIDR notation or compressed IPv6 form.

**How to avoid:** Convert IPv6 CIDR ranges to their full start/end IP pair before entering them in the UI. Use a free IPv6 range calculator to determine the first and last address in the block. Enter both in full 8-group colon-separated hex form. If entering ranges via the Metadata API (using the `NetworkAccess` metadata type), test in a sandbox first to confirm the accepted format for your org's API version.

---

## Gotcha 4: Login IP Ranges on a Profile Apply to All Users on That Profile — Including the Admin Configuring Them

**What happens:** If you add a Login IP Range to the System Administrator profile while logged in from an IP outside that range, your current session is not immediately terminated. However, on your next login attempt, you will be locked out. This typically surfaces the next time the admin logs in from a different network (e.g., working from home the next day) and finds their own account blocked.

**When it occurs:** When an admin configures Login IP Ranges without first confirming their own IP is within the range being saved. The Save operation succeeds without warning that the current session's source IP is outside the new range.

**How to avoid:** Before saving any Login IP Range configuration on the System Administrator profile, verify your current IP (check `whatismyip.com`) and confirm it falls within at least one of the ranges you are adding. Keep a browser session open on a separate System Administrator account that is not on the restricted profile (e.g., a break-glass admin account on a separate profile without Login IP Ranges) so you can recover if you lock yourself out.

---

## Gotcha 5: CORS Allowlist Only Applies to Browser-Initiated API Calls — Server-to-Server Calls Are Unaffected

**What happens:** A developer adds a CORS entry for an integration partner's domain expecting it to "allow" that partner to call the Salesforce API. The partner's integration (which runs server-side) continues working regardless of whether the CORS entry exists. Meanwhile, the developer misunderstands CORS as an authentication or authorization control rather than a browser security mechanism.

**When it occurs:** When teams conflate CORS allowlisting with API access control. CORS is enforced by the browser to protect end users — it has no effect on server-to-server HTTP calls made by Node.js, Python, Java, or any non-browser client.

**How to avoid:** Use CORS entries only for browser-based JavaScript applications that call the Salesforce API directly from the end user's browser. For server-to-server integrations, API access is controlled by Connected App OAuth scopes, Named Credentials, and IP filtering in Connected App settings — not CORS. Do not add CORS entries "just in case" for server integrations; it adds noise to the allowlist without providing any security or functionality benefit.

---

## Gotcha 6: CSP Trusted Sites Added for `script-src` Do Not Also Cover `connect-src` — JavaScript fetch() Calls Require a Separate Directive

**What happens:** A developer adds a CSP Trusted Site for an external domain with only the `script-src` directive checked, allowing the script file itself to load. However, if that script makes `fetch()` or `XMLHttpRequest` calls back to the same domain (or another external domain), those calls are blocked by a separate `connect-src` CSP violation.

**When it occurs:** With most modern third-party analytics, chat widgets, and API SDKs — they load a script file (`script-src`) but then also make network calls back to their servers (`connect-src`). Each type of network activity requires its own directive to be permitted.

**How to avoid:** When adding a CSP Trusted Site for a third-party SDK, check both `script-src` (for the script file) and `connect-src` (for API calls the script makes). Review the browser console for additional CSP violations after allowing `script-src` — a second wave of `connect-src` violations will often appear once the script itself loads. Add additional CSP Trusted Site entries for each distinct origin making network calls, with `connect-src` checked.
