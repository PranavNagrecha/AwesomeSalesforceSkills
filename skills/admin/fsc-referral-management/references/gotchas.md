# Gotchas — FSC Referral Management

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Missing ReferralRecordTypeMapping Entry Silently Drops All Routing

**What happens:** A referral is created successfully with the correct Lead record type and an Expressed Interest value, but the Lead is never assigned to a queue or user. No error appears on the record, in the Lead Assignment Log, or in any system alert. The referral looks healthy while routing has completely failed.

**When it occurs:** Any time a Lead record type is used for referral creation in FSC but there is no active `ReferralRecordTypeMapping__mdt` record whose `LeadRecordTypeDeveloperName__c` field matches the developer name of that record type. This happens most often when a new business line is added, a record type is renamed, or a metadata entry is deactivated.

**How to avoid:** Before deploying any new referral type, always deploy the corresponding `ReferralRecordTypeMapping__mdt` entry first and confirm it is active. After deployment, create a test referral and immediately check the Lead Assignment Log on the record to confirm a queue assignment was made. Do not rely on the absence of errors as confirmation that routing succeeded.

---

## Gotcha 2: Einstein Referral Scoring Was a Separately Licensed Feature and Is Retiring

**What happens:** Configurations that reference Einstein Referral Scoring — including any Einstein-specific setup flows, the Einstein Referral Scoring toggle in FSC Settings, or documentation written for that feature — describe a capability that is being retired. New orgs may not have it available at all; existing orgs relying on it will lose the feature at retirement.

**When it occurs:** When a practitioner searches for FSC referral scoring and finds older Trailhead content, blog posts, or implementation guides that document Einstein Referral Scoring as a current feature. The feature name and the Intelligent Need-Based Referrals feature name are often used interchangeably in legacy documentation, causing confusion.

**How to avoid:** Use Intelligent Need-Based Referrals as the scoring mechanism. Do not configure Einstein Referral Scoring for any new implementation. If an org has Einstein Referral Scoring active, plan migration to Intelligent Need-Based Referrals before the retirement date. When reviewing Salesforce Help or Trailhead content for FSC referral scoring, check the publication date and look for retirement notices. The Salesforce Help article "Referral Scoring Feature for Financial Services Retirement Notice" documents this explicitly.

---

## Gotcha 3: Partner Referrals Credit a Contact Record, Not a User — Referrer Score Requires Explicit Exposure

**What happens:** For external partner referrals submitted through Experience Cloud, `ReferredBy__c` is set to a Contact record rather than a User. Referrer Score is attributed to that Contact. If developers or admins build queries, reports, or page layouts that assume `ReferredBy__c` is always a User lookup, they will get null values or broken references for all partner-submitted referrals. Additionally, `ReferrerScore__c` is not on any default Experience Cloud page layout, so partners cannot see their own score without explicit configuration.

**When it occurs:** Any time partner referrals are in scope and the implementation team designs referral history, scoring visibility, or partner leaderboard features without accounting for the Contact-based referral credit model. Also occurs when a practitioner adds `ReferrerScore__c` to an internal Lead layout and assumes it appears in the Experience Cloud portal automatically.

**How to avoid:** When writing SOQL queries or building reports that traverse `ReferredBy__c`, handle both User and Contact as possible parent objects. When designing Experience Cloud partner referral pages, explicitly add `ReferrerScore__c` to the page layout in Experience Builder and set FLS for the community profile. Validate by logging in as a test partner community user and confirming the score is visible.

---

## Gotcha 4: Expressed Interest Picklist Values Must Match Assignment Rule Criteria Exactly

**What happens:** A Lead Assignment Rule entry is configured to route referrals with `Expressed Interest = "Home Loan"`, but the picklist value in the org is defined as `"HomeLoan"` (no space) or `"Home loan"` (different case). The rule never fires. Referrals land unassigned with no explanation.

**When it occurs:** During initial setup when picklist values are defined in one environment and Assignment Rules are configured in another (e.g. picklist in a scratch org, rules in UAT), or when picklist values are renamed after rules are created. Salesforce stores picklist API values separately from labels; the Assignment Rule evaluates against the API value.

**How to avoid:** After creating or modifying Expressed Interest picklist values, open each affected Assignment Rule entry in Setup and confirm the filter value shown matches the picklist API value exactly. When deploying picklist value changes, review all downstream Assignment Rule entries for exact-match dependencies. Use the `Expressed Interest` field's picklist API value list (not the label) as the authoritative reference when creating rule criteria.

---

## Gotcha 5: Referral Management Feature Toggle Must Be On Before Testing Routing

**What happens:** Lead Assignment Rules are configured correctly and ReferralRecordTypeMapping entries exist, but test referrals created directly via the Lead object (not through the FSC referral UI) do not trigger FSC routing behavior. Routing appears broken even when configuration is correct.

**When it occurs:** When developers or admins test referral routing by creating Lead records directly through the standard Lead new-record flow or via data loader, bypassing the FSC Referral Management entry point. FSC referral routing is triggered through the FSC-specific referral creation path, not the generic Lead create path.

**How to avoid:** Always test referral routing by creating referrals through the FSC Referral Management UI (the "New Referral" action on the Referral tab or the relevant FSC component), not by creating Lead records directly. If automated testing is needed, use the FSC Referral Management API or the proper record type with the FSC entry point to ensure the routing pipeline fires.
