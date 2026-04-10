# Gotchas — Multi-BU Marketing Architecture

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Role Assignments Do Not Cascade from Parent BU to Child BUs

**What happens:** A user with an Administrator role in the Parent BU has no access to any Child BU. When that user navigates to a Child BU (via the account switcher), they see a blank interface or receive a permissions error — even though they have the highest possible role in the org's root account.

**When it occurs:** Every time a new Child BU is created or a new user is added to the Parent BU without being explicitly provisioned in each Child BU they need to access. This is especially common after org migrations or when the admin team expands.

**How to avoid:** Build a Child BU onboarding checklist that includes explicit user provisioning as a mandatory step. For every Child BU, maintain a roster of users and their assigned roles. When provisioning a central admin team, they must be added and role-assigned individually in each Child BU — there is no "inherit from parent" option. Some teams automate this via the Marketing Cloud REST API (`POST /v2/accounts/{id}/members`) during BU provisioning.

---

## Gotcha 2: Deeply Nested BU Hierarchies Break Send Attribution Reporting

**What happens:** Analytics Builder's standard Email Performance and Subscriber reports aggregate send data at the BU level. When grandchild BUs exist (Parent → Regional Child → Country Grandchild), send performance for the grandchild BUs does not automatically roll up to the regional or parent level in standard reports. Each BU's data is reported independently, requiring manual aggregation.

**When it occurs:** Any time an organization adds a second tier of Child BUs — typically when attempting to model a geographic hierarchy (continent → country) or a brand/market hierarchy (brand → channel). The problem compounds as each new tier is added.

**How to avoid:** Keep the hierarchy flat — one Parent BU and one tier of Child BUs. If regional grouping is needed for reporting purposes, achieve it through naming conventions and custom SQL Activity queries rather than structural nesting. If a second tier is unavoidable, invest in a BI tool (Datorama, Tableau CRM, or a third-party data warehouse) that can aggregate across BUs via the Marketing Cloud API or data extracts, rather than relying on native Analytics Builder reports.

---

## Gotcha 3: Placing a DE in the Parent BU Does Not Automatically Share It with Child BUs

**What happens:** A data team creates a suppression list or shared audience in the Parent BU, assuming that Child BUs will automatically inherit access because the Parent BU is the administrative root. Child BU sends proceed without referencing the suppression list because the DE is invisible to the Child BUs.

**When it occurs:** Any time a DE is created in the Parent BU without an explicit Shared Data Extension folder permission configuration. This is almost universally surprising to teams migrating from single-BU implementations or from other ESP platforms that use org-wide shared lists by default.

**How to avoid:** After creating a DE intended for cross-BU use, navigate to the containing folder in the Parent BU, open folder properties, and explicitly configure Shared DE Permissions. Select each Child BU that needs access and set the appropriate permission level (Read or Read/Write). Verify by logging into a Child BU and confirming the Shared folder and its DEs appear in the Data Extensions interface. Add shared DE permission verification to the BU creation and DE creation checklists.

---

## Gotcha 4: All Subscribers List Is Enterprise-Wide, but BU-Level Unsubscribes Are Scoped

**What happens:** An unsubscribe recorded in Child BU A's email send updates the subscriber's status in Child BU A's All Subscribers list and the Enterprise-level All Subscribers list. However, Child BU B does not automatically suppress that subscriber unless it also references a shared suppression DE or the Enterprise All Subscribers list is configured as the suppression source for BU B.

**When it occurs:** Multi-BU implementations that rely solely on the default "All Subscribers" unsubscribe processing without configuring cross-BU suppression. Common in orgs that started as single-BU and later expanded to multi-BU without revisiting the suppression architecture.

**How to avoid:** Design the suppression strategy before creating Child BUs. For global opt-out requirements, establish a Shared DE-based suppression list as described in examples.md. Confirm suppression behavior with a test send from each Child BU before going live.

---

## Gotcha 5: SAP and IP Configuration Must Be Repeated for Each New Child BU

**What happens:** A new Child BU is created and immediately used for production sends. Emails are delivered from the org's default or shared IP with no BU-specific DKIM signing configured, which can affect deliverability and cause domain alignment issues for the Child BU's sending domain.

**When it occurs:** Child BU creation does not inherit sender authentication settings from the Parent BU or sibling BUs. Each new BU starts with no SAP or DKIM configuration until explicitly set up.

**How to avoid:** Include SAP setup, DKIM domain verification, Reply Mail Management configuration, and (if applicable) IP assignment in the mandatory BU creation runbook. For orgs using dedicated IPs, confirm with Salesforce support which IPs are assigned to the new BU and whether a warm-up plan is needed for new sending volume.
