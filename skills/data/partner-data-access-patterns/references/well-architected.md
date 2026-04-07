# Well-Architected Notes — Partner Data Access Patterns

## Relevant Pillars

- **Security** — Partner data access is a trust boundary design problem. Each design decision either correctly enforces separation between competing partners or inadvertently exposes sensitive deal, pricing, or customer data. The role hierarchy and OWD settings are the primary enforcement mechanisms; sharing rules are the exception surface that requires the most scrutiny.
- **Reliability** — Sharing model correctness must be predictable across normal operations and edge cases (account ownership changes, user deactivations, license changes). An unreliable sharing model causes intermittent access failures that are difficult to diagnose and erode partner trust.
- **Performance** — Partner community orgs can accumulate large numbers of sharing rows when sharing rules are applied to high-volume objects. Poorly designed sharing rules or redundant hierarchy-plus-rule combinations can cause slow sharing recalculations. The Well-Architected principle of right-sizing access (use the least complex mechanism that satisfies the requirement) directly reduces sharing overhead.
- **Operational Excellence** — Manual shares are invisible in sharing rule lists. Without documented processes for managing manual shares, orgs accumulate stale access grants that cannot be audited. Operational excellence requires making the sharing model legible and maintainable.

## Architectural Tradeoffs

**Hierarchy vs Sharing Rules for Within-Account Access:** The auto-generated role hierarchy provides within-account manager visibility for free — no rules to maintain, no recalculation overhead beyond the initial hierarchy build. Sharing rules on top of hierarchy for the same access are wasteful. The tradeoff: hierarchy is inflexible (fixed 3-tier structure), while sharing rules are flexible but carry a maintenance and performance cost. Use hierarchy for standard within-account access and reserve sharing rules for genuinely cross-account or exception-based requirements.

**Partner Community License vs Customer Community Plus:** Partner Community licenses cost more but provide the 3-tier hierarchy and PRM object access. Customer Community Plus licenses are cheaper but provide only one role and no PRM object access. The correct tradeoff depends on whether hierarchical visibility and PRM objects are requirements. Cost-driven downgrading to CC+ without re-auditing access requirements is a common source of post-go-live defects.

**Criteria-Based vs Owner-Based Sharing Rules:** Criteria-based sharing rules fire based on field values (e.g., Type = "Co-Sell"), making them resilient to ownership changes. Owner-based rules fire based on record ownership and can produce unexpected behavior when ownership changes frequently in partner-managed pipelines. For cross-account partner sharing, criteria-based rules are almost always the better choice.

## Anti-Patterns

1. **Sharing rules duplicating hierarchy access** — Creating sharing rules to grant within-account manager visibility when the role hierarchy already provides it. This doubles the sharing overhead and makes the model harder to reason about. Avoid by understanding hierarchy boundaries before designing rules; use rules only when hierarchy cannot satisfy the requirement.

2. **Setting External OWD to Public Read/Write for simplicity** — Opening External OWD to avoid complexity in sharing rule design. This violates data separation between partner accounts and creates a compliance and competitive-intelligence exposure. Always start with Private External OWD and explicitly grant access.

3. **Assuming license equivalence between Partner Community and Customer Community Plus** — Designing a PRM access model for a Partner Community scenario, then licensing users as Customer Community Plus to save cost. The hierarchy depth and PRM object availability are fundamentally different between these license types. The architecture must be validated against the actual license in use.

## Official Sources Used

- Salesforce Help — Sharing Data with Partner Users — partner user provisioning, role hierarchy auto-generation, sharing behavior for external users
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_partner_data_sharing.htm&type=5

- Salesforce Help — Partner User Roles — auto-generated role hierarchy structure, Executive/Manager/User tier behavior, account-scoped hierarchy
  URL: https://help.salesforce.com/s/articleView?id=sf.networks_partner_roles.htm&type=5

- Salesforce Well-Architected Overview — architecture quality model, security and reliability pillar framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

- Salesforce Help — Experience Cloud User Licenses — license comparison matrix (Partner Community, Customer Community Plus, Customer Community), object and sharing mechanism availability per license
  URL: https://help.salesforce.com/s/articleView?id=sf.users_license_types_communities.htm&type=5
