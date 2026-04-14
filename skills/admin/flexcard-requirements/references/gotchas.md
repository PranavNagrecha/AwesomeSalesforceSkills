# Gotchas — FlexCard Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Card State Templates Compile to LWC at Activation — Not at Save

**What happens:** Changes made to a FlexCard state template in Card Designer are not reflected in the running card until the card is reactivated. Saving the card does not update the running LWC output. This means that requirements that describe iterative state template changes during stakeholder review will each require a reactivation cycle, creating production outages for users currently viewing the card if changes are made to the active environment.

**When it occurs:** Any time requirements specify a FlexCard that will undergo iterative design review or mid-project state changes in a non-sandbox environment. Also occurs when a FlexCard is deployed to production and a state template change is requested in the same sprint.

**How to avoid:** Requirements must note the activation-required-for-changes behavior. All state template changes should be completed and approved in a sandbox before promoting to production. Document state template conditions completely at requirements time to minimize post-build iteration.

---

## Gotcha 2: Child FlexCards Must Be Activated Before the Parent Card Can Be Activated

**What happens:** A FlexCard that embeds a child FlexCard via a nested card component cannot be activated until the child FlexCard is in Active status. If requirements specify a nested card architecture without noting this dependency, the developer may build the parent card first, then be unable to activate it because the child card is still in Draft.

**When it occurs:** Any requirements that specify a parent FlexCard embedding one or more child FlexCards — common in summary cards with related list sections.

**How to avoid:** Requirements must explicitly document the card activation dependency order — list all child cards that must be activated before the parent card can be activated. Include this as a build sequence note in the requirements document.

---

## Gotcha 3: Integration Procedure Data Source Returns Empty Data Silently if IP Is Not Active

**What happens:** A FlexCard bound to an Integration Procedure data source silently returns empty data if the IP is in Draft or Inactive status. There is no error message on the card — fields simply appear blank. This can be confused with a broken data source mapping or a permissions issue.

**When it occurs:** When requirements specify a FlexCard using an IP data source that is still in development or when the IP is deactivated in the target environment after deployment.

**How to avoid:** Requirements must document which IPs serve as data sources and include an activation dependency note: the IP must be Active before the FlexCard can be activated. Add IP activation to the deployment checklist in the requirements document.

---

## Gotcha 4: Custom LWC Embedded in FlexCard Must Be Deployed Before Card Activation

**What happens:** A FlexCard that embeds a custom LWC component cannot be activated in an environment where the LWC has not been deployed. The FlexCard activation process validates that all embedded component references can be resolved. An undeployed LWC causes the activation to fail.

**When it occurs:** When requirements specify a custom LWC embedded in a FlexCard and the LWC is being built in parallel or has not yet been promoted to the target environment.

**How to avoid:** Requirements must note all custom LWC dependencies and include them in the deployment dependency sequence. The LWC must be deployed before the FlexCard is activated.
