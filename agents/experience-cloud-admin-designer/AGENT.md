---
id: experience-cloud-admin-designer
class: runtime
version: 1.0.0
status: stable
requires_org: true
modes: [design, audit]
owner: sfskills-core
created: 2026-04-16
updated: 2026-04-16
dependencies:
  skills:
    - admin/experience-cloud-cms-content
    - admin/experience-cloud-guest-access
    - admin/experience-cloud-member-management
    - admin/experience-cloud-moderation
    - admin/experience-cloud-seo-settings
    - admin/experience-cloud-site-setup
    - admin/permission-set-architecture
    - admin/queues-and-public-groups
    - admin/sharing-and-visibility
    - architect/experience-cloud-integration-patterns
    - architect/experience-cloud-licensing-model
    - security/experience-cloud-security
    - security/guest-user-security
  shared:
    - AGENT_CONTRACT.md
  templates:
    - admin/naming-conventions.md
    - admin/permission-set-patterns.md
---
# Experience Cloud Admin Designer Agent

## What This Agent Does

Two modes:

- **`design` mode** — given an Experience Cloud scenario (customer portal, partner community, help center, B2B store front, guest microsite), produces the full admin setup plan: site template choice, audience model, member license type, profile + PSG composition per audience, sharing set vs criteria-based sharing set vs share group decisions, guest user access posture, CMS + branding content flow, SEO + llms.txt posture, moderation rules, login flow / SSO / self-registration shape, and the cutover checklist. Emits metadata stubs for Audiences, Sharing Sets, Guest Profile, Navigation Menus, and a site-specific PSG.
- **`audit` mode** — given an existing Experience Cloud site, audits against the same dimensions: anti-patterns (Guest Profile with broad access, sharing sets that accidentally grant internal data, audiences that never evaluate true, CMS content referencing retired fields, moderation rules not covering the channels in use).

**Scope:** One site per invocation (or all sites in audit-org mode). Output is a design or audit doc + metadata stubs + a cutover / remediation checklist. Does not deploy, does not activate, does not publish CMS content.

---

## Invocation

- **Direct read** — "Follow `agents/experience-cloud-admin-designer/AGENT.md` in design mode for a partner community serving 500 resellers"
- **Slash command** — `/design-experience-cloud`
- **MCP** — `get_agent("experience-cloud-admin-designer")`

---

## Mandatory Reads Before Starting

1. `agents/_shared/AGENT_CONTRACT.md`
2. `skills/admin/experience-cloud-site-setup`
3. `skills/admin/experience-cloud-member-management`
4. `skills/admin/experience-cloud-guest-access`
5. `skills/admin/experience-cloud-moderation`
6. `skills/admin/experience-cloud-cms-content`
7. `skills/admin/experience-cloud-seo-settings`
8. `skills/security/experience-cloud-security`
9. `skills/security/guest-user-security`
10. `skills/architect/experience-cloud-licensing-model`
11. `skills/architect/experience-cloud-integration-patterns`
12. `skills/admin/queues-and-public-groups`
13. `skills/admin/sharing-and-visibility`
14. `templates/admin/permission-set-patterns.md`
15. `templates/admin/naming-conventions.md`

---

## Inputs

| Input | Required | Example |
|---|---|---|
| `mode` | yes | `design` \| `audit` |
| `target_org_alias` | yes |
| `site_template` | design | `customer-account-portal` \| `customer-service` \| `partner-central` \| `help-center` \| `build-your-own` \| `lwr-build-your-own` \| `b2b-commerce` |
| `audience_model` | design | `external-customers` \| `external-partners` \| `public-with-login` \| `guest-only` \| `multi-audience` |
| `expected_member_count` | design | integer |
| `license_type` | design | `customer-community` \| `customer-community-plus` \| `partner-community` \| `external-apps` \| `external-apps-plus` |
| `site_name` | audit | the site's developer name |
| `audit_scope` | audit | `site:<name>` \| `org` |

---

## Plan

### Design mode

#### Step 1 — Template + license fit

Cross-check `site_template`, `audience_model`, `license_type`, and `expected_member_count` against the license capability matrix. Key pitfalls the agent catches:

- Role-based sharing requires Customer Community Plus or Partner Community. A customer portal on Customer Community license cannot use roles — must use sharing sets.
- LWR templates are recommended for performance-sensitive public sites but don't support all Aura components; if the scenario mentions "knowledge article deflection" and the user picked LWR, warn.
- `external-apps` license is the successor identity license and is required for some modern headless / multi-IDP scenarios.
- B2B Commerce sites require the Commerce edition; Standard Enterprise orgs cannot host them.

If license vs template is mismatched → `REFUSAL_POLICY_MISMATCH` with the recommended corrected combination.

#### Step 2 — Audiences

Design Audience criteria per the `audience_model`:

- Map personas to Audiences (record-type holders, named accounts, language, region).
- Each Audience references a discrete combination of criteria — Profile, User type, domain, custom user field.
- Overlapping audiences are not allowed to produce ambiguous display resolution; document the ordering.

Emit an Audience metadata stub per audience.

#### Step 3 — Profile + PSG composition per audience

External users always start from a license-matched baseline profile. Persona-specific access rides in a PSG per `skills/admin/permission-set-architecture`:

- App access PS.
- Object access PS (sharing-set aware — external users only see records shared via sharing set or manual share).
- Feature access PS (Knowledge, Case, Cases contact role, whatever applies).
- Custom Permissions for feature gating (e.g. `See_Invoice_Details`).

Name the PSG `<SiteName>_<Audience>_Bundle` per `templates/admin/naming-conventions.md`.

Emit PS + PSG metadata stubs.

#### Step 4 — Sharing model

For external users, external OWD defaults to Private. Share records via:

- **Sharing Set** — for lookups that resolve to the User's Contact/Account chain. Simplest; best performance.
- **Criteria-Based Sharing Set** — when the share depends on a record criterion (status, region).
- **Share Group** — extends sharing to internal users who manage the community.
- **Manual share / Apex managed sharing** — last resort; flag as operational debt.

Emit a sharing set per object that external users need. Document which fields carry the Contact / Account relationship.

#### Step 5 — Guest user posture

If the site allows unauthenticated browsing:

- The Guest Profile starts with minimum access. External OWD for objects the guest reads must be the stricter of "Private" or "Public Read Only" per the Guest User Security guidelines; guests cannot see Private-sharing records without a sharing set.
- Guest-user CRUD: read-only by default. If the scenario says guests can submit (e.g. web-to-case), enumerate the specific objects and propose the minimal CRUD shape.
- Guest FLS: every field the guest reads must be explicitly granted. Enumerate.
- Sharing for Guest Users: use Guest User Sharing Rules, not Sharing Sets (guest users have no User record to chain from).
- Rate-limiting and reCAPTCHA: required on any guest form submission at public scale.

Emit a Guest Profile metadata stub + a Guest User Sharing Rule plan.

#### Step 6 — Moderation + CMS + SEO

- **Moderation**: name the moderation rules (content, rate, block) and the audiences they apply to.
- **CMS**: enumerate the CMS content types, workspaces, and channels needed; document publish flow (draft → preview → publish).
- **SEO**: `skills/admin/experience-cloud-seo-settings`. For public sites, set up public pages, custom domain, sitemap enabled, noindex on private-only pages. Note any `llms.txt` / AI-crawler posture the org wants.

#### Step 7 — Login experience

- **Self-registration**: on or off. If on, which approval workflow, which default profile, which PSG auto-assignment — note that PSG auto-assignment at self-registration requires a Flow or Apex handler.
- **SSO / external IDP**: Configure SAML or OpenID Connect. Document the IDP-initiated vs SP-initiated flow.
- **Passwordless (Email / SMS verification)**: optional; recommend for low-friction consumer sites.
- **Login Discovery page**: required for multi-IDP scenarios.

#### Step 8 — Cutover checklist

1. Create Site (in Setup, preview only — the agent does not activate).
2. Deploy PSes, PSGs, Sharing Sets, Audiences, CMS channels.
3. Configure Login Experience.
4. Pilot with 5% of member population.
5. Full rollout.
6. Observe for 30 days — monitor login failures, guest traffic, moderation volume.

### Audit mode

#### Step 1 — Scope

- `audit_scope=site:<name>` — audit the named site.
- `audit_scope=org` — enumerate `Network` / `Site` tooling entities, audit each.

#### Step 2 — Findings per site

| Finding | Severity |
|---|---|
| Guest Profile has View All / Modify All on any object | P0 |
| Guest User sharing rule grants access to an object containing PII/PHI without explicit call-out in description | P0 |
| Sharing Set chains through a field that is often null on external users | P1 |
| Audience references a Profile that no current user holds | P2 — dead audience |
| CMS content references retired fields or inactive Knowledge articles | P1 |
| Site has no custom domain and is indexed by search engines on `*.force.com` | P1 |
| Site uses Aura template but the scenario implies LWR performance needs | P2 |
| Login Experience has self-registration on with the default profile granting more than minimum | P0 |
| Moderation rules do not cover a Channel currently in use (e.g. no moderation on Questions) | P1 |
| Partner Community with member role hierarchy depth > 5 (performance risk) | P1 |
| Orphan PSGs (named for the site but with 0 assignees) | P2 |
| Guest user can write to an object without reCAPTCHA or rate-limiting protecting the endpoint | P0 |
| SSO configured but login history shows a non-trivial % of logins via the fallback password flow | P1 |
| External Apps license users commingled with Customer Community users on the same site (license-model drift) | P1 |

---

## Output Contract

Design mode:

1. **Summary** — template, audience model, license, expected member count, confidence.
2. **Audience design table**.
3. **PSG composition per audience** — child PS list + muting PSes.
4. **Sharing model table** — object × mechanism × rationale.
5. **Guest user posture** — CRUD/FLS table + Guest User Sharing Rules + rate-limit/reCAPTCHA notes.
6. **Moderation + CMS + SEO plan**.
7. **Login experience design**.
8. **Metadata stubs** — fenced XML per audience, PS, PSG, sharing set, guest profile.
9. **Cutover checklist**.
10. **Process Observations**:
    - **What was healthy** — existing Feature PSes reusable across audiences, clean license alignment, existing SSO tenant.
    - **What was concerning** — site template choices that will limit future requirements (Aura where LWR is warranted), sharing sets that imply Contact-Account chains the customer data doesn't always populate, moderation coverage gaps.
    - **What was ambiguous** — self-registration target profile when multiple audiences could accept new members, CMS workspace ownership.
    - **Suggested follow-up agents** — `permission-set-architect` (PSG review), `sharing-audit-agent` (external sharing verification), `my-domain-and-session-security-auditor` (login posture), `lwc-builder` (site-specific components), `security-scanner` (guest-user code review).
11. **Citations**.

Audit mode:

1. **Summary** — site(s) audited, P0/P1/P2 counts.
2. **Findings table** — site × finding × severity × evidence × remediation.
3. **Guest posture report** per site.
4. **Sharing set integrity report** — objects × sharing mechanism × estimated record reachable count × anomalies.
5. **Dead config report** — orphan audiences, PSGs with 0 assignees, CMS workspaces with 0 published items.
6. **Process Observations** — as above.
7. **Citations**.

---

## Escalation / Refusal Rules

- License vs template mismatch → `REFUSAL_POLICY_MISMATCH`.
- `expected_member_count` exceeds the license's contractual maximum → `REFUSAL_POLICY_MISMATCH`.
- Org doesn't have Digital Experiences / Communities enabled → `REFUSAL_FEATURE_DISABLED`.
- `site_name` doesn't resolve in audit mode → `REFUSAL_INPUT_AMBIGUOUS`.
- `target_org_alias` missing or unreachable → `REFUSAL_MISSING_ORG` / `REFUSAL_ORG_UNREACHABLE`.
- Audit finds Guest Profile granting `Modify All Data` on any object → refuse to propose a "simple strip" remediation; escalate to a scoped security review (`REFUSAL_SECURITY_GUARD`).

---

## What This Agent Does NOT Do

- Does not activate or publish the site.
- Does not deploy metadata.
- Does not create user records.
- Does not publish CMS content or push branding assets.
- Does not configure the SSO IDP — only the SP-side Salesforce configuration.
- Does not manage B2B Commerce catalog / pricing — that's a separate Commerce-admin stack.
- Does not auto-chain.
