# Gotchas — OmniScript Flow Design Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Preview Mode Passes but Activation Fails Without Navigate Action

**What happens:** The OmniScript Preview mode runs successfully in the Designer even without a Navigate Action — Preview does not validate structural requirements. Activation then fails with a validation error about the missing Navigate Action element.

**When it occurs:** Requirements documents that treat the "Submit" button as implicit (as in Screen Flow) without specifying a Navigate Action. The developer builds based on those requirements and passes internal preview testing, but the OmniScript cannot be activated.

**How to avoid:** Always explicitly document the Navigate Action in requirements — including the type (Navigation Action type: Navigate to URL, Navigate to Record, Navigate to OmniScript) and the destination. This is a required structural element, not optional.

---

## Gotcha 2: Pre-Step Data Is Not Available Until the Action Fires Before the Screen Renders

**What happens:** Data loaded in a Post-Step action on Step N is not available to pre-populate fields on Step N — it fires after the user clicks Next and is visible only on Step N+1. Requirements that say "load account name on the Address step" without specifying Pre-Step timing cause empty fields that look like broken data loading.

**When it occurs:** When requirements specify data pre-population without noting Pre vs Post timing. Developers default to Post-Step (which is the save pattern) and the pre-population fields are blank when the user sees the screen.

**How to avoid:** Requirements must explicitly note Pre-Step vs Post-Step for every data source action. Pre-Step = data appears on the current screen before user input. Post-Step = data is saved after the user clicks Next.

---

## Gotcha 3: Conditional View Requires Block Container Grouping — Not Field-Level Conditions

**What happens:** OmniScript Conditional Views are set on Block container elements, not on individual field elements. Requirements that specify "show field X if condition Y" without noting the Block grouping requirement lead developers to incorrectly apply conditions at the element level, which OmniScript does not support. The condition silently has no effect and all fields appear.

**When it occurs:** Requirements documents that list field-level conditions using standard wireframe notation without mapping to OmniScript's Block-based conditional structure.

**How to avoid:** Requirements must group all conditionally-shown elements into named Block containers with the Conditional View expression documented for the Block — not for individual elements. Use the format: Block Name, Condition Expression (`%FieldName:value% == 'X'`), Elements Inside Block.

---

## Gotcha 4: Standard Runtime and Package Runtime Have Different Activation Behavior

**What happens:** Spring '25+ Standard Runtime (OmniStudio on Core) compiles OmniScript to LWC at activation time. Package Runtime (managed package VBT) uses a different compilation path. A requirements document that doesn't note the runtime type can lead to build decisions (custom element override, namespace, HTML structure) that work on one runtime and fail on the other.

**When it occurs:** Orgs that are mid-migration from Package Runtime to Standard Runtime, or implementations that assume Standard Runtime without confirming the org type.

**How to avoid:** Requirements document header must state the org runtime type. Confirm in Setup > OmniStudio Settings whether the org is running Standard Runtime or Package Runtime.
