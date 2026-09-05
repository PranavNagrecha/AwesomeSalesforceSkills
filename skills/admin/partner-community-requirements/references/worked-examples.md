# Worked Examples — Partner Community Requirements

One channel-partner portal, worked from the tier sheet to the acceptance SOQL. Every block below
is copy-and-adapt shaped: the tier / licence worksheet, the per-partner-account role plan, the
partner-portal design YAML that `scripts/check_partner_community_requirements.py` lints, the
deal-registration and lead-distribution flow, the visibility model with the XML each mechanism
deploys as, the onboarding and offboarding runbooks, and the acceptance queries.

**Scenario.** Acme Cloud sells subscription software direct today. It is adding a channel: 60
reseller firms in three tiers, who must register deals, receive or claim marketing leads, see the
opportunities their own people own, and pull co-marketing assets. Acme already runs an Experience
Cloud customer support site; this is a second site for partners.

This page assumes `admin/portal-requirements-gathering` has already produced the persona / licence
matrix and access-architecture decision. It does not repeat them. It also does not author the site
itself — that is `admin/experience-cloud-site-setup` — nor the OWD and sharing-rule layer, which is
`admin/sharing-and-visibility`.

---

## 1. Tier and licence worksheet

| Tier | Partner firms | What they do in the portal | Licence | Login pattern | API allocation per licence / 24 h (EE, PE with API) |
|---|---|---|---|---|---|
| Platinum | 8 | Register deals, own opportunities, claim funds, run reports | Partner Community | Member — daily | `Partner Community: 200` |
| Gold | 22 | Register deals, claim leads from a regional pool, download assets | Partner Community | Member — weekly | `Partner Community: 200` |
| Referral | 30 | Submit a referral form, download brand assets. No pipeline. | Partner Community Login | Login — a handful of logins a year | `Partner Community Login: 10` |

Grounded in the *Salesforce Developer Limits and Allocations Quick Reference* ("Total API Request
Allocations", L546–L547 for Enterprise / Professional with API enabled, L584–L585 for Unlimited /
Performance). The org total on the same table is
`100,000 + (number of licenses x calls per license type) + purchased API Call Add-Ons`.

Three facts settle the licence column before any commercial conversation:

- `Account.IsPartner`, `Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` are all documented
  as available "if Partner Relationship Management is enabled or if digital experiences is enabled
  and you have partner portal licenses" (*Object Reference*, `Account.IsPartner` L13098–L13101,
  `Lead.PartnerAccountId` L163748–L163752, `Opportunity.PartnerAccountId` L192804–L192807). A
  customer-community licence does not put a partner account on a lead, so nothing downstream of
  `PartnerAccountId` can be designed on one.
- The documented licence keys are `PID_Partner_Community` → Partner Community and
  `PID_Partner_Community_Login` → Partner Community Login (*Object Reference*,
  `UserLicense.LicenseDefinitionKey`, L299583–L299585). Two older PRM keys still appear on the same
  list: `PID_STRATEGIC_PRM` → Gold Partner and `POWER_PRM` → Partner (L299569, L299604). Check which
  the org actually holds before assuming the modern pair.
- Sharing sets are documented as available with a licence list that includes Partner Community
  (*Metadata API Guide*, `SharingSet` § Special Access Rules, L130391–L130400). If a tier lands on a
  licence outside that list, the sharing-set rows in §4 are not available to it.

> **UNVERIFIED (2026-09-05):** "Partner Community Plus" is named as a licence in the Apex Reference
> Guide (L4398–L4399 and L9887–L9888, Login Discovery availability) but does **not** appear as a
> `LicenseDefinitionKey` in the Object Reference list at L299560–L299604, and is not in the
> `SharingSet` licence list at api_meta.txt L130391–L130400. The checker accepts the name because the
> Apex guide uses it; confirm the entitlement — and whether it can use sharing sets — against the
> org's Company Information page rather than from these guides. This worksheet does not use it.

---

## 2. Role plan per partner account

`UserRole.PortalRole` is a **restricted picklist** whose values are `Executive`, `Manager`, `User`,
`PersonAccount` (*Object Reference*, `UserRole.PortalRole` L303483–L303489; the same four values
appear as the `PortalRoles` enumeration on `Portal.selfRegUserDefaultRole`, *Metadata API Guide*
L96649–L96656). So the hierarchy inside one partner firm is at most three levels deep, and you
choose the depth per tier rather than designing a role tree.

| Tier | Roles created per partner account | Who sits where | Why that depth |
|---|---|---|---|
| Platinum | Executive → Manager → User | Channel exec sees the firm's whole pipeline; regional managers see their reps | Roll-up reporting is a Platinum entitlement |
| Gold | Manager → User | Principal sees the firm's deals; reps see their own | No third layer to roll up to |
| Referral | User only | Everyone sees only what they submitted | A referral firm has no internal hierarchy worth modelling |

Two behaviours to design around, both documented:

- `User.PortalRole` is nillable, and "when you set this field to null, a portal role is not
  automatically created. When this field is null and a `ContactId` is provided, the user is assigned
  to the User role" (*Object Reference*, L303484–L303489 / `User.PortalRole` L295663–L295680). A bulk
  onboarding load that omits `PortalRole` therefore lands every partner user at the bottom, silently.
- `SharingSettings.enableAccountRoleOptimization` "Indicates whether person roles are assigned to new
  site users in accounts without existing users (`true`) or if regular site roles are created for new
  users (`false`). This field has a default value of `false`" (*Metadata API Guide*, L127042–L127045).
  Flipping it changes what a newly enabled partner user gets, so it is an org-level decision that
  belongs in this worksheet and not in a build ticket.

---

## 3. The design artefact

This is the file the checker lints. Save it as `partner-portal-design.yaml` next to the requirements
document, and run:

```bash
python3 skills/admin/partner-community-requirements/scripts/check_partner_community_requirements.py \
  --file partner-portal-design.yaml
```

```yaml
partner_portal:
  name: Acme Channel Portal
  site_url_path_prefix: partners
  licence_model: mixed member and login
  requirements_owner: Priya N (Channel Ops)

tiers:
  - id: platinum
    name: Platinum
    licence: Partner Community
    role_depth: 3
    deal_registration: yes
    lead_distribution: push
    fund_requests: yes
    owner: Priya N (Channel Ops)
  - id: gold
    name: Gold
    licence: Partner Community
    role_depth: 2
    deal_registration: yes
    lead_distribution: pull
    fund_requests: yes
    owner: Priya N (Channel Ops)
  - id: referral
    name: Referral
    licence: Partner Community Login
    role_depth: 1
    deal_registration: no
    lead_distribution: none
    fund_requests: no
    owner: Priya N (Channel Ops)

exposed_objects:
  - object: Opportunity
    why: A partner rep must see deals owned by their colleagues in the same firm
    sharing_mechanism: partner-account-role-hierarchy
    external_owd: Private
    built_by: skills/admin/sharing-and-visibility
    owner: Dev Patel (Platform)
  - object: Lead
    why: Gold partners claim marketing leads from a regional pool
    sharing_mechanism: account-relationship-share-rule
    external_owd: Private
    note: Sharing sets cannot target Lead; see gotcha 8
    built_by: skills/admin/sharing-and-visibility
    owner: Dev Patel (Platform)
  - object: Account
    why: A partner user must read their own firm's account record
    sharing_mechanism: sharing-set
    external_owd: Private
    built_by: skills/admin/sharing-and-visibility
    owner: Dev Patel (Platform)
  - object: Case
    why: Partners raise and track their own support cases
    sharing_mechanism: sharing-set
    external_owd: Private
    built_by: skills/admin/sharing-and-visibility
    owner: Dev Patel (Platform)
  - object: PartnerFundRequest
    why: Platinum and Gold partners submit and track marketing fund requests
    sharing_mechanism: account-relationship-share-rule
    external_owd: Private
    built_by: skills/admin/sharing-and-visibility
    owner: Dev Patel (Platform)
  - object: Contract
    why: Contracts stay internal for legal review
    sharing_mechanism: not-exposed
    external_owd: Private
    built_by: n/a
    owner: Sam Ord (Legal Ops)

deal_registration:
  object: Lead
  expiry_days: 90
  steps:
    - id: dr-1
      name: Partner submits registration
      type: submission
      detail: Screen flow on the partner site sets Status = Submitted for Registration
      owner: Priya N (Channel Ops)
    - id: dr-2
      name: Block a prospect another partner already registered
      type: duplicate_check
      detail: Lead duplicate rule matching Company + Email, action Block
      built_by: skills/admin/duplicate-management
      owner: Priya N (Channel Ops)
    - id: dr-3
      name: Channel manager approves
      type: approval
      detail: Approval process on Lead routed to Channel_Manager_Queue, never to a named user
      owner: Priya N (Channel Ops)
    - id: dr-4
      name: Named partner rep accepts the registration
      type: acceptance
      detail: Lead ownership transfers to the accepting partner user, which is what sets PartnerAccountId
      owner: Priya N (Channel Ops)
    - id: dr-5
      name: Convert to Opportunity
      type: conversion
      detail: Convert with the accepting partner user as owner so Opportunity.PartnerAccountId derives
      built_by: skills/admin/lead-management-and-conversion
      owner: Dev Patel (Platform)
    - id: dr-6
      name: Rejection notice and resubmission window
      type: rejection
      detail: Email alert plus a 14-day resubmission window before the record is archived
      owner: Priya N (Channel Ops)

offboarding:
  trigger: Partner agreement terminated or a partner employee leaves
  steps:
    - id: off-1
      name: Reassign open pipeline
      action: reassign_records
      detail: Transfer open Leads and Opportunities to the channel manager before anything else
      owner: Priya N (Channel Ops)
    - id: off-2
      name: Deactivate the partner user
      action: deactivate_user
      detail: Set User.IsActive = false; a partner user cannot be deleted
      owner: Dev Patel (Platform)
    - id: off-3
      name: Remove public group and queue membership
      action: remove_group_membership
      detail: Drop the user from tier public groups and lead-pool queues
      owner: Dev Patel (Platform)
    - id: off-4
      name: Archive co-marketing content access
      action: archive_content
      detail: Remove the firm from the content library share
      owner: Marketing Ops
    - id: off-5
      name: Clear the partner flag, last, and only on full termination
      action: clear_partner_flag
      detail: Setting Account.IsPartner true to false permanently deletes the account's portal roles and groups
      owner: Priya N (Channel Ops)
```

Deliberate shapes in that file, each of which the checker enforces:

- **Every tier names a licence and a role depth.** A tier with no licence is an unpriced commitment;
  a tier with `role_depth: 4` is impossible against the `PortalRole` picklist.
- **`Lead` is not on a `sharing-set` row.** The `SharingSet` `AccessMapping.object` list in the
  Metadata API Guide (L130443–L130452) is Account, Campaign, Contact, Case, custom objects,
  Opportunity, Order, ServiceContract, User, WorkOrder. Lead is not on it. The checker rejects a
  design that tries.
- **`Contract` appears with `not-exposed`.** An object that is deliberately closed is still a row.
  A design that lists only the exposed objects cannot be reviewed for what it left out.
- **The deal-registration flow has both an acceptance step and a duplicate check.** Acceptance is
  what makes `PartnerAccountId` correct (§5); the duplicate check is what stops two partners
  registering the same prospect.
- **Offboarding reassigns before it deactivates.**

---

## 4. The visibility model, and the XML each row deploys as

### 4a. Account access — sharing set

Shaped from the guide's own sample (*Metadata API Guide*, `SharingSet` § Declarative Metadata Sample
Definition, L130475–L130520), extended to the partner case.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharingSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <name>Partner_Account_And_Cases</name>
    <description>Partner users read their own firm's Account and edit its Cases.</description>
    <profiles>Acme Partner Community User</profiles>
    <accessMappings>
        <accessLevel>Read</accessLevel>
        <objectField>Id</objectField>
        <object>Account</object>
        <userField>Account</userField>
    </accessMappings>
    <accessMappings>
        <accessLevel>Edit</accessLevel>
        <objectField>AccountId</objectField>
        <object>Case</object>
        <userField>Account</userField>
    </accessMappings>
</SharingSet>
```

How to read it:

- `name` is required and is the API identifier; `description` is capped at 255 characters
  (L130424–L130432).
- `profiles` is a list of profiles "associated with a license that can use sharing sets"
  (L130430–L130432). The `SharingSet` `<profiles>` element repeats — one per profile.
- `userField` walks from the running user to an Account or Contact. Valid values are `Account`,
  `Account.Field`, `Contact`, `Contact.Field`, `Contact.RelatedAccount`, `Manager.Account`,
  `Manager.Contact` (L130455–L130466). `objectField` is the target object's lookup back.
- `accessLevel` is `Read` or `Edit` only (L130436–L130440). There is no Full Access on a sharing set.

### 4b. Site-level partner settings — Network

Every element below is from the `Network` field table (*Metadata API Guide*, L90671–L91050).

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Network xmlns="http://soap.sforce.com/2006/04/metadata">
    <allowInternalUserLogin>true</allowInternalUserLogin>
    <communityRoles>
        <partnerUserRole>Channel Partner</partnerUserRole>
        <customerUserRole>Customer</customerUserRole>
        <employeeUserRole>Acme Employee</employeeUserRole>
    </communityRoles>
    <description>Acme Channel Portal</description>
    <emailSenderAddress>channel@acme.example.com</emailSenderAddress>
    <emailSenderName>Acme Channel Team</emailSenderName>
    <enableGuestChatter>false</enableGuestChatter>
    <enableGuestFileAccess>false</enableGuestFileAccess>
    <enableMemberVisibility>false</enableMemberVisibility>
    <forgotPasswordTemplate>unfiled$public/CommunityForgotPasswordEmailTemplate</forgotPasswordTemplate>
    <networkMemberGroups>
        <permissionSet>Acme_Partner_Deal_Registration</permissionSet>
        <profile>Acme Partner Community User</profile>
        <profile>Acme Partner Community Login User</profile>
    </networkMemberGroups>
    <selfRegistration>false</selfRegistration>
    <site>Acme_Channel_Portal</site>
    <status>UnderConstruction</status>
    <tabs>
        <defaultTab>home</defaultTab>
        <standardTab>Lead</standardTab>
        <standardTab>Opportunity</standardTab>
    </tabs>
    <urlPathPrefix>partners</urlPathPrefix>
</Network>
```

How to read it:

- `emailSenderAddress`, `emailSenderName`, `forgotPasswordTemplate`, `site`, `status` and `tabs` are
  the fields the guide marks **Required**.
- `emailSenderAddress` can be set "only when you deploy `Network` for the first time to create a new
  Experience Cloud site… You can't update this field via Metadata API. If you attempt to update this
  field via Metadata API, your changes are ignored and Salesforce doesn't show an error"
  (L90782–L90800). A redeploy that changes it fails silently.
- `status` values are `Live`, `DownForMaintenance`, `UnderConstruction`, and the guide notes that
  after a site is published it "can never be in [`UnderConstruction`] status again"
  (L91020–L91040). Ship the first deploy as `UnderConstruction`.
- `communityRoles` sets the **labels** for Customer, Partner and Employee roles in the site
  (L91153–L91161). It does not create `UserRole` records — those are the portal roles of §2.
- `networkMemberGroups` is what actually makes a profile or permission set a member of the site
  (L90963–L90973, `NetworkMemberGroup` L91430–L91443).
- There is no `template` element on `Network`. The site template is not readable from this file.

### 4c. The org switches this design depends on

`CommunitiesSettings` (*Metadata API Guide*, L112766–L112900) and `SharingSettings`
(L126985–L127160) both deploy as `Settings` members.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CommunitiesSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableEnablePRM>true</enableEnablePRM>
    <enablePRMAccRelPref>true</enablePRMAccRelPref>
    <enableRelaxPartnerAccountFieldPref>false</enableRelaxPartnerAccountFieldPref>
    <enableNetPortalUserReportOpts>true</enableNetPortalUserReportOpts>
</CommunitiesSettings>
```

| Element | What the guide says it does | Why this design sets it |
|---|---|---|
| `enableEnablePRM` | "allows admins to enable partner users" (API v48.0+) | Nothing partner-shaped works without it |
| `enablePRMAccRelPref` | "enables Account Relationship object and Account Relationship Data Sharing Rule setup options" (v48.0+) | The Lead and PartnerFundRequest rows in §3 use `AccountRelationshipShareRule` |
| `enableRelaxPartnerAccountFieldPref` | "allows editing for partner account fields on and opportunities and leads" (v48.0+) | Left `false` on purpose — see §5 |
| `enableNetPortalUserReportOpts` | "allows external users in Experience Cloud sites, with permission, to run reports" (v48.0+) | Platinum reporting is an org pref plus a permission, not a licence tier |

```xml
<?xml version="1.0" encoding="UTF-8"?>
<SharingSettings xmlns="http://soap.sforce.com/2006/04/metadata">
    <enableExternalSharingModel>true</enableExternalSharingModel>
    <enableAccountRoleOptimization>false</enableAccountRoleOptimization>
    <enablePartnerSuperUserAccess>true</enablePartnerSuperUserAccess>
    <enablePortalUserVisibility>false</enablePortalUserVisibility>
</SharingSettings>
```

`enablePartnerSuperUserAccess` "Indicates whether you can grant super user access to partners in
sites… To use this field, you need the Customize Application permission" (L127077–L127080).
`enablePortalUserVisibility` lets portal users in the same partner account see each other regardless
of org-wide defaults, and "To enable this field, contact Salesforce Support" (L127085–L127089) — so
if a tier needs it, the support case is a dated line in the plan, not a Setup click.

### 4d. The partner permission set

```xml
<?xml version="1.0" encoding="UTF-8"?>
<PermissionSet xmlns="http://soap.sforce.com/2006/04/metadata">
    <label>Acme Partner Deal Registration</label>
    <description>Deal registration and pipeline access for Platinum and Gold partner users.</description>
    <license>Partner Community</license>
    <hasActivationRequired>false</hasActivationRequired>
    <objectPermissions>
        <object>Lead</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>Opportunity</object>
        <allowCreate>false</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
    <objectPermissions>
        <object>PartnerFundRequest</object>
        <allowCreate>true</allowCreate>
        <allowRead>true</allowRead>
        <allowEdit>true</allowEdit>
        <allowDelete>false</allowDelete>
        <viewAllRecords>false</viewAllRecords>
        <modifyAllRecords>false</modifyAllRecords>
    </objectPermissions>
</PermissionSet>
```

`license` is "Either the related permission set license or the user license associated with this
permission set… Use this field instead of `userLicense`, which is deprecated and only available up to
API Version 37.0" (*Metadata API Guide*, `PermissionSet` L94828–L94834). A permission set stamped
with a partner licence cannot then be assigned to an internal user, which is exactly the guardrail a
channel programme wants. Where the org uses a custom permission set licence instead, the categories
`${partnerCommunity}` and `${partnerCommunityLogin}` are the documented restriction values
(`userLicenseRestrictions`, L95470–L95482).

### 4e. package.xml and the commands

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Acme_Channel_Portal</members>
        <name>Network</name>
    </types>
    <types>
        <members>Partner_Account_And_Cases</members>
        <name>SharingSet</name>
    </types>
    <types>
        <members>Acme_Partner_Deal_Registration</members>
        <name>PermissionSet</name>
    </types>
    <types>
        <members>Communities</members>
        <members>Sharing</members>
        <name>Settings</name>
    </types>
    <version>62.0</version>
</Package>
```

```bash
# Pull what the org already has, so the design is written against reality
sf project retrieve start --manifest package.xml --target-org acme-partial

# Lint the design and the retrieved metadata together
python3 skills/admin/partner-community-requirements/scripts/check_partner_community_requirements.py \
  --file partner-portal-design.yaml \
  --manifest-dir force-app/main/default

# Validate without deploying
sf project deploy start --manifest package.xml --target-org acme-partial --dry-run
```

---

## 5. Why the acceptance step exists

`Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` are both documented as **read-only**
(`Filter, Group, Nillable, Sort` — no Create, no Update) and as "ID of the partner account for the
partner user that **owns** this lead / opportunity… If the owner… isn't a partner user, this field
has no value" (*Object Reference*, L163743–L163757 and L192799–L192814).

Three consequences the requirements document must state:

1. **The partner account is a side effect of ownership.** A registration approved but left owned by
   the channel manager produces an opportunity with an empty `PartnerAccountId`. Channel reporting
   then under-counts partner-sourced revenue and nobody notices for a quarter. Step `dr-4` in §3
   exists to force the transfer.
2. **Making the field writable is an org-wide switch, not a field-level one.**
   `CommunitiesSettings.enableRelaxPartnerAccountFieldPref` "allows editing for partner account
   fields on and opportunities and leads" (*Metadata API Guide*, L112870–L112873). This design leaves
   it `false` so the field stays a derived fact; a programme that lets a channel manager attribute a
   deal to a partner who does not own it must turn it on deliberately and say so.
3. **`Lead.PartnerAccountId` is on the documented criteria list for account-relationship sharing.**
   `AccountRelationshipShareRule.AccountToCriteriaField` includes `Lead.PartnerAccountId` and
   `Opportunity.PartnerAccountId`, and its `EntityType` covers Account, Campaign, Case, Contact,
   **Lead**, Order, `PartnerFundAllocation`, `PartnerFundClaim`, `PartnerFundRequest`,
   `PartnerMarketingBudget` (*Object Reference*, L17416–L17560). That is the mechanism the Lead row
   in §3 points at, and the reason it is not a sharing set.

---

## 6. Marketing funds — standard first, custom only with a reason

Salesforce ships standard objects for this, all "available in API version 41.0 and later":

| Object | What the Object Reference says it represents | Line |
|---|---|---|
| `PartnerMarketingBudget` | "a budget that provides funds to channel partners for selling and marketing products and services" | L209145–L209147 |
| `PartnerFundAllocation` | "allocated funds from a partner marketing budget for channel partners" | L208705–L208707 |
| `PartnerFundRequest` | "a request for funds from the partner marketing budget by a channel partner" | L208967–L208969 |
| `PartnerFundClaim` | "a claim of funds from the partner marketing budget by a channel partner" | L208834–L208836 |
| `ChannelProgram` | "a channel program that vendors use to market and sell their products through channel partners" | L65989–L65991 |
| `ChannelProgramLevel` | "a level, based on member experience, in a channel program" | L66092–L66093 |
| `ChannelProgramMember` | "a partner who is a member of a channel program" (has `LevelId`) | L66205–L66206 |

Two things follow for the requirements document:

- The tier model in §1 has a standard home: `ChannelProgramLevel` plus `ChannelProgramMember.LevelId`.
  A custom `Account.Tier__c` picklist is still a legitimate choice — it is simpler to report on and
  easier to reference from assignment-rule criteria — but it is now a **decision with a reason**,
  not the only option. Record which one this programme picked and why.
- **`ChannelPartnerId` is not usable in formulas.** "The `ChannelPartnerId` field isn't supported for
  formula fields, custom buttons, or custom links for the `PartnerFundAllocation` object. This
  limitation also applies to the `PartnerMarketingBudget` and `PartnerFundRequest` objects"
  (*Object Reference*, L208745–L208752). Any fund-tracking requirement phrased as "a formula that
  rolls the partner name onto the claim" is unbuildable as written; it needs a lookup on the
  reporting side or a workflow-populated text field.

---

## 7. Onboarding runbook

Order matters, and the order is grounded rather than stylistic.

| # | Step | Grounding |
|---|---|---|
| 1 | Set `Account.IsPartner = true` on the partner firm's Account | `IsPartner` "Indicates whether the account has at least one contact enabled to use the org's partner portal" (*Object Reference*, L13093–L13097) |
| 2 | Create the portal roles for that account | `UserRole.PortalAccountId` is read-only and ties a role to its partner account (L303469–L303476) |
| 3 | Create Contacts on that Account | `User.ContactId` is settable, and "The contact must have a value in the `AccountId` field or an error occurs" (L295089–L295098) |
| 4 | Create partner Users with `ContactId` **and** an explicit `PortalRole` | A null `PortalRole` silently assigns the User role (L303484–L303489) |
| 5 | Assign the partner profile and permission set that appear in `networkMemberGroups` | `NetworkMemberGroup` is what makes them site members (*Metadata API Guide*, L91430–L91443) |
| 6 | Add public-group and queue membership last | LDV guide: "Load users into roles… Configure public groups and queues, and let those computations propagate. Add sharing rules one at a time" (*Large Data Volumes*, L855–L868) |

`User.AccountId` never appears in that list because it is read-only ("ID of the Account associated
with a Customer Portal user… This field is null for Salesforce users" — *Object Reference*,
L294996–L295009, properties `Filter, Group, Nillable, Sort`). It is derived from the Contact.

For a bulk onboarding of 60 firms, the LDV guide's sharing advice also applies directly: "Avoid
having any user own more than 10,000 records" and "Distribute child records so that no parent has
more than 10,000 child records" (L1033, L1052–L1056). A channel manager who owns the whole
unassigned lead pool is exactly the ownership skew that guidance names.

---

## 8. Offboarding runbook

```text
Partner employee leaves          Partner firm terminated
─────────────────────────        ───────────────────────────────
1. Reassign open Leads/Opps      1. Reassign ALL open Leads/Opps to channel manager
2. User.IsActive = false         2. Deactivate every partner user on the account
3. Remove group/queue membership 3. Remove group/queue membership
4. Revoke permission sets        4. Revoke permission sets
                                 5. Archive content library share
                                 6. LAST: Account.IsPartner = true -> false
```

Step 6 is destructive and one-way. The Object Reference is explicit: "If you change this field's
value from `true` to `false`, you can disable up to 15 partner portal users associated with the
account and **permanently delete all of the account's partner portal roles and groups. You can't
restore deleted partner portal roles and groups**" (L13100–L13104).

Two more documented behaviours that shape the runbook:

- "Disabling a partner portal user in the Salesforce user interface or the API doesn't change this
  field's value from `true` to `false`" (L13104–L13106). Deactivating people does not tidy the flag,
  so the flag needs its own step.
- "Even if this field's value is `false`, you can enable a contact on an account as a partner portal
  user via the API" (L13106–L13108). A data-load path can therefore re-create partner users on a
  supposedly closed account. If offboarding must be enforceable, it needs a validation rule or a
  monitoring query, not the flag alone.

---

## 9. Acceptance tests

Run these against the sandbox after configuration and before the first partner logs in. Each one
maps to a row in §3.

```sql
-- A1. Every partner user has a portal role, and it is not silently the default.
--     A row here means step 4 of the onboarding runbook was skipped.
SELECT Id, Username, ContactId, AccountId, UserRoleId, UserType
FROM   User
WHERE  UserType = 'PowerPartner'
AND    IsActive = true
AND    UserRoleId = null

-- A2. Role depth actually matches the tier sheet in section 1.
SELECT PortalAccountId, PortalRole, COUNT(Id) roles
FROM   UserRole
WHERE  PortalType = 'Partner'
GROUP BY PortalAccountId, PortalRole

-- A3. Approved registrations that never reached the acceptance step.
--     PartnerAccountId is derived from the owner, so a null here is an
--     attribution hole, not a display quirk.
SELECT Id, Company, Status, OwnerId, PartnerAccountId
FROM   Lead
WHERE  Status = 'Approved - Registered'
AND    PartnerAccountId = null

-- A4. Partner-sourced opportunities that lost their partner account on conversion.
SELECT Id, Name, StageName, Amount, OwnerId, PartnerAccountId
FROM   Opportunity
WHERE  IsClosed = false
AND    Owner.UserType = 'PowerPartner'
AND    PartnerAccountId = null

-- A5. Accounts flagged as partners with no enabled partner user, and the reverse.
SELECT Id, Name, IsPartner,
       (SELECT Id FROM Contacts WHERE Id IN (SELECT ContactId FROM User WHERE IsActive = true))
FROM   Account
WHERE  IsPartner = true

-- A6. Offboarding leak check: active partner users on a de-flagged account.
SELECT Id, Username, AccountId, IsActive
FROM   User
WHERE  UserType = 'PowerPartner'
AND    IsActive = true
AND    Account.IsPartner = false
```

`User.UserType` is a restricted picklist whose partner value is `PowerPartner` — "User whose access
is limited because they're a partner and typically access the application through a partner portal or
Experience Cloud site. Label is Partner" (*Object Reference*, L297100–L297112). `UserRole.PortalType`
is `None` / `CustomerPortal` / `Partner` (L303490–L303502).

A6 is the query that proves the §8 runbook was followed, and it exists because the guide says
disabling users does not clear `IsPartner` and clearing `IsPartner` does not disable users. Neither
implies the other, so both are checked.

---

## 10. Handoff

| Artefact from this page | Goes to | What they do with it |
|---|---|---|
| Tier / licence worksheet (§1) | `skills/architect/license-optimization-strategy` | Priced against member vs login economics |
| Role plan (§2) | `skills/admin/role-hierarchy-design` | Portal roles created per partner account |
| Design YAML (§3) | `skills/admin/experience-cloud-site-setup` | Becomes the site build ticket |
| Visibility model (§4) | `skills/admin/sharing-and-visibility` | Authors the OWD, sharing sets and share rules |
| Deal-registration flow (§3, §5) | `skills/admin/lead-management-and-conversion` | Conversion mapping and lead process |
| Opportunity attribution rules (§5) | `skills/admin/opportunity-management` | Stage, forecast category and partner reporting |
| Guest-page boundary (none exposed here) | `skills/admin/experience-cloud-guest-access` | Confirms the partner site has no public pages |
| Acceptance SOQL (§9) | The build team's UAT pack | Run before the first partner logs in |

---

## Source lines used on this page

- *Metadata API Developer Guide* (`api_meta.txt`) — `Network` L90671–L91050; `CommunityRoles`
  L91153–L91161; `NetworkMemberGroup` L91430–L91443; `SharingSet` and `AccessMapping`
  L130365–L130520; `CommunitiesSettings` L112766–L112900; `SharingSettings` L126985–L127160;
  `Portal.selfRegUserDefaultRole` L96649–L96656; `PermissionSet.license` L94828–L94834;
  `userLicenseRestrictions` L95470–L95482.
- *Object Reference* (`object_reference.txt`) — `Account.IsPartner` L13093–L13110;
  `AccountRelationshipShareRule` L17416–L17560; `ChannelProgram` L65989–L66010;
  `ChannelProgramLevel` L66092–L66095; `ChannelProgramMember` L66205–L66240;
  `Lead.PartnerAccountId` L163743–L163757; `Opportunity.PartnerAccountId` L192799–L192814;
  `Partner` L208550–L208700; `PartnerFundAllocation` L208705–L208760; `PartnerFundClaim`
  L208834–L208860; `PartnerFundRequest` L208967–L208995; `PartnerMarketingBudget` L209145–L209175;
  `User.AccountId` L294996–L295009; `User.ContactId` L295089–L295102; `User.PortalRole`
  L295663–L295685; `User.UserType` L297100–L297125; `UserLicense.LicenseDefinitionKey`
  L299560–L299604; `UserRole` L303342–L303502.
- *Salesforce Developer Limits and Allocations Quick Reference* — Total API Request Allocations,
  L525–L547 and L555–L585.
- *Best Practices for Deployments with Large Data Volumes* (`ldv.txt`) — load sequencing L855–L868;
  ownership and child-record guidance L1033, L1052–L1056.
