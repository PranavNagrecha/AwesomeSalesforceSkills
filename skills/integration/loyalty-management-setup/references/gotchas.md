# Gotchas — Loyalty Management Setup

Non-obvious behaviors that cause real go-live problems. "Loyalty guide" means Loyalty Management, Spring '26 (loyalty.pdf). "Loyalty dev guide" means the Loyalty Management Developer Guide pages fetched from developer.salesforce.com on 2026-10-03 (LoyaltyMemberCurrency, LoyaltyProgramCurrency, LoyaltyTierGroup, LoyaltyProgramPartner, Transaction Journals Execution). "Metadata API" means the Metadata API Developer Guide, Version 67.0.

## Gotcha 1: DPE Templates Do Nothing Until Cloned, Activated, and Called From a Flow

**What happens:** Balances never update, qualifying points never reset, and points never expire, although the program looks complete.

**When it occurs:** Loyalty Management ships DPE definitions as templates. "Admins can clone these templates and customize them ... After the cloned definition is modified and activated, it's available in the Flow Builder as an action. Use the action to run the definition at your required frequency." An earlier version of this skill described activating and scheduling the definitions directly in Setup > Data Processing Engine; the guide describes cloning and running through flows.

**How to avoid:** Clone each template the program needs (balance calculation, Reset Qualifying Points, the expiration template that matches the expiry model, Roll Over Escrow Points if escrow is used), activate the clones, and build scheduled flows that call them. Put the flows on the go-live checklist.

**Source:** Loyalty guide, Data Processing Engine Definitions (Clone the Template Data Processing Engine Definitions).

---

## Gotcha 2: Tier Upgrades Come From a Generated Process, Not From the DPE Jobs

**What happens:** Members pass a tier threshold and stay in their old tier, and the team keeps re-running DPE jobs.

**When it occurs:** Tier assessment is done by a Change Tier loyalty program process, generated and activated when a program manager enters minimum eligible balances in Manage Tier Eligibility and clicks Generate Rules. It runs in real time as a child of a Transaction Journal process, or in batches through a Batch Management job. The process must be regenerated after changing any tier's eligible balance or name, or adding a tier, and a new process is needed after renaming the tier group. The generated process is visible only with the Loyalty Management - Growth or - Advanced license.

**How to avoid:** Generate the process for each tier group, decide real time or batch, and add regeneration to the change procedure for tiers. Turn on Select Members for Tier Assessment Automatically so the batch job only touches members whose qualifying balance changed.

**Source:** Loyalty guide, Tier Assessment; Configure a Tier Assessment Process; Select Members for Tier Upgrade Automatically.

---

## Gotcha 3: The Generated Tier Process Reads One Qualifying Currency

**What happens:** A design that combines spend and engagement into one status cannot be built with the generated rules.

**When it occurs:** "You can specify the minimum eligible point balance for one qualifying currency. To change member tier based on members' point balance for two or more currencies, set up a custom process. If your loyalty program has multiple tier groups, generate a process for each tier group." The data model allows several qualifying currencies on one tier group ("A tier group can have more than one qualifying point"), and `LoyaltyTierGroup.TierAssessmentCurrencyId` (API 58.0+) names the currency used to assign tiers. An earlier version of this skill stated the reverse constraint, that a tier group accepts exactly one qualifying currency; the guide says a qualifying currency belongs to only one tier group, not the other way round.

**How to avoid:** Prefer one assessment currency per tier group. If status truly depends on two currencies, build the custom process (a DPE definition or Apex class that selects eligible members, plus a Tier Processing process with the Change Member Tier action).

**Source:** Loyalty guide, Loyalty Program Currencies; Configure a Tier Assessment Process; Assess Member Tier by Using Loyalty Program Process. Loyalty dev guide, LoyaltyTierGroup (`TierAssessmentCurrencyId`).

---

## Gotcha 4: Partner Ledgers and Balances Come From One Definition

**What happens:** A team searches for a second "Update Partner Balance" definition that does not exist, or activates a clone of one template and expects two.

**When it occurs:** "The Create Partner Ledgers and Update Partner Balances Data Processing Engine definition template creates partner ledgers and updates partner balances based on the processed partner transactions." It updates partner points for prepaid billing or the balance amount for postpaid billing and creates credit and debit ledgers. An earlier version of this skill described two separate definitions.

**How to avoid:** Clone the single template, activate it, and run it from a flow after partner transactions are processed. Set `BillingType` and the cost per unit fields on each `LoyaltyProgramPartner` first.

**Source:** Loyalty guide, Create Partner Ledgers and Update Partner Balances Definition; Data Processing Engine Definitions. Loyalty dev guide, LoyaltyProgramPartner.

---

## Gotcha 5: New Currencies Do Not Reach Existing Members

**What happens:** A currency added after launch never shows a balance for enrolled members.

**When it occurs:** "If a currency is created after Loyalty Program Member records are created, you've to set up a custom process to create Loyalty Member Currency records for existing members." Renaming a currency also requires manually updating the name on the associated Loyalty Member Currency records.

**How to avoid:** Define all currencies before enrollment opens. When a currency must be added later, run a flow or batch that creates `LoyaltyMemberCurrency` records for every existing member, and include currency renames in the same job.

**Source:** Loyalty guide, Loyalty Program Currencies (Important note).

---

## Gotcha 6: Real-Time Balance Updates Can Double-Count With the Batch Templates

**What happens:** Member balances jump by twice the earned points after the nightly job.

**When it occurs:** "The out-of-the-box Data Processing Engine definitions assume that only they update member point balances in batches. If your org is customized to update member point balances in real time, ensure that these definitions ignore the Ledger records that were already processed."

**How to avoid:** Choose one balance-update path. If both are needed, customize the cloned definitions to skip processed ledgers and test with a member who earns in real time.

**Source:** Loyalty guide, Point Balance Calculation (Note).

---

## Gotcha 7: One Experience Cloud Site per Loyalty Program

**What happens:** A company with consumer and business programs cannot associate both with one Loyalty Member Portal site.

**When it occurs:** "You can't associate the same Experience Cloud site to another loyalty program." If the program is not associated with the site, the site shows "the details of all the programs the contact is associated with".

**How to avoid:** Plan one site per program, or deliberately leave a site unassociated when a combined view is wanted.

**Source:** Loyalty guide, Associate the Experience Cloud Site with a Loyalty Program; Loyalty Member Portal.

---

## Gotcha 8: Transaction Journals Execution Does Not Enforce Promotion Limits

**What happens:** A member receives a promotion reward after its usage limit is exhausted.

**When it occurs:** "Promotion limits configured on a PromotionLimit record aren't automatically enforced when transaction journals are created using this resource." The resource `/connect/realtime/loyalty/programs/{programName}` (API 54.0+) needs one of the B2C - Loyalty, B2C - Loyalty Plus, Loyalty Management - Growth, or Loyalty Management - Advanced licenses and the Loyalty Management permission set.

**How to avoid:** Call Eligible Promotions List (POST) first and pass the returned promotions as `appliedPromotions` in the Transaction Journals Execution request.

**Source:** Loyalty dev guide, Transaction Journals Execution (Note and Special Access Rules).

---

## Gotcha 9: A `LoyaltyProgramSetup` Label Typo Creates a New Program

**What happens:** A deploy of program processes succeeds, and a second, empty loyalty program appears in production.

**When it occurs:** The `label` field is the "Name of the loyalty program that the program process is associated with. If a loyalty program or referral program with the specified name doesn't exist, a new LoyaltyProgram record is created."

**How to avoid:** Retrieve `LoyaltyProgramSetup` from the target org first and deploy with the exact program name. Review the label in every pull request that touches these files. Only `Active` processes process transaction journals.

**Source:** Metadata API, LoyaltyProgramSetup (label and status fields).

---

## Gotcha 10: Non-Qualifying Points Never Drive Tier Changes

**What happens:** A program where members earn only "Reward Points" never changes anyone's tier.

**When it occurs:** Qualifying currency "is used for a member's tier evaluation"; non-qualifying currency "refers to the points that the member earns for redemption". Tier assessment reads the tier group's assessment currency.

**How to avoid:** Create a qualifying currency on the tier group and credit it from the same transactions that credit reward points.

**Source:** Loyalty guide, Loyalty Program Currencies; Loyalty dev guide, LoyaltyProgramCurrency (`CurrencyType`).
