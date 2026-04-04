# Examples — Network Security and Trusted IPs

## Example 1: Locking Down the System Administrator Profile to Office IPs and VPN

**Context:** A financial services company is preparing for a SOC 2 audit. The auditor requires that all System Administrator logins originate from known corporate IP addresses — either the headquarters office NAT IP or the corporate VPN exit node. Currently, no Login IP Ranges are configured on the System Administrator profile, allowing admins to log in from any network.

**Problem:** Without Login IP Ranges on the System Administrator profile, an attacker who obtains admin credentials can log in from any IP in the world. The email verification challenge (bypassed by Trusted IP Ranges) is the only friction, but does not constitute a hard access control.

**Solution:**

Step 1 — Identify the IPs to allow. Collect the office egress IP and VPN exit IP from the network team:
- Office egress: `203.0.113.50` (single IP for this example)
- VPN exit: `198.51.100.0` to `198.51.100.255` (a /24 block)

Step 2 — Navigate to Setup > Profiles > System Administrator > Login IP Ranges > New.

Add entry 1 (office):
```
Start IP Address: 203.0.113.50
End IP Address:   203.0.113.50
Description:      HQ office egress — added 2026-04-04
```

Add entry 2 (VPN):
```
Start IP Address: 198.51.100.0
End IP Address:   198.51.100.255
Description:      Corporate VPN exit block — added 2026-04-04
```

Step 3 — Before saving, confirm your current IP is within one of these ranges. Open `whatismyip.com` in a separate tab. If your IP is not in range, establish VPN first, then save.

Step 4 — Test by attempting a login from a mobile hotspot (out-of-range IP) with a sandbox System Administrator user. The login should fail with:
> "You are not authorized to login from this IP address."

Step 5 — Verify the denial in LoginHistory:
```soql
SELECT UserId, LoginTime, SourceIp, Status
FROM LoginHistory
WHERE Status = 'No Salesforce.com Access'
  AND LoginTime >= LAST_N_DAYS:1
ORDER BY LoginTime DESC
```

**Why it works:** Login IP Ranges on a profile enforce a hard deny at authentication time. Any login attempt from outside the configured ranges is rejected before a session is created, regardless of whether the credentials are valid. This satisfies the SOC 2 requirement for IP-restricted privileged access.

---

## Example 2: Fixing a CSP Violation Breaking an LWC That Loads a Google Font

**Context:** A developer has built a Lightning web component that applies a custom brand font by loading it from Google Fonts (`https://fonts.googleapis.com`). The component works correctly in the developer sandbox but renders with the default Salesforce font in production, with a console error.

**Problem:** The browser Developer Tools console shows:
```
Content Security Policy: The page's settings blocked the loading of a resource at
https://fonts.googleapis.com/css2?family=Inter:wght@400;600 ("font-src").
```

Salesforce's default Lightning CSP does not include `fonts.googleapis.com` in the `font-src` or `style-src` directives. The resource is being silently blocked.

**Solution:**

Step 1 — Open Setup > CSP Trusted Sites > New.

Fill in:
```
Site Name:   GoogleFontsCSS
Site URL:    https://fonts.googleapis.com
Directives:  style-src  (checked)
             font-src   (checked)
```

Step 2 — Google Fonts also loads the actual font files from a separate origin (`fonts.gstatic.com`). Add a second entry:

```
Site Name:   GoogleFontsStatic
Site URL:    https://fonts.gstatic.com
Directives:  font-src   (checked)
```

Step 3 — Save both entries. Clear the browser cache (Ctrl+Shift+R or Cmd+Shift+R) and reload the Lightning page.

Step 4 — Verify the font loads correctly and the console shows no more CSP errors.

**Why it works:** Google Fonts serves CSS from `fonts.googleapis.com` and the binary font files from `fonts.gstatic.com`. Both origins must be in the CSP Trusted Sites list with the correct directives (`style-src` for the CSS stylesheet, `font-src` for the actual `.woff2` files). Missing either entry leaves one part of the chain blocked.

---

## Example 3: Adding a CORS Entry for an External React Portal Calling the Salesforce REST API

**Context:** An internal developer portal built in React is hosted at `https://portal.company.com`. It uses the Salesforce REST API with an OAuth 2.0 JWT flow to read case data directly from the browser. The portal works from Postman (server-to-server) but fails in the browser with:
```
Access to XMLHttpRequest at 'https://mycompany.my.salesforce.com/services/data/v62.0/sobjects/Case'
from origin 'https://portal.company.com' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**Problem:** The browser sends an `OPTIONS` preflight request before the actual API call. Salesforce rejects it because `https://portal.company.com` is not in the CORS allowlist, so no `Access-Control-Allow-Origin` header is returned.

**Solution:**

Step 1 — Navigate to Setup > CORS > New.

```
Origin URL Pattern: https://portal.company.com
```

Step 2 — Save. No Lightning page reload is needed — CORS changes take effect for new requests immediately.

Step 3 — Test by triggering the API call from the portal browser. The preflight `OPTIONS` request should now return with:
```
Access-Control-Allow-Origin: https://portal.company.com
```

**Why it works:** CORS is a browser security mechanism, not a Salesforce authentication mechanism. Adding the origin to the CORS allowlist causes Salesforce to include the `Access-Control-Allow-Origin` response header, which tells the browser the cross-origin request is permitted. Server-to-server calls (cURL, Apex callouts, integration middleware) bypass CORS entirely and are not affected by this setting.

---

## Anti-Pattern: Using Trusted IP Ranges to "Lock Down" Admin Access

**What practitioners do:** An admin wants to restrict logins to only come from the office. They add the office IP range to Setup > Security > Network Access (Trusted IP Ranges), assuming this blocks logins from outside that range.

**What goes wrong:** Trusted IP Ranges only bypass the email verification challenge — they do not restrict logins. Users from any IP can still log in; they just get an email challenge if outside the trusted range. The intent of "only allow logins from these IPs" is not achieved.

**Correct approach:** Add Login IP Ranges to the profile(s) that should be restricted (Setup > Profiles > [Profile] > Login IP Ranges). This is a hard deny: logins from outside the specified ranges are rejected entirely.
