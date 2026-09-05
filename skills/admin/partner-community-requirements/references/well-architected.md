# Well-Architected Notes — Partner Community Requirements

## Relevant Pillars

- **Security** — PRM portals expose CRM data (Leads, Opportunities, MDF records, co-marketing assets) to external partner users. The sharing model must enforce tier-based record visibility using sharing rules and public groups. Partner users must never access records outside their tier or territory. Guest user access should be disabled for authenticated PRM portals. Security review must happen in the requirements phase, not after the portal is built.

- **Adaptability** — The partner tier hierarchy and deal registration rules are expected to change as the partner program matures (new tiers, new territories, adjusted approval thresholds). Configuration choices that hard-code tier values in profiles or Apex reduce adaptability. Tier-driven logic should live in picklist values, assignment rule criteria, and sharing rules so it can be updated without code changes.

- **Reliability** — The deal registration approval flow is a business-critical path. Approval process design must account for absence coverage (delegated approvers, queue-based routing rather than individual user routing) so that deal registrations are not blocked when a channel manager is out of office. Lead queue-based assignment (rather than user-based) ensures leads remain accessible when partner users are inactive.

- **Operational Excellence** — Partner onboarding (Account setup, user provisioning, tier assignment) should be documented as a repeatable process with a checklist. The `IsPartner` flag dependency, license assignment, and public group membership are steps that are easy to miss in ad-hoc onboarding. A defined runbook reduces errors and support burden.

## Architectural Tradeoffs

**Partner Community vs. Partner Community Plus:** Partner Community Plus adds reporting, dashboard, and broader sharing model capabilities at a higher per-seat cost. The tradeoff is feature richness vs. license spend. Projects that underestimate partners' reporting needs and provision standard Partner Community licenses often face a mid-program license upgrade, which requires re-provisioning all existing users.

**Push vs. Pull Lead Distribution:** Push (assignment rules) provides immediate lead delivery to partners but requires capacity logic to avoid overloading active partners. Pull (shared queue) gives partners agency and eliminates capacity complexity, but requires partners to proactively work the lead pool, which reduces lead response time. The right model depends on partner engagement levels and SLA requirements.

**MDF in Salesforce vs. External System:** Tracking MDF in Salesforce provides portal visibility and audit trail but requires custom object design and ongoing Salesforce administration. An external finance system may already handle budget tracking with better reporting capabilities. The tradeoff is consolidation (Salesforce) vs. leverage of existing tools (external). Define this decision in requirements and size both options before recommending.

## Anti-Patterns

1. **Customer Community license for PRM features** — Assigning Customer Community or Customer Community Plus licenses to partner users in a PRM implementation results in silent feature unavailability. PRM-specific components (deal registration, lead inbox, MDF) are gated to Partner Community license. This is the most expensive mistake to correct post-build because it requires license re-provisioning and potential portal rebuild.

2. **Profile-only tier visibility without sharing rules** — Designing tier-differentiated record visibility using profiles alone. All partner users in the same tier share the same license type, so profile cannot vary record-level access within the tier. Co-marketing assets, lead pools, and MDF records require sharing rules scoped to tier-based public groups to enforce tier visibility correctly.

3. **Assuming the fund model must be custom** — Writing `MDF_Budget__c` / `MDF_Request__c` /
   `MDF_Claim__c` into the requirements without first evaluating `PartnerMarketingBudget`,
   `PartnerFundAllocation`, `PartnerFundRequest` and `PartnerFundClaim`, which have shipped since API
   version 41.0. Custom is a defensible choice; skipping the comparison is not. The adaptability cost
   runs both ways: a custom model carries permanent maintenance, and a standard model carries the
   `ChannelPartnerId` formula restriction. Pick one on the evidence and write the reason down.

4. **Individual user-based approval routing and lead assignment** — Routing deal registration approvals to a specific named user (rather than a queue) and assigning leads to individual partner user records (rather than queues). This creates single points of failure: when the named approver or user is inactive, the entire workflow stalls. Queue-based routing provides resilience and auditability.

## Official Sources Used

- **Metadata API Developer Guide** (Summer '26 / v62 PDF), `Network` type field table — the site's
  partner-relevant fields, the `communityRoles` labels, `networkMemberGroups`, the "you can't update
  `emailSenderAddress` via Metadata API" note, and the `NetworkStatus` values (supports the site
  metadata in `references/worked-examples.md` §4b and the checker's `Network` rules).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

- **Metadata API Developer Guide**, `SharingSet` and `AccessMapping` — the licence list that includes
  Partner Community, the `object` list that excludes Lead, the `userField` and `accessLevel` values,
  and the sample definitions the worked example is shaped from (supports gotcha 8 and §4a).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

- **Metadata API Developer Guide**, `CommunitiesSettings` and `SharingSettings` — `enableEnablePRM`,
  `enablePRMAccRelPref`, `enableRelaxPartnerAccountFieldPref`, `enableNetPortalUserReportOpts`,
  `enablePartnerSuperUserAccess`, `enableAccountRoleOptimization`, and the support-gated
  `enablePortalUserVisibility` (supports gotchas 9 and 11, and step 1 of the Recommended Workflow).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf

- **Object Reference for the Salesforce Platform**, `Account.IsPartner`, `User` (`ContactId`,
  `AccountId`, `PortalRole`, `UserType`), `UserRole` (`PortalAccountId`, `PortalRole`, `PortalType`)
  and `UserLicense.LicenseDefinitionKey` — the licence keys, the four-value portal role picklist, the
  destructive `IsPartner` clause, and the onboarding order (supports gotchas 6, 7 and 10 and the
  acceptance SOQL in §9).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

- **Object Reference**, `Lead.PartnerAccountId` and `Opportunity.PartnerAccountId` — read-only,
  derived from the owning partner user, empty when the owner is not a partner (supports gotcha 9 and
  the acceptance step in the deal-registration flow).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

- **Object Reference**, `PartnerMarketingBudget`, `PartnerFundAllocation`, `PartnerFundRequest`,
  `PartnerFundClaim`, `ChannelProgram`, `ChannelProgramLevel`, `ChannelProgramMember`,
  `AccountRelationship` and `AccountRelationshipShareRule` — the standard fund and channel-program
  objects from API v41.0, the `ChannelPartnerId` formula restriction, and the `EntityType` list that
  includes Lead (supports gotchas 3 and 8 and the MDF section of SKILL.md).
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf

- **Salesforce Developer Limits and Allocations Quick Reference**, "Total API Request Allocations" —
  `Partner Community: 200` and `Partner Community Login: 10` API calls per licence per 24 hours in
  Enterprise/Professional and Unlimited/Performance (supports the tier worksheet in §1 and the
  login-vs-member row in Decision Guidance). The same document contains **no** limit on portal roles,
  sharing sets, partner accounts or portal users — those numbers are not available from it and should
  not be quoted as if they were.

- **Best Practices for Deployments with Large Data Volumes** — the load order "Load users into roles…
  Configure public groups and queues… Add sharing rules one at a time", and the 10,000-record
  ownership and child-record guidance (supports the onboarding runbook in §7).

- **Salesforce Well-Architected** — architecture quality framing (Trusted / Easy / Adaptable model)
  used for the pillar sections above.
  https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Repo standards used by the artefacts on this page: `standards/decision-trees/sharing-selection.md`
  (which record-access mechanism, cited rather than restated by the `exposed_objects` rows) and
  `agents/_shared/AGENT_CONTRACT.md` § Citations (the handoff table in §10 of
  `references/worked-examples.md` names the skill each artefact is routed to).
