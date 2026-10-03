# Gotchas: Org Hardening And Baseline Config

Non-obvious Salesforce platform behaviors that cause real production problems in this domain. Each gotcha names the official source it rests on.

## Gotcha 1: Deploying `networkAccess` Replaces Every Trusted IP Range

**What happens:** A team adds one office range to `Security.settings-meta.xml` and deploys it. Every other trusted IP range in the org disappears, because the deployed list replaces the existing list. Users outside the remaining ranges start getting device activation challenges.

**When it occurs:** Any Metadata API or CLI deploy of `SecuritySettings` that contains a `networkAccess` element with a partial list. An empty `<networkAccess></networkAccess>` removes all ranges.

**How to avoid:** Retrieve `Settings:Security` immediately before editing, keep the full `ipRanges` list in the file, and review the diff for removed ranges. Leave `networkAccess` out of baseline files that are not meant to manage IP ranges.

**Source:** Metadata API Developer Guide, SecuritySettings > NetworkAccess `ipRanges`: "To add an IP range, deploy all existing IP ranges, including the one you want to add. Otherwise, the existing IP ranges are replaced with the ones you deploy."

---

## Gotcha 2: Trusted IP Ranges Don't Block Logins

**What happens:** A security team adds the corporate range under Network Access and believes logins from elsewhere are blocked. They are not. Trusted ranges only let users log in without device activation. Users outside the range still log in after verifying their identity.

**When it occurs:** Hardening plans that read "Trusted IP Ranges" as an access restriction.

**How to avoid:** Restrict logins with Login IP Ranges on profiles. Turn on `enforceIpRangesEveryRequest` when the range must also apply to every page request and client app, not just login.

**Source:** Metadata API Developer Guide, NetworkAccess ("The trusted IP address ranges from which users can always log in without requiring computer activation") and SessionSettings `enforceIpRangesEveryRequest`. Salesforce Security Guide, Profiles section on Login IP Ranges and "Enforce login IP ranges on every request".

---

## Gotcha 3: Profile Session and Password Policies Override the Org-Wide Values

**What happens:** The org-wide session timeout is tightened to 30 minutes and the minimum password length raised to 12. Users on a profile with its own session timeout of 12 hours and its own password policy see no change.

**When it occurs:** Orgs where some profiles carry `ProfileSessionSetting` or `ProfilePasswordPolicy` values, often set years ago for a specific integration or portal.

**How to avoid:** Retrieve `ProfileSessionSetting` and `ProfilePasswordPolicy` with the org settings, list every override, and decide each one.

**Source:** Metadata API Developer Guide, ProfileSessionSetting `sessionTimeout` ("applies to users of the profile and overrides the org-wide timeout value. Changes to the org-wide timeout value don't apply to users of this profile") and ProfilePasswordPolicy ("Profile password policies override org-wide password policies for that profile's users").

---

## Gotcha 4: `requireHttpOnly` Breaks JavaScript That Reads the Session Cookie

**What happens:** HttpOnly is enabled as a hardening step. A custom or packaged application that reads the session ID cookie from JavaScript stops working.

**When it occurs:** Orgs with legacy Visualforce pages, custom JavaScript, or managed packages that read cookies in the browser.

**How to avoid:** Search custom code for `document.cookie` and `sid` access, ask package vendors, and test in a sandbox before enabling `requireHttpOnly` in production.

**Source:** Metadata API Developer Guide, SessionSettings `requireHttpOnly`: "If you have a custom or packaged application that uses JavaScript to access session ID cookies, your application breaks if requireHttpOnly is set to true."

---

## Gotcha 5: Large CSP Headers and Malformed Trusted URLs Fail Quietly

**What happens:** An org with hundreds of CSP Trusted Sites sees intermittent page errors as the CSP header grows. Separately, some trusted URLs never take effect because they are malformed; they were saved before February 2025 and are excluded from the generated header.

**When it occurs:** Trusted-site sprawl, and legacy entries such as `https://{subdomain}.example.com`.

**How to avoid:** Keep the CSP header under 12 KB, remove unused entries, prefer narrow directives, and clean up malformed URLs. In API version 59.0 and later, at least one `isApplicable...` or `canAccess...` field must be true on each entry.

**Source:** Metadata API Developer Guide, CspTrustedSite (header-size tip, `endpointUrl` malformed URL note, `isApplicableToMediaSrc` rule for API 59.0+).

---

## Gotcha 6: CORS Allowlist Patterns Have Strict Rules

**What happens:** A browser app on `https://app.example.com` gets HTTP 404 from Salesforce APIs although `*.example.com` is allowlisted, or an origin is allowlisted by IP while the app calls by hostname.

**When it occurs:** Allowlist entries without the HTTPS scheme, with a wildcard in the wrong place, or that mix IP and domain forms.

**How to avoid:** Use `https://` plus a domain, with the wildcard only in front of a second-level domain (`https://*.example.com`). Add an IP address and a domain that resolve to the same host as separate entries. A non-allowlisted origin receives HTTP 404.

**Source:** Metadata API Developer Guide, CorsWhitelistOrigin `urlPattern` and Usage.

---

## Gotcha 7: Health Check's Fix Risks Can't Change Every Setting

**What happens:** An admin clicks Fix Risks expecting the score to reach 100. Some settings remain, because they are not available on the Fix Risks screen. A custom baseline also lags when Salesforce adds new settings until the admin accepts them.

**When it occurs:** Health Check remediation sprints and orgs with custom baselines.

**How to avoid:** Fix remaining settings with the Edit link on the Health Check page, or in metadata. Open each custom baseline after a release and add the new settings.

**Source:** Salesforce Security Guide, Security Health Check ("Fix Risks Limitations"; "New settings to Security Health Check are added to the Salesforce Baseline Standard with default values. If you have a custom baseline, you're prompted to add the new settings when you open it").

---

## Gotcha 8: The Metadata API Sample Security.settings Is Not Well-Formed

**What happens:** A team copies the sample `security.settings` from the Metadata API guide as a starting point. The deploy fails to parse.

**When it occurs:** Copy-paste of the Summer '26 sample, which opens `<logoutURL>` and closes it with `</logoutUrl>`. The sample also sets weak values (for example `complexity` `NoRestriction` and `minimumPasswordLength` 5) that are only illustrations.

**How to avoid:** Start from the skill's own baseline file in [metadata-examples.md](metadata-examples.md), and validate XML before deploying.

**Source:** Metadata API Developer Guide, SecuritySettings "Declarative Metadata Sample Definition" (read 2026-10-03).
