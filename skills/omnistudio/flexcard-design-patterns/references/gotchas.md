# Gotchas — FlexCard Design Patterns

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Empty Error State Renders a Blank Card — No Visible Failure

**What happens:** When a FlexCard data source call fails (IP returns `failureResponse`, SOQL throws an exception, Apex throws an AuraHandledException), the card renders its Error state template. If the Error state template is empty — the default after scaffolding — the card renders nothing. No spinner, no message, no console error visible to the page user.

**When it occurs:** Any time a FlexCard is deployed to production without an Error state configured. It is most likely to surface when an Integration Procedure hits a governor limit, a Named Credential is misconfigured, or a downstream system is unavailable.

**How to avoid:** Always configure the Error state before deployment. At minimum, add a text element bound to the failure node (e.g., `{IntegrationProcedure.errorMessage}`) and a static fallback message. Test the Error state by temporarily setting the IP to return `failureResponse: true` in the debugger. Make this a required item on your FlexCard review checklist.

---

## Gotcha 2: Template Changes Are Not Live Until Activation

**What happens:** A developer edits a FlexCard template in Card Designer, saves, and tests on a live record page — but the change does not appear. The designer preview shows the update, but the deployed LWC on the Lightning App Page still reflects the old template.

**When it occurs:** FlexCards compile to LWC components at activation time, not at save time. Saving a card in Card Designer persists the metadata but does not recompile the LWC. The page continues to render the previously activated compiled version until the card is explicitly activated again.

**How to avoid:** After every template edit, open the Card Designer, verify the change, and click **Activate**. In a deployment workflow, ensure the deployment pipeline includes the activation step. When using SFDX or the OmniStudio Migration Tool, activate the FlexCard in the target environment after deployment — activation does not transfer from source to target automatically.

---

## Gotcha 3: Child Card Iteration Multiplies Data Source Queries

**What happens:** A parent FlexCard has a child card embedded for iteration. The child card has its own data source (SOQL or IP). For every record in the iterated collection, the child card fires its data source independently. A list of 15 related records triggers 15 separate queries on card render.

**When it occurs:** Any FlexCard that uses child card iteration where the child card is configured with its own independent data source rather than receiving its data from the parent.

**How to avoid:** Retrieve all child record data in the parent card's data source (typically an Integration Procedure). Include the full child record data set as a nested collection in the IP output. Pass the collection down to the child card as its data context so the child card renders from local data with no additional query. The child card should have no data source of its own — it renders from what the parent provides.

---

## Gotcha 4: Conditional Visibility References Must Match the Exact Data Model Path

**What happens:** A conditional visibility expression evaluates to `false` (or never evaluates at all), so the element is always hidden or always shown regardless of the data value. The Card Designer does not validate path references at authoring time — it accepts any string.

**When it occurs:** When a developer uses an incorrect path like `{Record.Status__c}` instead of `{Record.Status}` (custom vs. standard field), or references a node that does not exist on the current state's data model (e.g., referencing `{IntegrationProcedure.someField}` when the data source is SOQL). The condition silently resolves to `false` because the path returns `null`.

**How to avoid:** Use the Card Designer's data node browser to select paths rather than typing them manually. After configuring conditional visibility, test the card with both a record where the condition should be `true` and one where it should be `false`. Check behavior with null/empty values explicitly — a null field value is not the same as `false`.

---

## Gotcha 5: OmniStudio Managed Package Metadata Namespace Breaks Standard SFDX Commands

**What happens:** SFDX retrieve/deploy commands that work correctly in a standard OmniStudio org fail or produce empty results in a managed-package OmniStudio org. The metadata component type names are different (`OmniInteractionConfig` vs. the standard type), and file paths and API names include a namespace prefix.

**When it occurs:** Partner orgs, ISV installations, and any org where OmniStudio was installed via the managed package (as opposed to the standard Salesforce Industries license that uses the native metadata type). You can tell by checking whether `OmniInteractionConfig` has a namespace prefix in Setup.

**How to avoid:** Identify the OmniStudio deployment mode before building any deployment pipeline. For managed-package orgs, use the OmniStudio Migration Tool (available in AppExchange) rather than raw SFDX commands. Document the deployment approach in the project's `salesforce-context.md` so subsequent contributors do not repeat the investigation.
