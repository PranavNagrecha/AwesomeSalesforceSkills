# Examples — CPQ Product Catalog Setup

## Example 1: Simple Bundle — Laptop with Accessories

**Context:** A hardware company sells a laptop bundle. The bundle always includes the laptop base unit and a power adapter (required). The customer can optionally add a carrying case and an extended warranty. These four products are grouped into two features: "Core Hardware" and "Accessories."

**Problem:** Without correct Product Option configuration, the rep can remove required components from the quote, or default-selected accessories get overlooked during quoting.

**Solution:**

Product Options setup (all linked to the Laptop Bundle parent product):

| Child Product | Feature | Required | Selected | Min Qty | Max Qty |
|---|---|---|---|---|---|
| Laptop Base Unit | Core Hardware | true | true | 1 | 1 |
| Power Adapter | Core Hardware | true | true | 1 | 1 |
| Carrying Case | Accessories | false | false | 0 | 1 |
| Extended Warranty | Accessories | false | true | 0 | 1 |

Feature configuration:
- "Core Hardware" — Min Options: 2, Max Options: 2 (enforces both required items always present)
- "Accessories" — Min Options: 0, Max Options: 2 (fully optional)

No product rules are needed for this pattern. Required = true on a Product Option is the correct mechanism to enforce mandatory inclusion. The Extended Warranty is pre-selected but removable.

**Why it works:** Product Options with `SBQQ__Required__c = true` are locked in the configurator UI — the rep cannot deselect them. Setting `SBQQ__Selected__c = true` on the Extended Warranty ensures it appears checked by default without forcing inclusion. This avoids creating unnecessary Selection rules that would fire on every configurator open.

---

## Example 2: Dynamic Bundle with Filter Rules — Cloud Service Tier Selection

**Context:** A SaaS company sells a Cloud Platform bundle where available add-on services depend on the service tier chosen by the rep. Standard tier customers see only basic monitoring and support add-ons. Enterprise tier customers see advanced analytics, dedicated support, and SLA upgrades in addition.

**Problem:** Without filter rules, all options appear in the configurator regardless of tier, causing reps to quote incompatible combinations and requiring downstream Validation rules to block mismatches.

**Solution:**

Step 1 — Create all Product Options for the Cloud Platform bundle:
- Basic Monitoring (visible to all tiers)
- Standard Support (visible to all tiers)
- Advanced Analytics (Enterprise only)
- Dedicated Support (Enterprise only)
- SLA Upgrade (Enterprise only)

Step 2 — Create a Configuration Attribute on the Cloud Platform bundle:
- Attribute Label: "Service Tier"
- Column: Maps to `SBQQ__QuoteLine__c.Service_Tier__c` (custom field)
- Feature: Header (not tied to a specific feature group)
- Default Value: "Standard"

Step 3 — Create a Filter Product Rule named "Hide Enterprise-Only Options for Standard Tier":

Conditions:
- `SBQQ__QuoteLine__c.Service_Tier__c` equals "Standard"

Actions (one per hidden option):
- Action Type: Show / Hide for each Enterprise-only option (set to "Hide")

Step 4 — Create an inverse Filter rule "Show Enterprise Options for Enterprise Tier":

Conditions:
- `SBQQ__QuoteLine__c.Service_Tier__c` equals "Enterprise"

Actions:
- Action Type: Show for each Enterprise-only option

Sequence these rules: Standard Hide rule = 10, Enterprise Show rule = 20.

**Why it works:** When the rep changes the "Service Tier" attribute in the configurator header, CPQ re-evaluates the filter rules and re-renders the option list. Enterprise-only options are hidden when "Standard" is selected, eliminating incompatible quoting at the source rather than blocking it post-hoc with Validation rules.

---

## Anti-Pattern: Using Validation Rules to Enforce Required Components

**What practitioners do:** A Validation Product Rule is created with a condition that fires when a required component option is not selected, showing an error message like "Power Adapter is required."

**What goes wrong:** The Validation rule fires on every save attempt for every quote that includes this bundle, adding processing overhead. More critically, the rule is evaluated server-side on save — the rep only discovers the violation after attempting to save, rather than being prevented from deselecting the option in the first place. If the rule condition is slightly misconfigured, required components can slip through.

**Correct approach:** Set `SBQQ__Required__c = true` on the Product Option record. This locks the option in the configurator UI before the rep can attempt a save. Reserve Validation rules for business logic that cannot be expressed as a Product Option constraint — for example, ensuring that the quantity of one option does not exceed the quantity of another option.
