# Knowledge Base Administration — Work Template

Use this template when setting up, reviewing, or troubleshooting Lightning Knowledge in a Salesforce org.

## Scope

**Skill:** `knowledge-base-administration`

**Request summary:** (fill in what the user asked for — e.g., "Set up Lightning Knowledge with two article types and audience-scoped visibility")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md:

- **Lightning Knowledge enabled?** (Yes / No — if No, confirm enablement is irreversible before proceeding)
- **Classic Knowledge in use?** (Yes / No — if Yes, migration plan must exist before enablement)
- **Content types needed:** (e.g., FAQ, How-To, Known Issue, Release Note)
- **Audience segments:** (e.g., Internal Agents, Partner Users, Customer Community)
- **Publishing surfaces in scope:** (Internal app only / Authenticated Experience Cloud site / Public guest Knowledge base)
- **Approval/review requirements:** (e.g., compliance officer sign-off required, or none)
- **Known constraints:** (e.g., default Data Category limits — 5 groups with 3 active at a time, 100 categories per group, 5 hierarchy levels; no existing category hierarchy)

---

## Record Type Design

| Record Type Name | Intended Audience | Key Fields | Page Layout Name | Profiles Assigned |
|---|---|---|---|---|
| (e.g., FAQ) | (e.g., All users) | (e.g., Question, Answer) | (e.g., FAQ Layout) | (e.g., Support Agent, Partner) |
| (e.g., Known Issue) | (e.g., Internal agents only) | (e.g., Root Cause, Workaround) | (e.g., Known Issue Layout) | (e.g., Support Agent) |

---

## Data Category Group Design

| Category Group | Purpose | Top-Level Categories | Visibility: Internal Agents | Visibility: Partners | Visibility: Customers |
|---|---|---|---|---|---|
| (e.g., Products) | Content org + visibility | (e.g., Product A, Product B) | All | Product A only | Product A only |

**Data Category Visibility mechanism per audience:** (Role / Permission Set / Profile — Salesforce ORs all three; a child role can be reduced below its parent but never raised above it)

**Guest / high-volume portal user visibility:** (these users have no role — record the Guest User profile or permission set that carries their Data Category Visibility, and the categories granted)

**Org-wide fallback:** (Default Data Category Visibility — what a user with no role/permission-set/profile visibility sees)

---

## Channel Matrix

One row per record type. Channels are publishing eligibility, independent of Data Category Visibility. Pick each flag from the *reader*, not from the site template: `IsVisibleInCsp` is authenticated customer users, `IsVisibleInPkb` is unauthenticated guests (including guests on a public-access Help Center). `IsVisibleInApp` is defaulted on create and not settable through the API, so it is shown here for reference only.

| Record Type | Customer (`IsVisibleInCsp`) | Partner (`IsVisibleInPrm`) | Public KB (`IsVisibleInPkb`) | Who approves external release? |
|---|---|---|---|---|
| (e.g., FAQ) | Yes | Yes | Yes | (e.g., Content Lead) |
| (e.g., Known Issue) | No | No | No | n/a — internal only |

---

## Experience Cloud Exposure (skip if internal app only)

Complete in order. Each row is a hard gate; skipping one produces an empty page, not an error.

- [ ] Knowledge manager permission set provisioned: object CRUD on Knowledge + Manage Articles + Manage Knowledge Article Import/Export + Manage Salesforce Knowledge + Publish Articles + **Share internal Knowledge articles externally** + Manage Data Categories
- [ ] Knowledge User checkbox confirmed on each author's user record
- [ ] **Topics enabled on the Knowledge object** (Setup > Topics for Objects > Knowledge; Title field selected) — articles cannot display outside the org without this
- [ ] Site template chosen: (Help Center — public-access, purpose-built for self-service Knowledge / general template — Knowledge assembled by hand)
- [ ] Salesforce Knowledge enabled on the site itself (distinct from org-level enablement)
- [ ] Channel flag set on the in-scope articles for the **reader**: `IsVisibleInCsp` for authenticated customers, `IsVisibleInPkb` for unauthenticated guests — a Help Center serving both needs both
- [ ] Data Category Visibility assigned to the external audience (role / permission set / profile; guests and high-volume portal users have no role)
- [ ] Topics assigned to articles (Content Management > Topics > Article Management, or Automatic Topic Assignment)
- [ ] Navigational Topics configured (browse tree); Featured Topics configured (home page)
- [ ] Knowledge components placed in Experience Builder (Topic Catalog / Top Articles by Topic / Trending Articles by Topic / Articles with This Topic / Article Content)

**Public (guest) access only:**

- [ ] Articles carry the Public Knowledge Base designation (`IsVisibleInPkb`) — the Customer channel does not reach guests
- [ ] Site's Guest User profile granted Knowledge object access (profile or permission set)
- [ ] Guest Data Category Visibility set explicitly on that profile or permission set — guests have no role, and the org-wide Default Data Category Visibility fallback is not a substitute
- [ ] Knowledge Settings > Share Article via URL configured with the hosting site
- [ ] Verified by loading an article URL in a logged-out private browser window (an Experience Builder preview runs as the admin and will not catch a missing guest permission)

---

## Publishing Workflow Decision

Select the appropriate workflow for this org:

- [ ] **Native statuses only** (Draft → Published → Archived; `PublishStatus` API values are `Draft` / `Online` / `Archived`) — appropriate for small teams with high author trust
- [ ] **Validation Status enabled** — adds quality signal picklist without blocking publish
  - Picklist values: (list planned values, e.g., "Draft", "Ready for Review", "Validated", "Not Validated")
- [ ] **Approval Process on Knowledge__kav** — blocking gate before publish
  - Approver role/user: ___
  - Entry criteria: ___
  - On approve: Field Update → Validation Status = ___
  - On reject: Notification to author + Field Update → Validation Status = ___

---

## Checklist

Work through items in order. Tick as complete.

- [ ] Stakeholders acknowledged Lightning Knowledge enablement is irreversible
- [ ] Record type taxonomy designed and approved before enabling in production
- [ ] Lightning Knowledge enabled in the target environment
- [ ] Record types created in Object Manager > Knowledge > Record Types
- [ ] Page layouts created and assigned to record types
- [ ] Record types assigned to appropriate author profiles
- [ ] Data Category Groups created within default limits (5 total, 3 active at a time)
- [ ] Category hierarchy built to reflect content taxonomy, then activated only after categories and visibility are final (an inactive group is hidden from users)
- [ ] Category visibility assigned to roles/profiles/permission sets for each audience segment; no child role expected to see a category its parent role lacks
- [ ] Guest User profile / permission set Data Category Visibility configured (if a public Knowledge surface exists)
- [ ] Channel matrix filled in and signed off by the external-content owner
- [ ] Experience Cloud exposure section completed (if any article leaves the org)
- [ ] Validation Status picklist enabled (if required)
- [ ] Approval Process created and activated on Knowledge__kav (if required)
- [ ] Pilot article created for each record type, assigned to appropriate category and topic
- [ ] Visibility verified by logging in as a test user from each audience segment
- [ ] Uncategorized article behavior understood (they stay visible but surface only under the No Filter category option; activating a group is what hides classified articles)
- [ ] Re-publish behavior tested (confirm previous published version archives immediately)
- [ ] Admin runbook documented with record type taxonomy and category structure

---

## Notes

Record any deviations from the standard pattern and their rationale:

(e.g., "Used Profile-based category visibility instead of Role-based for Partner tier because partner users share a role with other non-Knowledge users — override required at profile level")
