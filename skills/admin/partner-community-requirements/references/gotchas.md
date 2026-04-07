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

## Gotcha 3: MDF Tracking Has No Standard Object in Core PRM

**What happens:** There is no standard `MDF_Budget__c`, `MDF_Request__c`, or `MDF_Claim__c` object in the base Salesforce PRM product (without Channel Revenue Management). Projects that assume MDF is "included" discover during build that they need to design, create, and test a custom object model from scratch.

**When it occurs:** Requirements workshops that rely on Trailhead PRM module overviews without checking whether MDF features require Channel Revenue Management. The Trailhead content demonstrates MDF capabilities without always making the license dependency explicit.

**How to avoid:** In the requirements phase, explicitly confirm with the Salesforce AE or solution engineer whether the org has Channel Revenue Management licensed. If not, specify the custom object data model (Budget, Request, Claim with their field lists, lookup relationships to partner Account, and approval process for claim reimbursement) as a build deliverable. Size the data model design effort — it is typically 2–3 days of configuration work before PRM portal build can begin.

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
