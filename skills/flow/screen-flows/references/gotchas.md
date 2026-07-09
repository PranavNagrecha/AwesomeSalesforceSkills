# Gotchas - Screen Flows

## Early DML Changes What Back And Cancel Mean

**What happens:** Users think they are still reviewing information, but the flow has already changed records.

**When it occurs:** Create or update elements run before the interview reaches a true confirmation point.

**How to avoid:** Gather and review first, then commit late unless the business process explicitly requires otherwise.

---

## Custom Screen Components Need More Than Rendering

**What happens:** A custom input appears on the screen but does not integrate cleanly with Flow validation.

**When it occurs:** The component omits the validation methods or handles internal and external errors inconsistently.

**How to avoid:** Implement the validation contract intentionally and test Next, Back, and external error scenarios.

---

## Too Many Screens Create Cognitive Overhead

**What happens:** Users stop understanding where they are in the process or why another screen appeared.

**When it occurs:** The flow uses screens to hide complex logic instead of simplifying the experience.

**How to avoid:** Combine related inputs thoughtfully, remove low-value branches, and keep screens focused on one clear purpose.

---

## Standard Components Age Better Than Over-Customized Screens

**What happens:** A highly custom screen needs extra maintenance after platform changes or minor requirement shifts.

**When it occurs:** Teams build custom components for interactions that standard Flow screen fields already handled adequately.

**How to avoid:** Use custom LWC screen components only for real runtime UX gaps.

---

## Multi-Select Choice Output Is A String, Not A Collection

**What happens:** A Checkbox Group or Multi-Select Picklist is wired straight into a Loop, a Get Records filter, or a Transform element, and the flow errors or silently processes nothing.

**When it occurs:** The builder assumes a component that lets users pick several values returns a collection. It does not — every checked selection is stored in one semicolon-delimited text string (unstructured data). Elements that need structured data, such as Loop and Get Records, cannot consume it directly, and Checkbox Group, Choice Lookup, and Multi-Select Picklist are explicitly incompatible with the Transform element.

**How to avoid:** Convert the semicolon-delimited string into a collection variable before any Loop, Get Records, or Transform step. Remember these components also require the Lightning runtime, and on Lightning runtime version 58 and earlier they retain no memory of their values — selections are lost on Back navigation, pause/resume, or an input-validation error unless an attribute is configured to keep them.
