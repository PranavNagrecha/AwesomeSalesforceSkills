# Gotchas — Org Setup And Configuration

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deploying My Domain Breaks Hardcoded Login URLs In Integrations

**What happens:** After My Domain is deployed to users, any external system that has the old login URL (`https://login.salesforce.com` or `https://test.salesforce.com`) hardcoded in OAuth callback URLs, SAML metadata, or Connected App endpoint configurations will fail to authenticate. Users who bookmarked the old login URL will be redirected, but machine-to-machine integrations that construct the authorization URL programmatically will break.

**When it occurs:** Immediately after deploying My Domain to users in production. Common victims: CI/CD pipeline credentials, ETL tools (MuleSoft, Informatica), managed packages that registered their OAuth callback against the legacy URL, and Salesforce mobile SDK apps using the old token endpoint.

**How to avoid:** Before deploying My Domain, audit all Connected Apps in the org (**Setup > App Manager**) and check their callback URLs. Update them to the new domain format. Similarly, update any external IdP (Okta, Azure AD) SAML configurations that reference `salesforce.com/saml`. After deployment, monitor integration logs for authentication failures on day 1 and day 2.

---

## Gotcha 2: Session Lock-To-IP Breaks Mobile And VPN Users Without Warning

**What happens:** When "Lock sessions to the IP address from which they originated" is enabled in Session Settings, any session request that arrives from a different IP than the one that created the session is immediately invalidated. The user sees a generic "Session expired" or login page with no explanation.

**When it occurs:** Users on mobile data connections (where the carrier dynamically reassigns IPs), users who switch from office WiFi to cellular (or VPN off to VPN on), or users behind load balancers that change source IPs. It also affects mobile app users more than desktop users.

**How to avoid:** Do not enable this setting in orgs with significant mobile usage or users on cellular networks. If it must be enabled for compliance, exempt mobile-device users via a separate profile or warn them about expected logouts when switching networks. The security benefit of IP-locking is largely superseded by MFA, which provides stronger session assurance without the UX disruption.

---

## Gotcha 3: Tightening Password Policy Does Not Immediately Expire Existing Passwords

**What happens:** An admin changes the org-level password policy to a shorter expiration window (e.g., from 90 days to 30 days) or adds complexity requirements. Existing users whose passwords were set under the old policy are not immediately affected. The new policy only applies to passwords set after the change date.

**When it occurs:** After any upward tightening of the password policy. The security change has no effect on the current user population until their passwords naturally expire or are manually reset.

**How to avoid:** To make the policy change effective immediately, use the **Expire All Passwords** button at the bottom of **Setup > Security > Password Policies**. This forces all users to change their password on next login. Plan this for a low-traffic period and communicate to users in advance to avoid support load.

---

## Gotcha 4: CSP Violations Are Silent To End Users

**What happens:** When a Lightning page, LWC, or Visualforce page attempts to load a resource from a domain not in CSP Trusted Sites, the browser silently blocks the resource. The component either renders blank, shows no image, or silently skips an API call. There is no Salesforce error message — only a browser console error.

**When it occurs:** During development or after deploying a new component that calls an external API or loads an external resource. Also occurs after an external vendor changes their CDN subdomain.

**How to avoid:** When a Lightning component appears blank or is missing expected content, always check **browser DevTools > Console** first. A CSP violation message will name the blocked domain and violated directive. Then navigate to **Setup > Security > CSP Trusted Sites** and add the specific domain and directive. For Apex callouts (server-side HTTP), the fix is **Setup > Security > Remote Site Settings**, not CSP Trusted Sites.

---

## Gotcha 5: MFA Enforcement Waiver Does Not Automatically Apply To New Integration Users

**What happens:** An admin enables org-wide MFA enforcement and then creates a new integration/service account user intended for API-only access. The new user's profile does not automatically inherit the MFA waiver — and if that user attempts a UI login, MFA is required.

**When it occurs:** When new API users are provisioned after org-wide MFA enforcement is turned on. Some automation scripts or ETL tools may attempt UI-session-based authentication instead of OAuth, which will fail if MFA is enforced and no waiver is set.

**How to avoid:** For API-only users, assign the **Waive Multi-Factor Authentication for Exempt Users** system permission via a permission set or profile, or use an integration user profile with the **API Only** user interface access restriction. Better still, migrate all API integrations to OAuth 2.0 JWT bearer token or client credentials flow, which never attempts a UI session and is outside the scope of MFA enforcement entirely.

---

## Gotcha 6: Deploying Security.settings Replaces The Whole Trusted-IP List

**What happens:** `networkAccess` is not merged into the org's existing trusted IP ranges — it replaces them. The Metadata API Developer Guide states it flatly under `NetworkAccess.ipRanges`: "To add an IP range, deploy all existing IP ranges, including the one you want to add. Otherwise, the existing IP ranges are replaced with the ones you deploy. To remove all the IP ranges, leave the `networkAccess` field blank (`<networkAccess></networkAccess>`)." A hand-written file containing only the one new range silently deletes every other range in the org.

**When it occurs:** Any time someone authors `Security.settings-meta.xml` from a template or from an example instead of from a fresh retrieve — which is exactly what an LLM asked to "add the Berlin office IP" will do. Symptom: users at every *other* site suddenly start receiving email identity-verification challenges on logins that used to be silent.

**How to avoid:** Retrieve `Settings:Security` from the target org immediately before editing, add your `<ipRanges>` block to the retrieved file, and diff the before/after. Treat the settings file as an overlay of whole containers, not a patch. The same applies in reverse for removal: an empty `<networkAccess></networkAccess>` is the documented way to clear the list, so an accidentally emptied container is a valid deploy that wipes it.

---

## Gotcha 7: You Cannot Register Or Rename A My Domain By Deploying MyDomain.settings

**What happens:** `myDomainName` and `myDomainSuffix` are both documented "This field is read-only in the API" in `MyDomainSettings`, as are `domainPartition`, `edgeRoutingMethod` and `useEdge`. A deploy that changes `<myDomainName>` does not move the org's domain. The other fields in the same file — the redirect and cookie behaviours — do deploy, so the deployment succeeds and reports success while the thing the author cared about did not happen.

**When it occurs:** When My Domain is treated as source-controlled config and someone tries to promote a domain name from a scratch-org definition or sandbox to production. Also when an agent is asked to "set up My Domain as metadata."

**How to avoid:** Register and deploy the domain name from the My Domain Setup page (a per-org, human, one-way action), then source-control the *behaviour* fields around it: `canOnlyLoginWithMyDomainUrl`, `doesApiLoginRequireOrgDomain`, `redirectPriorMyDomain`, `instancedUrlRedirectHandling`, `logRedirections`. Read `myDomainSuffix` as the enhanced-domains indicator (`MySalesforce` = enhanced, `MySalesforceLimited` = not) rather than expecting an `enhancedDomains` flag — there isn't one.

---

## Gotcha 8: Deploying A New My Domain Silently Resets redirectPriorMyDomain To true

**What happens:** `redirectPriorMyDomain` controls whether calls to the previous My Domain's URLs are forwarded to the current one. Per the guide: "When you deploy a new My Domain, this setting resets to its default, `true`." An org that had deliberately turned old-hostname redirection *off* — usually to force integrations onto the new URL and expose stragglers — gets it turned back on by the next domain change, and the stragglers go quiet again.

**When it occurs:** Any My Domain change after the first: a rebrand, a merger, moving to enhanced domains. The reset is not surfaced as a warning.

**How to avoid:** Re-assert `redirectPriorMyDomain` (and `doesWarnOnRedirect`, whose behaviour is gated on it) in the same change window as any domain change, and re-retrieve `Settings:MyDomain` afterwards to confirm the stored value. If you rely on redirection to buy migration time, set `logRedirections` to `true` so the Hostname Redirects event log tells you which callers are still on the old hostname before you switch it off.

---

## Gotcha 9: Session Timeout And Login Attempts Are Enums, Not Numbers

**What happens:** `sessionTimeout` accepts only `FifteenMinutes`, `ThirtyMinutes`, `SixtyMinutes`, `NinetyMinutes` (API 58.0+), `TwoHours`, `FourHours`, `EightHours`, `TwelveHours`, `TwentyFourHours` (API 38.0+). `maxLoginAttempts` accepts only `NoLimit`, `ThreeAttempts`, `FiveAttempts`, `TenAttempts`. `lockoutInterval` accepts only `FifteenMinutes`, `ThirtyMinutes`, `SixtyMinutes`, `Forever`. Writing `<sessionTimeout>120</sessionTimeout>` or `<maxLoginAttempts>5</maxLoginAttempts>` is a deploy error, not a coercion. Meanwhile `minimumPasswordLength` *is* a plain number as a string, valid 5 through 50 with a default of 8 — so the file mixes both conventions and the intuition "numbers are numbers" is wrong half the time.

**When it occurs:** Whenever the file is written by hand or generated from a requirements table that says "45 minutes" or "3 attempts." `FortyFiveMinutes` does not exist either — there is no 45-minute session timeout.

**How to avoid:** Map the business requirement onto the nearest legal enum before writing XML, and record the rounding in the change ticket. Run `scripts/check_org_setup_and_configuration.py`, which rejects values outside the documented enum lists rather than letting the deploy find them.

---

## Gotcha 10: The MFA Waiver Permission Overrides The Org-Wide MFA Setting

**What happens:** `enableMFADirectUILoginOptIn` "Requires all users in your Salesforce org to provide an additional verification method when logging in directly to the UI with their username and password." But the same field's documentation adds two exceptions: "Users who are already enabled via the **Multi-Factor Authentication for User Interface Logins** user permission experience no change" and "The **Waive Multi-Factor Authentication for Exempt Users** user permission **overrides this setting**." So the org-level switch is not the last word — a permission set assigned to a user beats it, and the org toggle gives no indication of who is exempt.

**When it occurs:** After an MFA rollout that only inspected the org setting. A profile or permission set granting the waiver — often created years earlier for an ETL account and since assigned to humans — leaves a population unprotected while the org-wide setting reads "enabled."

**How to avoid:** Treat MFA enforcement as two artefacts, not one: the `sessionSettings` field *and* an inventory of every permission set and profile granting the waiver permission. Audit the waiver assignment list on every review, not just the setting. Design of the permission side belongs to `security/mfa-enforcement-patterns` and `security/mfa-enforcement-strategy`; this skill owns only the deployable setting.

---

## Gotcha 11: disableTimeoutWarning Is Inverted And Independent Of Forced Logout

**What happens:** Two session fields look like one control and are not. `disableTimeoutWarning` "Indicates whether the session timeout warning popup is disabled (`true`) or enabled (`false`)" — so `true` means *no warning*, the opposite of what the name suggests to a reader skimming for "enable the warning." `forceLogoutOnSessionTimeout` is a separate field: "If enabled (`true`), the default, when sessions time out for inactive users, current sessions become invalid. The browser refreshes and returns to the login page." Setting the first to `true` and assuming it also stops the logout, or setting the second to `false` and assuming users still get warned, produces a session experience nobody designed.

**When it occurs:** During a "make sessions less annoying" change, where the intent is usually to keep the warning and lengthen the timeout, and the change lands as suppressing the warning instead — so users lose work at the timeout boundary with no prompt.

**How to avoid:** Set both fields explicitly in the file, never rely on defaults, and state the intended user-visible behaviour in the ticket in plain language ("users see a warning at T-30s, then are returned to the login page") so the reviewer can check the two booleans against it.

---

## Gotcha 12: canOnlyLoginWithMyDomainUrl In A Sandbox Disables The Sandboxes Page Log In Button

**What happens:** Hardening a sandbox by requiring My Domain logins has a documented side effect on admin access: "Admins can log in to a sandbox via the Log In action on the Sandboxes Setup page only when `canOnlyLoginWithMyDomainUrl` is `false` in the sandbox." Deploy `true` to a sandbox and the one-click Log In action from the production Sandboxes page stops working for everyone.

**When it occurs:** Immediately, whenever a hardened production `MyDomain.settings` file is deployed unchanged into sandboxes as part of "make sandboxes match production." It is discovered later, by an admin who can no longer reach a refreshed sandbox the convenient way.

**How to avoid:** Keep `canOnlyLoginWithMyDomainUrl` as a per-environment value rather than a promoted one — `true` in production, `false` in sandboxes — and record the divergence deliberately rather than letting a diff tool "fix" it. Confirm each sandbox's own My Domain login URL is documented and reachable before you change it in any environment.

---

## Gotcha 13: An Old CspTrustedSite File Redeployed On A New API Version Grants Nothing

**What happens:** The default behaviour when every `isApplicableTo*` field is `false` has changed three times. "In API version 49.0 and earlier, if all `isApplicable` fields are `false`, these fields all default to `true`." "In API version 50.0 to 58.0, if all `isApplicable` fields are `false`, the `isApplicableToImgSrc` field is set to `true`." "In API version 59.0 and later, for each trusted URL, at least one `CSPTrustedSite` starting with `isApplicable` or `canAccess` must be set to `true`." So a trusted site authored against an old API — which relied on all-false meaning all-allowed — grants everything on 49.0, only images on 50.0–58.0, and is invalid on 59.0+.

**When it occurs:** During an API-version bump of a long-lived repository, or when a `cspTrustedSites/` folder is copied out of an old package. The symptom is a component that worked for years rendering blank after an otherwise unrelated version bump, with only a browser-console violation to go on.

**How to avoid:** Set every directive field explicitly in every `CspTrustedSite` file — never leave the grant implicit in a version default. When bumping the project's API version, re-retrieve the `cspTrustedSites` folder and diff it; the org's stored values reveal which implicit default you were relying on. Keep the whole generated CSP header under 12 KB, since Salesforce records customer-reported issues as it approaches 16 KB.
