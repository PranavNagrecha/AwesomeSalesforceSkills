---
name: partner-community-requirements
description: "Use this skill to define and validate the requirements for a Salesforce Partner Relationship Management (PRM) implementation: deal registration flows, lead distribution models, partner tier hierarchies, MDF budget tracking, and co-marketing content entitlement. Trigger keywords: partner community requirements, PRM deal registration setup, channel partner portal requirements, lead distribution partner, partner tier management, MDF tracking, co-marketing entitlement. NOT for implementing the partner sharing model — use data/partner-data-access-patterns. NOT for building the portal in Experience Builder — use admin/experience-cloud-site-setup. More trigger keywords: partner portal design worksheet, partner tier licence and role depth, PartnerAccountId blank on opportunity, portal role Executive Manager User, sharing set does not support Lead, enable partner user greyed out, offboard a partner firm, PartnerMarketingBudget PartnerFundRequest PartnerFundClaim, ChannelProgramLevel partner tier, deal registration acceptance step."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "partner community requirements for deal registration and lead distribution"
  - "PRM deal registration setup with approval flow and opportunity conversion"
  - "channel partner portal requirements — tier management, MDF, co-marketing assets"
  - "lead distribution to partners using assignment rules"
  - "partner tier management Gold Silver Bronze feature access"
  - "partner community isn't working"
  - "partner account field is blank on the converted opportunity"
  - "enable partner user is greyed out on the contact"
  - "partner rep cannot see a deal owned by their colleague"
  - "how many portal roles can one partner account have"
  - "sharing set will not let me pick the lead object"
  - "offboard a partner firm without breaking their open pipeline"
  - "which licence do channel partners need — partner community or login"
  - "does salesforce have standard MDF objects or do we build custom"
tags:
  - partner-community
  - prm
  - deal-registration
  - lead-distribution
  - partner-tiers
  - mdf
  - co-marketing
  - experience-cloud
inputs:
  - "Number and types of partner tiers (e.g., Gold / Silver / Bronze)"
  - "Deal registration business rules — who can register, approval chain, duplicate prevention"
  - "Lead distribution criteria — geography, product line, partner tier, capacity"
  - "MDF budget allocation model — whether tracked in Salesforce or external system"
  - "Co-marketing asset entitlement rules per tier"
  - "Existing Experience Cloud org edition and license inventory"
outputs:
  - "PRM requirements document covering license model, tier hierarchy, deal registration flow, lead distribution rules"
  - "Partner tier decision matrix with feature access and MDF eligibility per tier"
  - "Deal registration approval workflow specification"
  - "Lead distribution assignment rule specification"
  - "Review checklist confirming configuration readiness before build"
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-05
---

# Partner Community Requirements

Use this skill when a project needs to define the functional and configuration requirements for a Salesforce PRM implementation built on Experience Cloud. It covers the full requirements surface: license selection, partner tier hierarchy, deal registration approval flow, lead distribution assignment rules, MDF budget tracking, and co-marketing content entitlement per tier.

---

## Before Starting

Gather this context before working on anything in this domain:

- Confirm whether the org has Partner Community or Partner Community Plus licenses. Customer Community licenses do not support deal registration or PRM features — this is the single most common scoping error.
- Establish the partner tier model upfront (names, count, promotion/demotion criteria). Tier drives sharing rules, feature access, MDF eligibility, and content entitlement — retrofitting tiers after build is expensive.
- Clarify whether deal registration is gated by a formal approval process and who approves (channel manager, regional VP, automated). Approval chain length directly affects flow design.
- Understand whether MDF budgets will live in Salesforce custom objects or in an external finance system. In-Salesforce tracking requires custom object design before PRM build begins.
- Determine the lead distribution model: push (Salesforce assigns leads to partners) vs. pull (partners claim leads from a pool). Each model uses different configuration primitives.

---

## Questions to Ask Before Configuring

Ask these before anything is written down. Each one closes a gotcha in `references/gotchas.md`, and
each answer becomes a row in the design artefact of `references/worked-examples.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which partner-portal licence is actually on the contract?" | `Account.IsPartner`, `Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` are documented as available only when PRM is enabled or digital experiences is enabled **and the org holds partner portal licences** (Object Reference, `Account.IsPartner`) | Whether the design may reference `PartnerAccountId` at all, and the licence line item per tier |
| "How many decision layers exist inside one partner firm?" | `UserRole.PortalRole` is a restricted picklist — `Executive`, `Manager`, `User`, `PersonAccount` — so a partner account stacks at most three roles | A role depth per tier instead of an invented role tree |
| "Which records must a partner see that they do not own — and is Lead one of them?" | The `SharingSet` `AccessMapping.object` list does not include Lead, so lead-pool visibility needs a different mechanism | One named mechanism per object, chosen from a documented set |
| "Is the Partner Account on a deal declared by the channel manager, or derived from who owns it?" | `Lead.PartnerAccountId` / `Opportunity.PartnerAccountId` are read-only and set from the owning partner user; making them writable is the org-wide `CommunitiesSettings.enableRelaxPartnerAccountFieldPref` switch | Whether the registration flow needs an ownership-transfer step, and whether an org pref changes |
| "Does fund tracking need per-claim audit, or just a number on the tier sheet?" | `PartnerMarketingBudget`, `PartnerFundAllocation`, `PartnerFundRequest` and `PartnerFundClaim` are standard objects from API v41.0 — a custom object model is a choice, not a necessity | A standard-vs-custom decision with a stated reason |
| "What happens the day a partner firm is terminated?" | Flipping `Account.IsPartner` from `true` to `false` disables up to 15 partner portal users and **permanently deletes** the account's partner portal roles and groups | The offboarding order: reassign, deactivate, then flag — never the reverse |
| "Must partner users inside one firm be invisible to each other?" | `SharingSettings.enablePortalUserVisibility` overrides org-wide defaults for same-account portal users, and enabling it requires a Salesforce Support case | A dated support case in the plan, or an explicit decision not to need one |

What a proper set of PRM requirements adds over just writing "we want a partner portal": every tier
has a licence it can actually be provisioned on, every object a partner can reach has one named
sharing mechanism that is capable of carrying it, deal attribution survives conversion because
ownership transfer is a designed step, and terminating a partner is a reversible sequence rather than
a one-way delete of their portal roles.

---

## Core Concepts

### License Requirements and What They Gate

PRM is delivered through the Partner Central Experience Cloud template.
**UNVERIFIED (2026-09-05):** the "Partner Central" template name does not appear in the Metadata API
Developer Guide, the Object Reference or the App Limits cheat sheet, and the `Network` metadata type
has no `template` field at all — so the template cannot be read from, or asserted by, a retrieved
package. Confirm it from the site's Experience Builder settings before relying on the name.

The documented licence keys for partner users are:

| `UserLicense.LicenseDefinitionKey` | Licence | Notes |
|---|---|---|
| `PID_Partner_Community` | Partner Community | Member-based. On the documented sharing-set licence list |
| `PID_Partner_Community_Login` | Partner Community Login | Login-based; 10 API calls per licence per 24 h vs 200 for member-based |
| `PID_STRATEGIC_PRM` | Gold Partner | Legacy PRM licence still enumerated by the API |
| `POWER_PRM` | Partner | Legacy PRM licence still enumerated by the API |

"Partner Community Plus" is named as a licence in the Apex Developer/Reference documentation but is
not among the `LicenseDefinitionKey` values above.
**UNVERIFIED (2026-09-05):** Partner Community Plus is named in the Apex Reference Guide (Login
Discovery availability) but appears in neither the Object Reference's `LicenseDefinitionKey` list nor
the `SharingSet` licence list in the Metadata API Guide. Confirm the entitlement on the org's Company
Information page before designing anything on it — in particular, do not assume it can use sharing sets.

What the licence actually gates is narrower and more concrete than "PRM features":

- `Account.IsPartner`, `Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` are each documented
  as available "if Partner Relationship Management is enabled or if digital experiences is enabled and
  you have partner portal licenses". Without a partner portal licence there is no partner account on a
  lead, so nothing downstream of `PartnerAccountId` exists to design.
- Sharing sets are documented as available with a licence list that includes Partner Community.
- `AccountBrand` (partner account branding) requires "a Partner Community or Customer Community Plus
  license".
- `ProcessDefinition` — the approval-process definition — is readable by "Portal and communities users
  with the Customer Community Plus and Partner Community licenses".

Partner users are Contacts on an Account with `IsPartner = true`. Set `User.ContactId`, not
`User.AccountId`: `AccountId` is read-only and derived from the Contact, and the Contact "must have a
value in the `AccountId` field or an error occurs".

`CommunitiesSettings.enableEnablePRM` ("allows admins to enable partner users", API v48.0+) is the
org switch underneath all of this. See `references/worked-examples.md` §4c for the settings XML.

### Deal Registration Flow: Lead → Approval → Opportunity

Deal registration in Partner Central follows a defined object lifecycle:

1. Partner submits a deal registration record (backed by the `Lead` object in standard PRM, or a custom object in some implementations).
2. The submitted Lead enters an approval process. The approval process routes to the channel manager or an automated queue based on criteria (territory, deal size, product).
3. **Ownership transfers to a named partner user** — this is the step most designs omit, and it is what makes attribution work.
4. On approval and acceptance, the Lead is converted to an Opportunity. `Opportunity.PartnerAccountId` then derives from the owning partner user; it is read-only and cannot be stamped by a Flow.
5. On rejection, the partner receives a notification and may resubmit with updated information.

`Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` carry the properties
`Filter, Group, Nillable, Sort` — no Create, no Update — and are documented as "ID of the partner
account for the partner user that **owns** this lead / opportunity… If the owner… isn't a partner
user, this field has no value." Making them editable is the org-wide
`CommunitiesSettings.enableRelaxPartnerAccountFieldPref` switch, not a field-level permission.

Key constraint: deal registration requires the Lead record to exist before conversion. You cannot register against an existing Opportunity directly in standard PRM. Any requirement to register deals that are already past the Lead stage requires a custom solution or the Channel Revenue Management product.

Duplicate prevention relies on Lead duplicate rules. These must be configured before launch — otherwise partners can register the same deal multiple times, creating channel conflict.

### Lead Distribution

Lead distribution delivers inbound or marketing-generated leads to qualified partners. There are two models:

- **Push (assignment rule-based):** Salesforce evaluates lead assignment rules on lead creation or reassignment. Rules match on criteria such as geography (state/country fields), product interest (lead source or product picklist), partner tier, and capacity (custom formula-based logic). The lead is assigned to a partner queue or directly to a partner user.
- **Pull (lead pool / lead inbox):** Leads are placed in a shared queue visible to eligible partners. Partners claim leads from the pool. Pull requires careful sharing rule design so that only eligible partners (by tier or territory) can see the pool.

Lead distribution does not function correctly without a defined partner tier and territory model. Criteria-based rules that reference partner tier require a lookup from the Lead to the partner Account tier field, which requires a cross-object formula or a trigger/flow to stamp tier on the lead at assignment time.

### Partner Tier Management

Partner tiers (commonly Gold / Silver / Bronze or Registered / Authorized / Premier) are the structural backbone of a PRM implementation. Tier drives:

- **Feature access:** Gold partners may have access to deal registration and the lead pool; Bronze partners may only have access to co-marketing assets.
- **Fund eligibility:** Higher tiers receive larger marketing-fund allocations, tracked on the standard `PartnerMarketingBudget` / `PartnerFundAllocation` objects or on custom equivalents.
- **Co-marketing content entitlement:** Content visibility in the portal is controlled by sharing rules scoped to a tier-based public group or a record-level share. Profile or permission set alone is insufficient because content entitlement varies within the same license type.
- **Approval routing:** Approval processes can route differently based on tier — Gold deals may auto-approve below a threshold while Silver deals always require manual review.

Tier has two documented homes, and the choice is a decision to record rather than a default:

- **Standard:** `ChannelProgram` ("a channel program that vendors use to market and sell their
  products through channel partners"), `ChannelProgramLevel` ("a level, based on member experience,
  in a channel program") and `ChannelProgramMember.LevelId` — all available from API v41.0.
- **Custom:** a picklist on the partner Account, referenced by assignment rules, sharing rules,
  approval criteria and content entitlement. Simpler to report on and easier to use in rule criteria.

Tier is **not** the same thing as role depth. Roles inside a partner firm come from
`UserRole.PortalRole`, a restricted picklist with exactly `Executive`, `Manager`, `User`,
`PersonAccount` — so at most three stacked levels per partner account, regardless of how many tiers
the programme has.

### MDF and Co-Marketing

Market Development Funds (MDF) are budget allocations made to partners to fund co-marketing
activities. Salesforce ships standard objects for the budget → allocation → request → claim chain,
all available from API version 41.0:

| Object | What the Object Reference says it represents |
|---|---|
| `PartnerMarketingBudget` | "a budget that provides funds to channel partners for selling and marketing products and services" |
| `PartnerFundAllocation` | "allocated funds from a partner marketing budget for channel partners" |
| `PartnerFundRequest` | "a request for funds from the partner marketing budget by a channel partner" |
| `PartnerFundClaim` | "a claim of funds from the partner marketing budget by a channel partner" |

Start there. A custom `MDF_Budget__c` / `MDF_Request__c` / `MDF_Claim__c` model is a legitimate
choice — the standard objects have a fixed field set and one hard reporting limitation (see below) —
but it is a decision that needs a written reason, not the default.

The limitation to check first: "The `ChannelPartnerId` field isn't supported for formula fields,
custom buttons, or custom links for the `PartnerFundAllocation` object. This limitation also applies
to the `PartnerMarketingBudget` and `PartnerFundRequest` objects." Any fund requirement phrased as a
formula that pulls partner attributes onto the claim is unbuildable as written on the standard objects.

Co-marketing assets (templates, brand assets, campaign collateral) are surfaced in the portal via CMS Content or Salesforce Files with sharing rules based on partner tier. Content entitlement rules must be defined before the portal build begins.

---

## Common Patterns

### Pattern 1: Multi-Tier Deal Registration with Differential Approval Routing

**When to use:** The org has 3+ partner tiers with different deal registration privileges (e.g., Gold auto-approves deals under $50K; Silver always goes to manual review).

**How it works:**
1. Store partner tier as a picklist on the partner Account (`Tier__c`).
2. Create a custom `Partner_Account__c` lookup on Lead and a cross-object formula `Partner_Tier__c = Partner_Account__r.Tier__c`. Do not build the formula off the standard `PartnerAccountId` — it is a read-only derived field, not a designed lookup for your own formulas.
3. Build an approval process on Lead with entry criteria `Status = Submitted for Registration`.
4. Add approval steps: Step 1 checks `Partner_Tier__c = Gold AND Amount < 50000` and routes to auto-approve; Step 2 routes all other leads to channel manager queue.
5. On final approval, transfer Lead ownership to the accepting partner user, **then** convert. `Opportunity.PartnerAccountId` derives from the new owner; a Flow cannot write it.
6. On rejection, a Flow sends a notification to the submitting partner user with rejection reason.

**Why not the alternative:** A single-step approval process with no tier differentiation creates a manual review bottleneck for high-volume Gold partners and degrades partner experience. Auto-approval criteria require the tier field to exist on the Lead at approval time — which requires the formula field in step 2.

### Pattern 2: Criteria-Based Lead Distribution to Partner Queue

**When to use:** The org distributes inbound leads to partners based on geography and product interest and wants assignments to respect partner tier eligibility.

**How it works:**
1. Define partner tier eligibility for lead distribution (e.g., only Gold and Silver partners receive distributed leads).
2. Create a partner queue for each tier-territory combination (e.g., `Gold_West_Queue`, `Silver_East_Queue`). Keep queue count manageable — excessive queues become an administrative burden.
3. Build Lead assignment rules with criteria ordered by specificity: state match + product interest + tier eligibility.
4. Stamp the matched partner queue on the Lead Owner field.
5. Configure portal Lead list views scoped to the partner user's queue membership so partners only see their assigned leads.
6. If pull model is required, expose a shared Lead list view for the eligible tier group (use a public group share on the Lead record rather than a queue).

**Why not the alternative:** Assigning leads directly to partner user records (rather than queues) breaks when partner users are inactive or at capacity. Queue-based assignment provides an auditable routing layer and allows partner admins to manage queue membership without reconfiguring assignment rules.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Partner needs deal registration and lead distribution | Partner Community (member) or Partner Community Login | `Account.IsPartner` and `PartnerAccountId` are documented as requiring partner portal licences |
| Partner logs in a handful of times a year | Partner Community Login | 10 API calls per licence per 24 h vs 200 for member-based — sized for occasional use |
| Partner users must run reports in the portal | `CommunitiesSettings.enableNetPortalUserReportOpts` plus the report permission | The guide describes external-user reporting as an org preference "with permission", not a licence tier |
| Deal registration volume is high and most Gold deals auto-qualify | Criteria-based auto-approval for top tier, manual for others | Reduces channel manager workload while preserving governance on mid-market deals |
| Leads should be claimed by partners, not pushed automatically | Pull model with shared queue and tier-scoped list view | Push assignment requires capacity logic that is expensive to maintain; pull gives partners agency while respecting tier eligibility |
| MDF tracking must be auditable and tied to campaign outcomes | Standard `PartnerMarketingBudget` / `PartnerFundAllocation` / `PartnerFundRequest` / `PartnerFundClaim` first | They ship from API v41.0; build custom only when the fixed field set or the `ChannelPartnerId` formula restriction blocks a stated requirement |
| Partner needs visibility of records that hang off a *related* account, not their own | `AccountRelationshipShareRule` | Its documented `EntityType` list covers Account, Campaign, Case, Contact, Lead, Order and the four partner fund objects — including the Lead a sharing set cannot reach |
| Co-marketing assets should only be visible to Gold partners | Sharing rules on CMS Content or Files tied to Gold public group | Profile-only visibility does not vary within a license type; sharing rules are required |

---

## Recommended Workflow

1. **Licence and switch audit** — Query `UserLicense` for the org's actual partner keys
   (`PID_Partner_Community`, `PID_Partner_Community_Login`, and the legacy `PID_STRATEGIC_PRM` /
   `POWER_PRM`). Retrieve `Settings` members `Communities` and `Sharing` and read
   `enableEnablePRM`, `enablePRMAccRelPref`, `enableRelaxPartnerAccountFieldPref`,
   `enableAccountRoleOptimization`, `enablePartnerSuperUserAccess` and `enablePortalUserVisibility`.
   These six flags decide what the rest of the design is allowed to assume — the XML and the
   guide quotations are in `references/worked-examples.md` §4c.

2. **Fill the tier / licence worksheet and the role plan** — Copy §1 and §2 of
   `references/worked-examples.md`. Every tier gets a licence and a role depth of 1–3, because
   `UserRole.PortalRole` is a four-value restricted picklist. Decide tier storage here: standard
   `ChannelProgramLevel` or a custom Account picklist, with the reason written down.

3. **Write the partner-portal design YAML** — Use the artefact in §3 of
   `references/worked-examples.md`. List **every** object a partner can reach, including the ones
   set to `not-exposed`, each with one sharing mechanism from the documented set. The
   deal-registration block must include an `acceptance` step and a `duplicate_check` step;
   offboarding must include `reassign_records` and `deactivate_user`.

4. **Run the checker** —
   `python3 scripts/check_partner_community_requirements.py --file partner-portal-design.yaml`.
   It fails the design when a tier has no licence or an impossible role depth, when an object is
   handed to a mechanism that cannot carry it (a sharing set on Lead), when a row has no owner,
   or when the registration and offboarding flows are incomplete. Point `--manifest-dir` at a
   retrieved package to parse `networks/*.network-meta.xml` and `sharingSets/*.sharingSet-meta.xml`
   against the guide's field tables at the same time.

5. **Write the acceptance SOQL before the build starts** — §9 of `references/worked-examples.md`
   has the six queries. A3 and A4 (null `PartnerAccountId` on approved registrations and open
   partner-owned opportunities) are the ones that catch the attribution failure this domain is
   prone to; A6 catches an offboarding leak. Hand them to the build team as the UAT pack.

6. **Read `references/gotchas.md` end to end, then hand off** — Confirm each of the eleven
   behaviours is either designed for or explicitly out of scope. Route the artefacts using the
   handoff table in §10 of `references/worked-examples.md`; this skill stops at the specification.

---

## Review Checklist

Run through these before marking requirements work complete:

- [ ] Partner licence keys confirmed against `UserLicense` in the target org — not assumed from the contract
- [ ] Role depth per tier set to 1–3 against the `UserRole.PortalRole` picklist
- [ ] Partner tier hierarchy documented with tier names, promotion criteria, and feature access matrix
- [ ] Deal registration object model selected (Lead-based standard PRM or custom object)
- [ ] Approval chain fully mapped per tier including auto-approval thresholds and rejection flow
- [ ] Lead duplicate rules defined to prevent multi-registration of the same deal
- [ ] Lead distribution model selected (push or pull) with assignment rule criteria documented
- [ ] Queue structure defined for push model OR shared pool sharing model defined for pull model
- [ ] Fund tracking decided: standard partner fund objects, custom objects with a stated reason, or external
- [ ] Ownership-transfer step present in the registration flow so `PartnerAccountId` is populated
- [ ] Offboarding sequence documented: reassign, deactivate, then (only on termination) clear `IsPartner`
- [ ] `partner-portal-design.yaml` written and `scripts/check_partner_community_requirements.py` exits 0
- [ ] Co-marketing asset entitlement rules defined per tier
- [ ] Sharing rule model documented — profile/permission set vs. sharing rule distinction confirmed
- [ ] Open decisions logged with owner and target resolution date

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Deal registration requires Lead before Opportunity** — Standard PRM deal registration is built on the Lead object. Partners submit a Lead record which is converted to an Opportunity on approval. You cannot register a deal against an existing Opportunity in standard PRM. If the business requires registration of deals already past the Lead stage (e.g., partner-identified opportunities already in the pipeline), a custom solution or the Channel Revenue Management product is required. Attempting to work around this with a custom field on Opportunity breaks the standard conversion flow and audit trail.

2. **Tier-based visibility requires sharing rules, not just profiles** — All partner users in a tier share the same license type. Profile and permission set alone cannot vary content or record visibility within a tier. Sharing rules scoped to a tier-based public group are required for co-marketing asset entitlement, lead pool visibility, and MDF record access. Administrators who rely only on profiles to control tier-differentiated access will find that all partners see all content.

3. **Standard partner fund objects exist, and `ChannelPartnerId` is not formula-usable** — `PartnerMarketingBudget`, `PartnerFundAllocation`, `PartnerFundRequest` and `PartnerFundClaim` have shipped since API v41.0, so a requirements document that assumes a custom MDF build is skipping an evaluation. The trap on the standard path is different: `ChannelPartnerId` is documented as unsupported for formula fields, custom buttons and custom links across all three of budget, allocation and request.

4. **Lead assignment rules do not natively reference partner tier** — Assignment rules evaluate fields on the Lead record; partner tier lives on the partner Account. Route by tier and you need a custom lookup plus a cross-object formula, or a Flow that stamps the value. The standard `PartnerAccountId` is not the field to build that on: it is read-only and only populated once a partner user owns the record, which is after assignment, not before it.

5. **Partner user creation requires Partner Account checkbox** — A Contact cannot be enabled as a partner Experience Cloud user unless the parent Account has `IsPartner = true`. If Accounts are created in bulk without this flag, partner user provisioning fails silently or produces a generic error. Bulk partner onboarding scripts must set the flag before user creation.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| PRM requirements document | Full written specification covering license model, tier hierarchy, deal registration flow, lead distribution rules, MDF model, and co-marketing entitlement |
| Partner tier decision matrix | Table mapping each tier to its feature access, MDF eligibility, lead pool access, and co-marketing content categories |
| Deal registration flow diagram | Lead → Approval → Opportunity conversion path with approval routing criteria per tier |
| Lead distribution rule specification | Assignment rule criteria table (push model) or shared pool sharing model (pull model) |
| MDF custom object data model | Entity definitions for MDF Budget, Request, and Claim with field list and approval process notes |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/worked-examples.md` | You are producing the actual artefacts — tier worksheet, role plan, design YAML, Network/SharingSet/Settings XML, onboarding and offboarding runbooks, acceptance SOQL |
| `references/gotchas.md` | Before signing off a design, and when a partner-portal behaviour is not what the requirements assumed |
| `references/examples.md` | You want two end-to-end scenarios (multi-tier deal registration; push/pull lead distribution) with the reasoning behind each choice |
| `references/llm-anti-patterns.md` | You are reviewing PRM requirements an AI assistant produced, or about to generate some |
| `references/well-architected.md` | You need the pillar framing, the licence and MDF trade-offs, and the source list behind the platform claims |
| `templates/partner-community-requirements-template.md` | You are running the requirements workshop and want the blank worksheet to fill in live |
| `scripts/check_partner_community_requirements.py` | After writing the design YAML, and again after retrieving partner metadata from the org |

---

## Related Skills

- `admin/portal-requirements-gathering` — run first: persona/licence matrix and access architecture for any portal, partner or customer
- `admin/experience-cloud-site-setup` — receives the design artefact and builds the site (Network, CustomSite, template selection)
- `admin/experience-cloud-guest-access` — use to confirm the partner site exposes no public pages, and to design any that must be
- `admin/sharing-and-visibility` — owns the OWD, sharing set and sharing rule layer this skill's design YAML points at
- `admin/lead-management-and-conversion` — owns the conversion field mapping and lead process behind the registration flow
- `admin/opportunity-management` — owns stage, forecast category and the opportunity side of partner attribution
- `admin/role-hierarchy-design` — creates the per-partner-account portal roles this skill plans the depth of
- `admin/duplicate-management` — builds the Lead duplicate rule the deal-registration flow depends on
- `data/partner-data-access-patterns` — implements the partner data access model once this skill has specified it
- `security/experience-cloud-security` — hardens the portal after the sharing model is agreed
- `architect/license-optimization-strategy` — prices member vs login partner licences against the tier worksheet
