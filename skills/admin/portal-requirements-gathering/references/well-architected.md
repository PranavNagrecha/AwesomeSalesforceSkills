# Well-Architected Notes — Portal Requirements Gathering

## Relevant Pillars

- **Trusted** — Access architecture (public / authenticated / hybrid) and license selection directly govern what data external users can read and write. Getting these wrong creates data exposure risk. Requirements must lock the access model and include guest user profile lockdown as a named deliverable.
- **Adaptable** — License type and access architecture are difficult to change at scale. Requirements must make forward-looking decisions that accommodate the business's likely phase 2 needs without over-engineering phase 1.
- **Easy** — Portal requirements should translate directly to a clear, prioritized feature scope that a build team can execute without ambiguity. The top-3 jobs model keeps scope manageable and measurable.

## Architectural Tradeoffs

**License cost vs. capability headroom**
Customer Community is lower cost per user but lacks advanced sharing and custom object flexibility. Customer Community Plus adds cost but removes the need for a future migration. The right answer depends on the sharing requirements identified during contact reason analysis and use case definition. Do not default to the cheapest license without confirming capability coverage.

**Hybrid access vs. authenticated-only**
Hybrid access increases reach (anonymous visitors can access public pages) but introduces guest user profile risk and adds complexity to the sharing model. Authenticated-only is simpler to govern and audit. Only choose hybrid if there is a clear, signed-off business case for public pages (e.g., a public knowledge base that reduces search engine-driven contacts).

**Phase 1 deflection focus vs. full community vision**
Full community portals (with social, gamification, and idea exchange) have higher long-term value but require the core self-service loop to work first. Phasing correctly means phase 1 delivers a measurable business outcome (deflection) before phase 2 adds community engagement features. Collapsing both phases into one produces a portal that is large in scope and difficult to measure.

## Anti-Patterns

1. **Feature-first requirements** — Selecting portal features before running contact reason analysis produces a portal that does not match what customers actually need. The Well-Architected principle of building for customer outcomes requires starting with evidence of what customers are trying to do, not what stakeholders believe they want.

2. **License selection as afterthought** — Treating license selection as an IT procurement task rather than an architectural decision delays it until build. Because license type governs sharing model, object access, and feature availability, a late or wrong license decision requires rework that impacts every other build decision made before it.

3. **Unscoped hybrid access** — Choosing a hybrid access model without explicitly documenting which pages are public, what the guest user profile permits, and how record-level access is controlled. This creates a trusted architecture risk (data exposure) that is invisible during requirements and expensive to fix post-launch.

## Official Sources Used

- Salesforce Developer Limits and Allocations Quick Reference (App Limits cheat sheet), "Total API Request Allocations" — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_app_limits_cheatsheet.pdf (the per-licence API allocation rows for Customer Community, Customer Community Login, Customer Community Plus, Customer Community Plus Login, Partner Community and Partner Community Login, and the `100,000 + (licences x per-licence calls) + add-ons` org total — used by the persona/licence matrix and the NFR table in `references/worked-examples.md`, and by gotcha 8)
- Metadata API Developer Guide, `SharingSet` / `AccessMapping` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (the Special Access Rules licence list, the `profiles` constraint, and the `object` / `objectField` / `userField` / `accessLevel` vocabulary — used by the access-model implications table and gotcha 7; the deployable XML itself lives in `skills/admin/sharing-and-visibility`)
- Metadata API Developer Guide, `Network` and `NetworkMemberGroup` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`selfRegistration`, `selfRegProfile`, `allowInternalUserLogin`, `enableMemberVisibility`, `enableGuestMemberVisibility`, `urlPathPrefix`, `site`, and membership by profile or permission set — used by the authentication decision section and gotcha 10)
- Metadata API Developer Guide, `CustomSite` and `Profile` / `ProfileCategoryGroupVisibility` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf (`guestProfile` as read-only, `siteGuestRecordDefaultOwner`, and the required `ALL` / `CUSTOM` / `NONE` data category visibility — used by gotchas 4 and 9)
- Object Reference for the Salesforce Platform, `User` and `Profile.UserType` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (`User.ContactId` requiring a Contact with an `AccountId`, `User.AccountId`, `User.PortalRole` defaulting silently, and the `PowerPartner` / `CspLitePortal` / `PowerCustomerSuccess` / `Guest` user types — used by the persona rows and gotchas 2 and 6)
- Object Reference for the Salesforce Platform, `NetworkMember` / `NetworkMemberGroup` — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf (site membership is granted by adding a profile or permission set, and members are "either users in your internal org or external users assigned portal profiles" — used by the internal-agent persona row)
- `standards/decision-trees/sharing-selection.md` — the repo's OWD / role hierarchy / sharing rules / sharing sets / Apex managed sharing routing tree, read before filling the Mechanism column of the access-model implications table rather than re-deriving the choice here
- `agents/experience-cloud-admin-designer/AGENT.md` § Mandatory Reads — the run-time consumer of this skill's catalogue; its reading list assumes the licence and access decisions are already made, which is what fixes the handoff checklist boundary in `references/worked-examples.md` section 6
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (the Trusted / Adaptable / Easy framing used in the Relevant Pillars section above)
