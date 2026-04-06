# Well-Architected Notes — User Access Policies

## Relevant Pillars

### Security

User Access Policies are a direct implementation of the principle of least privilege. By tying permission assignments to user attribute criteria, UAP enforces that users receive only the permissions appropriate for their current role, profile, or department — and that permissions are revoked automatically when those attributes change. This removes a class of stale-access vulnerabilities that manual provisioning processes routinely leave behind. UAP also provides an auditable, declarative record of the provisioning logic, making access reviews more tractable.

### Operational Excellence

UAP eliminates manual permission provisioning steps from onboarding and offboarding checklists. Automating provisioning declaratively (without Apex code) reduces operational overhead, lowers the skill floor for managing provisioning logic, and makes the rules inspectable in Setup without reading code. Change management is simplified because UAP configuration is deployable as Salesforce metadata (`UserAccessPolicy` type), meaning provisioning rules travel with deployments and are version-controlled.

## Architectural Tradeoffs

**UAP vs. Apex Triggers:** UAP is the preferred approach for attribute-based provisioning when the filter logic can be expressed with AND equality conditions on standard user fields. Apex triggers offer more flexibility (arbitrary logic, cross-object lookups, conditional branching) but add code maintenance burden and require developer expertise. Choose UAP for the common case; reserve Apex triggers for complex provisioning logic that UAP cannot express.

**Declarative Simplicity vs. Evaluation Order Complexity:** UAP's grant-before-revoke evaluation order is simple to state but easy to violate in practice. As policy counts grow, the interaction surface between grant and revoke policies increases. Orgs that accumulate many policies without governance documentation can develop unexpected permission states. Establish a policy naming convention and a design document mapping each policy's filter to its intent before the policy count grows large.

**No Backfill on Activation:** UAP's forward-only evaluation model keeps the platform performant (no bulk re-evaluation of millions of users on policy activation), but it requires a separate operational step to bring existing users into compliance. This is a deliberate design tradeoff that practitioners must account for in their operational runbooks.

## Anti-Patterns

1. **Relying on UAP Alone for Immediate Bulk Remediation** — UAP does not re-evaluate existing users when a policy is activated. Using UAP as a remediation tool for a security finding that requires immediate bulk permission removal will fail silently — no existing users will have permissions revoked. Use UAP for ongoing provisioning governance; use a separate bulk data operation for immediate remediation.

2. **Running UAP and Apex Triggers in Parallel for the Same Users** — Keeping Apex triggers active that manage the same permission sets as UAP policies creates race conditions and unpredictable permission states. The two mechanisms are not coordinated by the platform. This anti-pattern is especially common during UAP adoption phases when teams incrementally migrate from Apex-based provisioning.

3. **Designing UAP Policies Without Documenting Evaluation Order** — Creating grant and revoke policies for overlapping user segments without a written map of which policies apply to which users leads to permission conflicts that are difficult to diagnose. The platform does not surface "why" a permission was revoked — only that it was. Maintain a policy design document that maps filter criteria to expected outcomes and identifies any users who match multiple policies.

## Official Sources Used

- Salesforce Help — User Access Policies: https://help.salesforce.com/s/articleView?id=sf.perm_user_access_policies.htm
- Salesforce Help — Active User Access Policy: https://help.salesforce.com/s/articleView?id=sf.perm_active_user_access_policy.htm
- Release Notes — User Access Policies GA (release 242): https://help.salesforce.com/s/articleView?id=release-notes.rn_permissions_user_access_policies_beta.htm
- Release Notes — UAP Enhanced Filter Support (release 246): https://help.salesforce.com/s/articleView?id=release-notes.rn_permissions_user_access_policy_filters.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
