# Worked Examples — Portal Requirements Gathering

One portal, worked end to end from personas to a signed handoff. Every artefact below is
copy-and-adapt shaped: the persona/licence matrix, the access-model implications table, the
requirements catalogue YAML the checker lints, the authentication decision, the grounded NFRs,
and the handoff checklist that closes this skill and opens `admin/experience-cloud-site-setup`.

**Scenario.** Acme Cloud sells a B2B SaaS product to ~900 customer accounts, ~40 of which resell
through a reseller channel. Support runs 3,800 contacts/month. The ask is a customer self-service
support portal: case deflection for end users, account-wide case visibility for customer admins,
a public Knowledge base for search-engine traffic, and pipeline visibility for the resellers.

---

## 1. Persona / licence matrix

Every persona is a row. A persona with no distinct record-visibility need is not a persona — merge it.

| Persona | Records they must see | Licence implied | Login vs member | Cheat-sheet API allocation (Enterprise / Professional) |
|---|---|---|---|---|
| End customer (support contact) | Own Cases; published Knowledge | Customer Community Login | Login-based — logs in a few times a year to check one case | `Customer Community Login: 0` API calls per licence per 24 h |
| Customer admin (account-wide) | Every Case on their Account, entitlement + contract records | Customer Community Plus | Member-based — logs in weekly | `Customer Community Plus: 200` |
| Reseller channel manager | Cases on child accounts, plus Leads and Opportunities | Partner Community | Member-based — daily user | `Partner Community: 200` |
| Anonymous visitor | Published Knowledge only, no records | Guest (no user licence consumed) | n/a — never authenticates | No per-licence row; guest traffic runs under the site's guest user |
| Internal support agent | Everything they already see internally | Existing internal Salesforce licence | Member of the site by profile / permission set | `Salesforce: 1,000` |

Grounded in *Salesforce Developer Limits and Allocations Quick Reference* (App Limits cheat sheet),
"Total API Request Allocations", L525–L547 for Enterprise / Professional Edition and L555–L585 for
Unlimited / Performance Edition. The same table states the org total as
`100,000 + (number of licenses x calls per license type) + purchased API Call Add-Ons` (L529–L531).

Read the two implications off the table rather than asserting them:

- **The gap between `Customer Community Login: 0` and `Customer Community Plus: 200` is an
  architecture input, not trivia.** A persona on a licence with a 0-call allocation contributes
  nothing to the org's API ceiling, so a mobile app or middleware that calls the API *as that user*
  has no headroom of its own to draw on.
- **The `... Login` variants exist as distinct rows with distinct allocations** (`Customer Community
  Plus Login: 10`, `Partner Community Login: 10`, cheat sheet L538–L539 and L547). Which of the two
  variants a persona takes is a commercial decision — send it to
  `skills/architect/experience-cloud-licensing-model`, which owns login-vs-member selection.
- Internal users are site members only if `allowInternalUserLogin` is set on the `Network` and their
  profile or permission set appears in `networkMemberGroups` (Metadata API Guide, `Network`
  L90695–L90697 and `NetworkMemberGroup` L91430–L91443).

---

## 2. Access-model implications

Each visibility requirement resolves to exactly one mechanism, one metadata type, and one skill that
builds it. This skill decides *which*; it does not author the XML.

| Requirement | External OWD needed | Mechanism | Metadata type | Built by |
|---|---|---|---|---|
| End customer sees only their own Cases | `Case` external = Private | Record ownership (the portal user owns the Case) | `CustomObject` → `externalSharingModel` | `skills/admin/sharing-and-visibility` |
| Customer admin sees every Case on their Account | `Case` external = Private | Sharing set: `object` Case, `userField` Account, `objectField` AccountId | `SharingSet` / `AccessMapping` | `skills/admin/sharing-and-visibility` (owns the SharingSet XML) |
| Reseller manager sees their reps' Opportunities | `Opportunity` external = Private | Partner account role hierarchy (roles created per partner account) + `User.PortalRole` | `RoleOrTerritory`, `User.PortalRole` | `skills/admin/sharing-and-visibility` + `skills/architect/experience-cloud-licensing-model` |
| Anonymous visitor reads published Knowledge | n/a — no record ownership | Guest profile object access + data category visibility | `Profile.categoryGroupVisibilities` (`ALL` / `CUSTOM` / `NONE`) | `skills/admin/experience-cloud-guest-access` + `skills/security/guest-user-security` |
| Members can see each other in the site directory | n/a | Site-level member visibility switches | `Network.enableMemberVisibility`, `Network.enableGuestMemberVisibility` | `skills/admin/experience-cloud-member-management` |
| Reseller must not see another reseller's deals | `Opportunity` external = Private | Account-scoped hierarchy only — no cross-account sharing rule | `RoleOrTerritory` | `skills/admin/sharing-and-visibility` |

Sharing-set mechanics are grounded in the Metadata API Guide, `SharingSet` / `AccessMapping`,
L130365–L130470: `accessLevel` is `Read` or `Edit`; `object` is one of Account, Campaign, Contact,
Case, custom objects, Opportunity, Order, ServiceContract, User, WorkOrder; `userField` is one of
`Account`, `Account.Field`, `Contact`, `Contact.Field`, `Contact.RelatedAccount`, `Manager.Account`,
`Manager.Contact`. Read `standards/decision-trees/sharing-selection.md` before committing a row in
the Mechanism column — do not re-derive the choice here.

---

## 3. Requirements catalogue

The machine-readable artefact this skill produces. `scripts/check_portal_requirements_gathering.py
--file <path>` lints it. Every row names the persona it serves, the licence that row implies, the
access mechanism that satisfies it, and the downstream skill or agent that turns it into config.

```yaml
# acme-portal-requirements.yaml
portal: acme-cloud-customer-portal
network_api_name: Acme_Support          # the Network metadata component the site will deploy as
url_path_prefix: support                # Network.urlPathPrefix
data_period: "2026-05-01 to 2026-07-31"
baseline_containment_rate_pct: 11

requirements:
  - id: PR-001
    statement: "As a support contact I can view the status and comments of the Cases I raised, without emailing support."
    persona: end-customer
    licence_implication: customer-community-login
    access_mechanism: ownership
    content_type: record
    auth: self-registration
    downstream: skills/admin/experience-cloud-member-management
    owner: "Priya Raman (Support Ops)"
    status: approved
    notes: "Deflects contact reasons #1 and #3 (case status chase, 640/month combined)."

  - id: PR-002
    statement: "As a customer admin I can view every Case raised by anyone on my Account, including cases I did not raise."
    persona: customer-admin
    licence_implication: customer-community-plus
    access_mechanism: sharing-set
    content_type: record
    auth: sso
    downstream: skills/admin/sharing-and-visibility
    owner: "Priya Raman (Support Ops)"
    status: approved
    notes: >
      Sharing set mapping: object Case, userField Account, objectField AccountId, accessLevel Read.
      Confirm the admin profile is on a licence that appears in the SharingSet Special Access Rules list.

  - id: PR-003
    statement: "As a reseller channel manager I can see the Leads and Opportunities registered by my own reps."
    persona: reseller-channel-manager
    licence_implication: partner-community
    access_mechanism: account-role-hierarchy
    content_type: record
    auth: sso
    downstream: skills/admin/partner-community-requirements
    owner: "Dan Ochieng (Channel)"
    status: approved
    notes: "Requires Lead + Opportunity object access. Confirm Sales Cloud is present before build."

  - id: PR-004
    statement: "As an anonymous visitor I can read published how-to Knowledge articles found via a search engine."
    persona: anonymous-visitor
    licence_implication: guest
    access_mechanism: data-category-visibility
    content_type: knowledge
    auth: guest
    downstream: skills/admin/experience-cloud-guest-access
    owner: "Priya Raman (Support Ops)"
    status: approved
    guest_review: "Sam Okafor (Security) — signed 2026-08-19"
    notes: >
      Only the Public data category is exposed. Guest read access is deliberately scoped to
      Knowledge; no sObject read is granted to the guest profile.

  - id: PR-005
    statement: "As a customer admin I can download the invoice PDFs filed against my Account."
    persona: customer-admin
    licence_implication: customer-community-plus
    access_mechanism: sharing-set
    content_type: file
    auth: sso
    downstream: skills/admin/experience-cloud-cms-content
    owner: "Lena Fischer (Finance Ops)"
    status: in-review
    notes: "Blocked pending confirmation that invoices are ContentVersion, not an external system link."

  - id: PR-006
    statement: "As a support contact I can browse product announcements and release notes published by marketing."
    persona: end-customer
    licence_implication: customer-community-login
    access_mechanism: not-applicable
    content_type: cms
    auth: login-only
    downstream: skills/admin/experience-cloud-cms-content
    owner: "Marcus Hale (Product Marketing)"
    status: approved
    notes: "CMS content, not records — no sharing mechanism applies."

  - id: PR-007
    statement: "As a community member I can post questions to a peer forum and see other members' names."
    persona: end-customer
    licence_implication: customer-community-login
    access_mechanism: object-permission-only
    content_type: record
    auth: login-only
    downstream: skills/admin/community-engagement-strategy
    owner: "Priya Raman (Support Ops)"
    status: deferred
    notes: >
      Deferred to phase 2 behind the deflection gate. Member visibility is a Network switch
      (enableMemberVisibility); moderation is a precondition — see skills/admin/experience-cloud-moderation.
```

Field contract enforced by the checker:

| Field | Rule |
|---|---|
| `id` | Required, unique across the file |
| `statement` | Required, non-empty |
| `persona` | Required — must match a row in the persona/licence matrix |
| `licence_implication` | Required, one of the allowed licence values |
| `access_mechanism` | Required, one of the allowed mechanisms (`ownership`, `sharing-set`, `sharing-rule`, `account-role-hierarchy`, `partner-super-user`, `apex-managed-sharing`, `manual-share`, `external-owd`, `guest-public-page`, `guest-sharing-rule`, `data-category-visibility`, `object-permission-only`, `not-applicable`) |
| `content_type` | Required, one of `record` / `knowledge` / `cms` / `file` / `external-object` / `static-page` |
| `auth` | Required, one of `self-registration` / `sso` / `admin-provisioned` / `login-only` / `guest` |
| `downstream` | Required — a repo path is resolved on disk; a free-text owner name is accepted |
| `owner` | Required, non-empty |
| `status` | Required, one of `draft` / `in-review` / `approved` / `deferred` / `out-of-scope` |
| `guest_review` | Required **only** on rows whose licence, auth, or mechanism is guest-facing |

Run it:

```bash
python3 skills/admin/portal-requirements-gathering/scripts/check_portal_requirements_gathering.py \
  --file acme-portal-requirements.yaml

# lint every catalogue in a folder
python3 skills/admin/portal-requirements-gathering/scripts/check_portal_requirements_gathering.py \
  --manifest-dir requirements/

# the narrative workshop doc still lints separately
python3 skills/admin/portal-requirements-gathering/scripts/check_portal_requirements_gathering.py \
  --doc acme-portal-requirements.md
```

---

## 4. Authentication decision

One decision per persona, recorded with what it costs downstream. `Network.selfRegistration` and
`Network.selfRegProfile` are the two fields that carry it (Metadata API Guide, `Network`,
L91038–L91045: `selfRegProfile` is "the profile assigned to users who self-register. This value is
used only if `selfRegistration` is enabled for the site").

| Persona | Decision | Why | What it obliges |
|---|---|---|---|
| End customer | **Self-registration** | 900 accounts, long tail of individual contacts; admin provisioning does not scale | A matching + duplicate rule on Contact before go-live — see `skills/admin/duplicate-management`. Self-registration lands a person who may already exist as a Contact. |
| Customer admin | **SSO** to the customer's own IdP where they have one; admin-provisioned otherwise | These users hold account-wide visibility; identity must be revocable by the customer, not by us | A per-customer IdP onboarding runbook — see `skills/security/sso-configuration` |
| Reseller channel manager | **SSO**, mandatory | Channel staff turnover is high and deals are commercially sensitive | Same as above, plus deprovisioning on the channel-agreement termination path |
| Anonymous visitor | **Guest** | Search-engine reach is the point of the public Knowledge base | Guest profile lockdown as a named build deliverable — `skills/admin/experience-cloud-guest-access` |

`Network.selfRegistration` is a **site-level** boolean, not a per-persona one. If any persona
self-registers, self-registration is on for the site, and every self-registered user lands on the
single `selfRegProfile`. Personas that must not self-register are separated by profile and licence
after registration, or by a registration handler — not by the switch.

---

## 5. Non-functional requirements

Only the NFRs that rest on a published allocation are stated as numbers here. Everything else is a
target the team sets and measures.

| NFR | Value | Ground |
|---|---|---|
| Org API ceiling the portal's integrations draw on | `100,000 + (licences x per-licence calls) + purchased add-ons` per 24 h | App Limits cheat sheet L529–L531 |
| API headroom contributed by end-customer personas | Zero — `Customer Community Login: 0` | App Limits cheat sheet L534–L535 |
| API headroom contributed by customer-admin and reseller personas | 200 calls per licence per 24 h each | App Limits cheat sheet L536–L537, L546 |
| Portal page load target | Set by the team; measure with the site's own analytics, not an assumed figure | UNVERIFIED (2026-09-04): no Experience Cloud page-load or guest-concurrency figure exists in the extracted App Limits, Metadata API, or Object Reference PDFs. State the team's own target and its measurement method instead of a platform number. |
| Guest traffic ceiling | Treat as unknown at requirements time and confirm with Salesforce before committing an SLA on the public Knowledge base | UNVERIFIED (2026-09-04): no guest-user request ceiling appears in the extracted App Limits cheat sheet. |

---

## 6. Handoff checklist to `admin/experience-cloud-site-setup`

Requirements are done when a builder can start without asking a question. Tick every row before the
handoff meeting.

```markdown
- [ ] Persona/licence matrix signed, one row per distinct visibility need
- [ ] Every persona maps to a licence value the org either owns or has a procurement request for
- [ ] Requirements catalogue passes `check_portal_requirements_gathering.py --file`
- [ ] Every catalogue row has a `downstream` that resolves to a real skill, agent, or named owner
- [ ] External OWD per object recorded, and each divergence from internal OWD justified
      -> hands to skills/admin/sharing-and-visibility
- [ ] Sharing-set rows name object / userField / objectField / accessLevel
      -> hands to skills/admin/sharing-and-visibility, which authors the SharingSet XML
- [ ] Guest rows carry a named security reviewer in `guest_review`
      -> hands to skills/admin/experience-cloud-guest-access and skills/security/guest-user-security
- [ ] Authentication decision recorded per persona; self-registration rows name the duplicate control
      -> hands to skills/admin/duplicate-management and skills/security/sso-configuration
- [ ] Knowledge rows name the data category group and the categories the external profile may see
      -> hands to skills/admin/knowledge-base-administration
- [ ] Content rows separated into record / Knowledge / CMS / file
      -> CMS rows hand to skills/admin/experience-cloud-cms-content
- [ ] Any user-generated-content row has a moderation precondition recorded
      -> hands to skills/admin/experience-cloud-moderation
- [ ] Public-page rows flagged for indexing review
      -> hands to skills/admin/experience-cloud-seo-settings
- [ ] Deferred rows carry the gate that releases them (not "phase 2")
- [ ] Site identity decided: Network api name, urlPathPrefix, and the CustomSite it will bind to
```

The `/design-experience-cloud` run-time agent
(`agents/experience-cloud-admin-designer/AGENT.md`) consumes this catalogue as its input. Its
Mandatory Reads list assumes the licence and access decisions on this page are already made — hand
it a catalogue with `status: draft` rows and it will produce a design full of assumptions.

---

## Source lines used on this page

- App Limits cheat sheet, "Total API Request Allocations": L525–L547 (Enterprise / Professional),
  L555–L585 (Unlimited / Performance), L605 ("For Experience Cloud limits, see Experience Cloud User Licenses")
- Metadata API Guide: `SharingSet` L130365–L130470; `Network` L90671–L91060 and the sample
  definition L91807–L91845; `NetworkMemberGroup` L91430–L91443; `CustomSite` L46743–L47060;
  `ProfileCategoryGroupVisibility` L97911–L97930
- Object Reference: `User.AccountId` L294996–L295003, `User.ContactId` L295088–L295100,
  `User.PortalRole` L295663–L295678; `NetworkMember` L188296–L188305; `NetworkMemberGroup`
  L188595–L188600; `Profile.UserType` L232430–L232480
