# Gotchas — Fit-Gap Analysis Against Org

Non-obvious behaviors that cause real fit-gap mistakes in production engagements.

---

## Gotcha 1: Misclassifying Process Builder as "Still Standard"

**What happens:** A reviewer sees existing Process Builders in the org and classifies a new requirement as "Standard automation via Process Builder, no new build needed."

**When it occurs:** Brownfield orgs with legacy automation. Process Builder is end-of-life in Salesforce — Salesforce Help officially recommends migration to Flow.

**How to avoid:** Treat Process Builder as a *migration backlog item*, never as a target for new requirements. Any row that would land in PB is Low-Code (Flow) at best, plus a `customization-debt` tag if PB is used as the temporary holding pattern.

---

## Gotcha 2: Treating Apex as Automatic When the Requirement Says "Automation"

**What happens:** The requirement reads "automate X when Y happens" and the reviewer reflexively classifies it as Custom (Apex).

**When it occurs:** When the reviewer has a developer background and skips the `automation-selection.md` decision tree.

**How to avoid:** Default to Low-Code. Promote to Custom only when the row genuinely needs same-transaction callout, complex bulkification, or behavior Flow cannot model. Cite the decision tree branch on the row.

---

## Gotcha 3: Ignoring License Caps That Turn Standard Rows Into GAP

**What happens:** A "Standard" Service Cloud row is delivered to the build team, who then discovers no Service Cloud user licenses exist for the persona.

**When it occurs:** Whenever the fit-gap reviewer treats the org's *edition* as the only license input.

**How to avoid:** Probe `Setup → Company Information → User Licenses` and `Permission Set Licenses`. Map every requirement to the personas that need it; cross-check each persona's license SKUs. License-blocker rows are Unfit, not Standard.

---

## Gotcha 4: Missing AppExchange Alternatives

**What happens:** A requirement is classified as Custom and routed to the apex-builder, when a $5/user/month managed package would have delivered 90% of the behavior.

**When it occurs:** When AppExchange is not part of the probe step.

**How to avoid:** For every Custom and Unfit row, search AppExchange before routing to a builder agent. Confirm the package's last-update date and supported edition. Add `appexchange_alternatives[]` to the JSON row when matches exist.

---

## Gotcha 5: Not Probing the Edition

**What happens:** A reviewer assumes Enterprise Edition and scores the matrix accordingly. The customer is on Professional Edition. Half the "Standard" rows are unavailable.

**When it occurs:** When the project starts with a requirements list and skips the org probe.

**How to avoid:** First action of every fit-gap engagement: confirm edition. Before any classification work, validate that every "Standard" feature being assumed is *actually* available in the customer's edition. Salesforce's edition comparison page is authoritative.

---

## Gotcha 6: Conflating Fit-Gap with Prioritization

**What happens:** Reviewers re-rank rows based on customer urgency or business value, then publish the matrix as the build plan.

**When it occurs:** When the team treats fit-gap as "the project plan" instead of "the routing manifest."

**How to avoid:** Fit-gap is *classification + effort + risk + handoff*. Prioritization is a separate exercise that consumes the matrix. Keep them in separate documents and separate columns.

---

## Gotcha 7: Treating Sandbox State as Production State

**What happens:** A feature is enabled in the partial-copy sandbox the consultancy has been demoing in. Production has it disabled. The matrix says Standard; the build fails.

**When it occurs:** Common in long sales cycles where the customer never enabled the feature in prod.

**How to avoid:** The probe step targets *production* (or the org that will receive the build), not the sandbox. If only the sandbox is accessible, every Standard row that depends on a feature flag must carry a `governance` tag pending production confirmation.

---

## Gotcha 8: Permission Cliffs

**What happens:** A "Standard" feature requires Setup access (e.g. Customize Application) for end users to use it directly. Without that permission the feature is effectively unavailable.

**When it occurs:** Knowledge management features, some report subscription features, some Lightning App Builder behaviors.

**How to avoid:** When classifying as Standard, also confirm the permission profile for the consuming persona. If end users need Setup-level permissions to use the feature, the row becomes Configuration (a permission-set authoring task) at minimum, possibly with a `governance` tag.
