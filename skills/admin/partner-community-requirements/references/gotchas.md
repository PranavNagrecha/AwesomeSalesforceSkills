# Gotchas — Partner Community Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Deal Registration Requires Lead — Cannot Register Against an Existing Opportunity

**What happens:** Standard PRM deal registration is built on the Lead object. When a partner submits a deal, they create (or reference) a Lead record. On approval, Salesforce converts the Lead to an Opportunity via the standard Lead Conversion process. There is no native mechanism in the base PRM product to register a deal against an Opportunity that already exists in the org.

**When it occurs:** Projects where the vendor's internal sales team creates Opportunities directly (before any partner interaction), and the business later wants partners to register those same deals. Also occurs in overlay sales models where an internal rep qualifies the deal before partner engagement.

**How to avoid:** Define the deal registration entry point during requirements. If any deals will already exist as Opportunities at the time of partner registration, specify this as a requirement and design a custom solution (custom deal registration object, or the Salesforce Channel Revenue Management product) before build begins. Do not attempt to retrofit this with a custom field on Opportunity — it breaks the standard audit trail and lead conversion reporting.

---

## Gotcha 2: Tier-Based Visibility Requires Sharing Rules — Profile Alone Is Insufficient

**What happens:** All partner users in the same tier share the same license type (Partner Community). Profile and permission set control object-level and field-level access, but they cannot create record-level visibility differences within the same profile. If Gold partners should see a lead pool that Silver partners cannot, this requires a sharing rule scoped to a Gold public group — not a profile setting.

**When it occurs:** Administrators who come from an internal Salesforce background design the security model around profiles and permission sets. They set up a "Gold Partner" profile with additional object permissions but do not configure sharing rules. All partners with the same license end up seeing the same records regardless of tier.

**How to avoid:** Define the full sharing model in the requirements phase. For each record type that has tier-differentiated visibility (leads, co-marketing files, MDF records), specify the sharing rule and public group configuration. Explicitly document that profile alone is insufficient for record-level tier visibility. Include sharing rule configuration in the build specification handed to the configuration team.

---

## Gotcha 3: The Standard Partner Fund Objects Exist — and `ChannelPartnerId` Cannot Be Used in a Formula

**What happens:** Salesforce ships a standard budget → allocation → request → claim chain for partner
marketing funds: `PartnerMarketingBudget` ("a budget that provides funds to channel partners for
selling and marketing products and services"), `PartnerFundAllocation`, `PartnerFundRequest` and
`PartnerFundClaim`, all "available in API version 41.0 and later", alongside `ChannelProgram`,
`ChannelProgramLevel` and `ChannelProgramMember`. A team that assumes MDF must be custom-built skips
the evaluation entirely.

The real constraint on the standard path is narrower and easier to hit: "The `ChannelPartnerId` field
isn't supported for formula fields, custom buttons, or custom links for the `PartnerFundAllocation`
object. This limitation also applies to the `PartnerMarketingBudget` and `PartnerFundRequest`
objects." So a requirement such as "show the partner's tier and region on the fund claim as a formula"
is unbuildable as written, and only surfaces when someone tries to save the field.

**When it occurs:** Two symmetrical failures. First, a requirements workshop that inherits "MDF is
custom in Salesforce" from an older engagement and specifies `MDF_Budget__c` / `MDF_Request__c` /
`MDF_Claim__c` without ever comparing them to the standard objects. Second, a team that correctly
picks the standard objects and then designs a reporting layer out of formulas on `ChannelPartnerId`,
which fails at build time with no design-time warning.

**How to avoid:** Evaluate the standard objects first and record the outcome as a decision with a
reason, not a default. If the design goes custom, the reason must be a specific requirement the
standard field set cannot carry. If it goes standard, check every proposed formula, button and link
against the `ChannelPartnerId` restriction before the field list is signed off, and move partner
attributes onto the reporting side (a report type or a workflow-populated field) rather than a formula.

---

## Gotcha 4: Lead Assignment Rules Cannot Natively Reference Partner Tier

**What happens:** Lead assignment rules evaluate fields on the Lead record. Partner tier is stored on the partner Account (a lookup from the Lead's `PartnerAccount__c` or similar field). Assignment rules do not support cross-object formulas, so a rule condition of `Partner_Tier__c = "Gold"` fails unless that value exists directly on the Lead record.

**When it occurs:** Teams design assignment rule criteria that include partner tier eligibility without first building the mechanism to stamp tier onto the Lead at creation or assignment time.

**How to avoid:** Add a cross-object formula field on Lead (`Partner_Tier__c = PartnerAccount__r.Tier__c`) or build a Flow that fires on Lead creation/update and stamps the tier value onto a plain text field. Document this dependency in the lead distribution requirements so the build team knows the formula field or flow must exist before assignment rules are configured.

---

## Gotcha 5: Partner User Creation Fails If Partner Account Checkbox Is Not Set

**What happens:** A Contact cannot be enabled as a Partner Experience Cloud user unless its parent Account has `IsPartner = true` (the Partner Account checkbox in the UI). If Accounts are created via data load or API without this flag, the "Enable Partner User" action is unavailable, and attempting to create the user via API produces a non-obvious permission error.

**When it occurs:** Bulk partner onboarding projects where Account records are migrated or created programmatically. The data migration script does not set `IsPartner = true`, and the partner user provisioning step fails for every migrated Account.

**How to avoid:** Include `IsPartner = true` in the Account creation or migration specification. If Accounts already exist in the org, run a data update to set the flag before partner user provisioning begins. Validate the flag in the post-migration checklist before attempting user creation.

---

## Gotcha 6: Partner Fields Are Gated on Partner Portal Licences, Not on Experience Cloud

**What happens:** `Account.IsPartner`, `Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` are
each documented with the same availability clause: available "if Partner Relationship Management is
enabled or if digital experiences is enabled **and you have partner portal licenses**". Turning on
digital experiences alone does not produce any of them. The Partner Account checkbox does not appear,
the partner-account fields on Lead and Opportunity stay absent, and every downstream design that
references them has nothing to reference.

**When it occurs:** A discovery workshop run in a sandbox that has Experience Cloud enabled but no
partner licences provisioned — which is the normal state of a developer or partial sandbox before the
licences are ordered. The requirements document is written against what the sandbox shows, and the
gap is discovered when the design is validated in a licensed org.

**How to avoid:** Query `UserLicense` in the target org before writing anything and confirm the
partner keys are actually present: `PID_Partner_Community`, `PID_Partner_Community_Login`, and the
legacy `PID_STRATEGIC_PRM` / `POWER_PRM` that some long-lived orgs still carry. Two related
availability clauses are worth confirming in the same pass: `AccountBrand` requires "a Partner
Community or Customer Community Plus license", and `ProcessDefinition` is readable by "Portal and
communities users with the Customer Community Plus and Partner Community licenses" — so a partner user
who must see their own approval history depends on that licence too.

---

## Gotcha 7: Portal Role Depth Is a Fixed Four-Value Picklist, Not a Hierarchy You Design

**What happens:** `UserRole.PortalRole` is a **restricted** picklist and its documented values are
`Executive`, `Manager`, `User`, `PersonAccount`. The same four values appear as the `PortalRoles`
enumeration behind `Portal.selfRegUserDefaultRole` in the Metadata API Guide. A partner account
therefore supports at most three stacked hierarchy levels, and there is no way to add a fourth.

Worse for bulk onboarding: `User.PortalRole` is nillable, and the Object Reference states that in API
version 16.0 and above, "when you set this field to null, a portal role is not automatically created.
When this field is null and a `ContactId` is provided, the user is assigned to the User role." A load
file that omits the column does not error — it silently flattens every partner user to the bottom of
their firm's hierarchy, and the roll-up visibility the design promised never materialises.

**When it occurs:** A programme that models partner firms with four or five internal levels (global
principal → country lead → regional manager → team lead → rep) and discovers at build time that only
three fit. And any bulk user load written from a spreadsheet that has a "Role" column for the internal
hierarchy but not for `PortalRole`.

**How to avoid:** Fix role depth per tier at requirements time — one number between 1 and 3 per tier,
which is exactly what the design artefact in `references/worked-examples.md` records and what
`scripts/check_partner_community_requirements.py` enforces. Where a partner firm genuinely has more
levels than three, the extra levels are a reporting concern, not an access concern; solve them with a
grouping field, not with roles. Make `PortalRole` a mandatory column in every partner user load
template and verify it with acceptance query A1.

---

## Gotcha 8: A Sharing Set Cannot Target Lead

**What happens:** Sharing sets are the natural mechanism for "let a partner user see the records that
hang off their account", and they cover a lot: the guide's `AccessMapping.object` list is Account,
Campaign, Contact, Case, custom objects, Opportunity, Order, ServiceContract, User and WorkOrder.
Lead is not on that list. A lead pool designed around a sharing set has no mechanism behind it, and
the gap only becomes visible when someone opens the Sharing Set page and finds Lead missing from the
object picker.

**When it occurs:** Pull-model lead distribution. The design says "eligible partners see the regional
lead pool", the sharing model section says "sharing set scoped to the partner's account", and nobody
checks the two against each other until configuration.

**How to avoid:** Pick the mechanism per object from a documented set and write it down per object.
For Lead specifically, the documented options are queue ownership (the partner user is a queue
member), a criteria-based or owner-based sharing rule shared to a `portalRole` or
`portalRoleandSubordinates` group, or `AccountRelationshipShareRule`, whose `EntityType` list does
include Lead and whose `AccountToCriteriaField` list includes `Lead.PartnerAccountId`. Account
relationships need `CommunitiesSettings.enablePRMAccRelPref` turned on, and the `AccountRelationship`
object's own access note says the "Enable Account Relationships org preference… is off by default".

---

## Gotcha 9: `PartnerAccountId` Is Read-Only and Derived From Whoever Owns the Record

**What happens:** `Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` both carry the properties
`Filter, Group, Nillable, Sort` — no Create, no Update — and both are documented as "ID of the partner
account for the partner user that **owns** this lead / opportunity… If the owner of the
lead/opportunity isn't a partner user, this field has no value."

Two things follow that break naive designs. A Flow or Apex step that tries to "stamp the partner
account on the opportunity" cannot write the field. And a registration that is approved by a channel
manager but never transferred to a partner user converts into an opportunity with an empty
`PartnerAccountId` — so partner-sourced revenue is under-reported, silently, for as long as nobody
runs the query.

**When it occurs:** Any deal-registration flow whose approval step is the last step. The approver is
an internal user, the record stays with them through conversion, and the attribution field never
populates.

**How to avoid:** Put an explicit ownership-transfer step between approval and conversion, and make it
a numbered step in the requirements, not an implementation detail. Where the business genuinely needs
a channel manager to attribute a deal to a partner who does not own it, the switch is
`CommunitiesSettings.enableRelaxPartnerAccountFieldPref` — "allows editing for partner account fields
on and opportunities and leads" — which is org-wide and therefore a decision with a blast radius, not
a field-level permission. Verify with acceptance queries A3 and A4 in
`references/worked-examples.md` §9.

---

## Gotcha 10: Clearing the Partner Account Checkbox Permanently Deletes That Account's Portal Roles and Groups

**What happens:** The Object Reference is unusually blunt about `Account.IsPartner`: "If you change
this field's value from `true` to `false`, you can disable up to 15 partner portal users associated
with the account and permanently delete all of the account's partner portal roles and groups. **You
can't restore deleted partner portal roles and groups.**"

Two further clauses make the offboarding sequence non-obvious in both directions. "Disabling a partner
portal user in the Salesforce user interface or the API doesn't change this field's value from `true`
to `false`" — so deactivating everyone does not tidy the flag. And "Even if this field's value is
`false`, you can enable a contact on an account as a partner portal user via the API" — so clearing
the flag does not lock the account either.

**When it occurs:** A partner agreement is terminated and an admin does the tidy-up in the order that
feels natural: clear the flag first, because it looks like the master switch. The account's portal
roles vanish with it, and re-onboarding that partner six months later means rebuilding the role
structure and every group membership that referenced it.

**How to avoid:** Sequence offboarding as reassign → deactivate → remove group and queue membership →
revoke permission sets → and only on full termination, clear `IsPartner`. Note that the documented
"up to 15" is a bound on what the flag change disables, not a guarantee that it covers everyone, which
is another reason deactivation is its own step. Because clearing the flag does not prevent API-driven
re-enablement, an offboarding requirement that must be enforceable needs a monitoring query — A6 in
`references/worked-examples.md` §9 — rather than trusting the flag.

---

## Gotcha 11: Two Partner Sharing Behaviours Are Org-Wide Switches, One of Them Support-Gated

**What happens:** Two `SharingSettings` fields change partner record visibility across the whole org,
not per site and not per tier.

`enablePortalUserVisibility` "Indicates whether portal users in the same customer or partner portal
account can see each other regardless of the organization-wide defaults" — and, critically, "To enable
this field, contact Salesforce Support." It cannot be turned on inside a sprint.

`enableAccountRoleOptimization` "Indicates whether person roles are assigned to new site users in
accounts without existing users (`true`) or if regular site roles are created for new users
(`false`). This field has a default value of `false`." Flipping it changes what a newly enabled
partner user gets, which means the role plan written for existing partners does not describe the
partners onboarded after the flip.

`enablePartnerSuperUserAccess` ("whether you can grant super user access to partners in sites") is the
third field in this family and needs the Customize Application permission.

**When it occurs:** A requirement phrased as "partner users at the same firm should see each other in
the member directory" arrives in UAT week. It reads like a site setting; it is a support case with a
lead time. Or: a design is validated against a handful of existing partner accounts, then
`enableAccountRoleOptimization` is flipped during a later data-loading exercise, and every partner
onboarded afterwards has a different role shape from the ones the design was tested on.

**How to avoid:** Read all three flags in the licence-and-switch audit (step 1 of the Recommended
Workflow) and record their current values in the requirements document. Anything that needs
`enablePortalUserVisibility` becomes a dated support case in the plan with the go-live date behind it.
Anything that depends on role shape states which value of `enableAccountRoleOptimization` it assumes.
