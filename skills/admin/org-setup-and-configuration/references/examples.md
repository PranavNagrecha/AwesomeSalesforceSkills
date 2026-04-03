# Examples — Org Setup And Configuration

## Example 1: New Production Org — My Domain + MFA Setup Before Go-Live

**Context:** A project team is preparing a net-new Salesforce Sales Cloud production org for go-live in 6 weeks. The org will use SSO via Okta. They have not yet registered My Domain or enabled MFA.

**Problem:** The team learns that My Domain is required for SSO configuration and that SAML callback URLs must reference the custom subdomain. They also need MFA enforced at go-live as per Salesforce's contractual requirement. If they configure SSO before My Domain is deployed, the SAML callback URL will use `login.salesforce.com` and will break when My Domain is deployed.

**Solution:**

1. Register My Domain early: **Setup > Company Settings > My Domain**. Choose a subdomain (`mycompany.my.salesforce.com`). Salesforce provisions the domain within minutes for sandboxes and up to 24 hours for production.
2. Verify the new domain URL works: open a private browser window and log in at `mycompany.my.salesforce.com/login`.
3. Deploy to Users: **My Domain > Deploy to Users**. All users are redirected to the custom domain URL.
4. Configure the Okta SAML integration with the `mycompany.my.salesforce.com` Issuer and callback URL — now that My Domain is stable.
5. Navigate to **Setup > Identity > MFA Management and Setup**. Enable the org-wide **Require MFA** toggle. Okta users whose IdP performs MFA are automatically exempted.
6. Verify: have a test user log in directly (bypassing SSO). Confirm MFA is prompted. Have the Okta test user log in via SSO — confirm no Salesforce MFA prompt appears (IdP satisfies the requirement).

**Why it works:** My Domain deployment must precede any SSO configuration that references the org's login URL. MFA enforcement can be applied via the org-wide toggle without needing to touch individual profiles once all SSO users are exempted through the IdP.

---

## Example 2: Lightning Page CSP Error — External Analytics Widget Blocked

**Context:** A development team embeds a third-party analytics dashboard widget inside a Lightning App Page using an LWC iframe-based component. After deploying to the sandbox, the widget displays a blank area. No Salesforce error is shown.

**Problem:** The Lightning Experience CSP blocks the external domain (`https://analytics.thirdparty.com`) because no CSP Trusted Site entry exists for it. The LWC iframe attempt is silently blocked. The team checks browser DevTools and sees: `Refused to frame 'https://analytics.thirdparty.com/' because it violates the following Content Security Policy directive: "frame-src 'self'"`.

**Solution:**

1. Open browser DevTools > Console. Copy the blocked domain and directive from the CSP error message.
2. Navigate to **Setup > Security > CSP Trusted Sites > New Trusted Site**.
3. Name: `ThirdPartyAnalytics`. URL: `https://analytics.thirdparty.com`. Check only **frame-src** (since the violation is iframe embedding, not script or fetch).
4. Save. Refresh the Lightning page.
5. If additional violations appear (e.g., the embedded dashboard itself loads scripts from another subdomain), repeat for each blocked domain/directive pair.

**Why it works:** Lightning Experience CSP is a browser-enforced whitelist. Each directive must be explicitly permitted per domain. Adding only the necessary directive (`frame-src`) follows the principle of least-privilege — do not check all directives when only one is needed.

---

## Example 3: Password Expiry Creating Go-Live Day Disruption

**Context:** An org has the default 90-day password expiration policy. The project team does User Acceptance Testing 60 days before go-live, creating user accounts for 200 test users. At go-live, these accounts are reused for production — but 30 days have elapsed since their creation, leaving only 30 days before mandatory expiry.

**Problem:** Thirty days after go-live, 200 users are simultaneously prompted to change their password. Support is overwhelmed. Some users cannot log in until the password reset completes.

**Solution (preventive):** After UAT is complete, use the **Expire All Passwords** button at the bottom of **Setup > Security > Password Policies** immediately before go-live. This resets the password age clock for all users and gives the full 90-day window from go-live day.

Alternatively, set the expiration period to **Never** if the org relies on SSO + MFA for all users (password expiry is not adding security when SSO enforces re-authentication).

**Why it works:** Password expiry date is calculated from the last password change, not from go-live. Forcing expiry immediately before launch resets the clock uniformly. For SSO-only orgs, disabling password expiry eliminates a friction point with no security loss.

---

## Anti-Pattern: Adding All CSP Directives for Every External Domain

**What practitioners do:** When a CSP trusted site is needed for a new integration, the admin checks all available directive checkboxes (connect-src, style-src, img-src, font-src, frame-src, media-src) to "make sure it works."

**What goes wrong:** The domain is trusted for far more than necessary. Over time, dozens of entries accumulate with all directives checked and no documented business justification. Stale entries for defunct integrations remain indefinitely. Note: Salesforce does not expose `script-src` through CSP Trusted Sites — external JavaScript must be hosted as a static resource instead.

**Correct approach:** Check only the specific directive(s) actually required. Open browser DevTools and read the CSP violation message — it specifies exactly which directive was violated. Grant only that directive. Document the reason in the CSP Trusted Sites entry name or a separate exception register.
