# Gotchas — Industries Cloud Selection

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Industry Standard Objects Return SOQL Errors — Not Empty Sets — in Unlicensed Orgs

**What happens:** When a developer runs a SOQL query against an industry standard object (e.g., `SELECT Id FROM InsurancePolicy LIMIT 1`) in an org that does not hold the corresponding Industries license, Salesforce returns an error stating the object does not exist — not an empty result set. This is different from querying a custom object that has no records, which returns an empty list. The object itself is absent from the org's metadata schema.

**When it occurs:** Any time a developer, integration, or automated test runs SOQL or REST API calls against industry standard objects in a Developer Edition org, a standard Salesforce org without Industries licensing, or a sandbox that was refreshed from a licensed production org but whose sandbox license did not carry the Industries entitlement.

**How to avoid:** Always provision and validate the selection decision in a sandbox that holds the actual Industries license before any development begins. Confirm object availability by running a basic SOQL query from the Developer Console. Do not assume that a sandbox refreshed from a licensed production org automatically inherits Industries licensing — sandbox license entitlements are provisioned separately and may not match production.

---

## Gotcha 2: Insurance Cloud Cannot Be Licensed Without FSC — They Are Not Alternatives

**What happens:** A Salesforce AE or SI quotes only Insurance Cloud licenses for a property and casualty insurance implementation. The org is provisioned. `InsurancePolicy` objects appear in the schema because Insurance Cloud is licensed. However, the underlying FSC objects (`FinancialAccount`, household data model, relationship groups) that Insurance Cloud's data model and pre-built components depend on are missing — FSC was not included in the license purchase. Components and configuration that reference FSC base objects fail silently or produce "object not found" errors during setup.

**When it occurs:** When Insurance Cloud is purchased without FSC as the base layer. Insurance Cloud is architecturally layered on top of FSC. The two licenses are bundled in valid industry cloud configurations, but if a quote or order is assembled incorrectly and FSC is omitted, the org configuration is invalid.

**How to avoid:** Always verify the full license dependency chain during the selection and quoting phase. Insurance Cloud requires FSC. Any Insurance Cloud recommendation must explicitly include FSC in the license scope. When reviewing an implementation contract or SOW, confirm both licenses appear in the order form before the project starts.

---

## Gotcha 3: OmniStudio Standard Designer Migration Is One-Way and Cannot Be Undone

**What happens:** An existing org runs OmniStudio via the managed package. As part of upgrading to the platform-native OmniStudio model, a developer opens a managed-package OmniScript in the Standard Designer to complete the migration. From that point on, the component is platform-native — it is removed from the managed-package designer and cannot be returned to it. If the migration is started but the team decides to revert (e.g., because a dependent system was not ready), the component cannot be rolled back. The component exists only in the platform-native model.

**When it occurs:** During any managed-package to platform-native OmniStudio migration, even if the component is opened in the Standard Designer accidentally or as part of an exploratory review. The state change is committed at the point of opening, not at the point of saving.

**How to avoid:** Treat the OmniStudio packaging decision as a project-level commitment, not a per-component choice. Before beginning any migration of existing managed-package components, confirm that all downstream systems, integration points, and deployment processes are compatible with platform-native OmniStudio metadata. Document every component to be migrated and obtain formal sign-off before starting. Never open managed-package OmniStudio components in the Standard Designer in a production org as a test.

---

## Gotcha 4: Multiple Vertical Cloud Objects Can Coexist — But Require Multiple Licenses

**What happens:** An architect designs a multi-vertical solution for a conglomerate that includes both insurance policy management and energy service point management in the same Salesforce org. When the project starts, the team discovers that the org was licensed for only one vertical cloud, and the standard objects for the second vertical are absent. The assumption was that "Salesforce Industries" was a single license covering all vertical clouds.

**When it occurs:** When a customer or SI assumes that purchasing "Salesforce Industries" grants access to all vertical cloud standard objects. In practice, each vertical cloud is a separately licensed product. Communications Cloud, Insurance Cloud, Energy & Utilities Cloud, Health Cloud, and FSC are all distinct licenses. An org can hold multiple vertical cloud licenses simultaneously, but each must be purchased separately.

**How to avoid:** During selection, explicitly list every vertical cloud whose standard objects the solution requires. Confirm each appears as a separate line item on the license order form. For multi-vertical architectures, obtain written confirmation from Salesforce that the combination is a supported configuration before beginning the project.

---

## Gotcha 5: Refreshing a Sandbox Does Not Guarantee Industries License Parity with Production

**What happens:** A production org holds an Energy & Utilities Cloud license. The team refreshes a Full Copy sandbox from production to use for implementation testing. Developers begin building against `ServicePoint` and `UtilityAccount` objects. At some point, a second sandbox is refreshed for a different team, and that sandbox does not carry the E&U license — either because the org's sandbox license allocation was not configured correctly or because a different sandbox template was used. Developers in the second sandbox encounter SOQL errors against E&U objects and cannot reproduce production behavior.

**When it occurs:** When sandbox license entitlements are not explicitly provisioned and verified for each sandbox environment used in an Industries implementation. Sandbox license allocation is separate from production license allocation and must be managed in the Salesforce contract and org settings.

**How to avoid:** Before starting any development in a sandbox, confirm that the sandbox holds the same Industries licenses as production by checking org-level features in Setup or running a test SOQL query against a core industry standard object. Work with the Salesforce AE to ensure sandbox license entitlements are correctly provisioned before the project begins.
