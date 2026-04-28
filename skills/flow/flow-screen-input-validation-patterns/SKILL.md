---
name: flow-screen-input-validation-patterns
description: "Design input validation inside Screen Flow screens using component-level <validationRule> (formula + errorMessage), isRequired, cross-field rules on the second field, reactive components, and screen-level Decision fallbacks for cross-screen checks. Trigger keywords: screen flow validation rule, EndDate after StartDate validation in flow screen, block Next button until input valid. NOT for record-level Validation Rules — see admin/validation-rules-and-formulas. NOT for Apex-side input checks — see apex/input-validation-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Operational Excellence
triggers:
  - "screen flow validation rule on input field"
  - "EndDate after StartDate validation in flow screen"
  - "block Next button until input valid"
  - "screen flow inline error message vs decision element"
  - "reactive validation custom LWC in screen flow"
tags:
  - flow-screen-input-validation-patterns
  - screen-flow
  - validation
  - input-components
  - reactive-screens
  - accessibility
inputs:
  - Screen Flow design (which screens, which inputs per screen)
  - Validation contract per input (formula expression + user-facing error message)
  - Cross-field and cross-screen dependencies between inputs
  - Whether reactive components are enabled in the org
outputs:
  - Validated input components with `<validationRule>` formula + errorMessage
  - Screen-level Decision fallbacks for cross-screen validation only
  - Custom LWC `@api validate()` contract where bespoke components are used
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-27
---

# Flow Screen Input Validation Patterns

Activate this skill any time a Screen Flow captures user input that must satisfy a format, range, regex, or cross-field constraint **before** the user clicks Next. The skill is the contract between `agents/flow-builder/AGENT.md` (which decomposes screens and assigns "validation per screen") and `agents/flow-analyzer/AGENT.md` (which audits screen flows that allow junk data into the system because they have no inline validation).

---

## Before Starting

Gather this context before designing or auditing any screen-flow input:

- **What data shape does each screen capture?** Inventory the inputs per screen with their type (Text, Number, Date, Date/Time, Picklist, Checkbox, Long Text, custom LWC) — different component types accept different formula return shapes.
- **What business rule must each input satisfy?** Format (email regex), range (`Age >= 18`), cardinality (5–500 chars), enumeration (must be one of three picklist API names), conditional presence (`Phone` required only when `ContactMethod = 'Phone'`).
- **Are any rules cross-field or cross-screen?** Cross-field on the same screen → put the rule on the *second* field. Cross-screen → screen-level Decision on the downstream screen, not a per-input rule.
- **Is the underlying object protected by a record-level Validation Rule?** Inline validation is a UX layer; the object's Validation Rule is the authority. Both are needed (defence-in-depth) but the formulas should not contradict each other.
- **Is the org on Winter '24+ with Reactive Screens enabled?** Reactive components can show validation feedback live (on each keystroke / change) instead of only when Next is clicked.
- **Are any inputs custom LWC screen components?** Custom LWCs do NOT inherit `<validationRule>`. They must implement `@api validate()` returning `{isValid, errorMessage}`.

The most common wrong assumption: practitioners think a Decision element placed *after* the input screen is "validation". It is not — the user has already clicked Next. Real validation blocks Next inline.

---

## Core Concepts

### Concept 1 — Component-level `<validationRule>`

Every Screen Input Component (Text, Number, Date, Date/Time, Currency, Picklist, Checkbox, Long Text Area, etc.) accepts a single `<validationRule>` element with two children:

- `<formulaExpression>` — a Salesforce formula that **must return BOOLEAN**. `TRUE` = valid (allow Next). `FALSE` = invalid (block Next, render `errorMessage` under the field).
- `<errorMessage>` — the user-facing string. Plain text. Shown inline beneath the component.

The component's own value is referenced inside the formula via `{!ScreenComponentApiName}`. The formula re-evaluates when the user clicks Next; it does **not** re-evaluate on every keystroke unless the component is reactive.

```xml
<fields>
    <name>Email</name>
    <dataType>String</dataType>
    <fieldType>InputField</fieldType>
    <isRequired>true</isRequired>
    <validationRule>
        <formulaExpression>AND(
            LEN({!Email}) &gt; 5,
            CONTAINS({!Email}, "@"),
            CONTAINS({!Email}, ".")
        )</formulaExpression>
        <errorMessage>Enter a valid email address (must contain @ and a domain).</errorMessage>
    </validationRule>
</fields>
```

The two failure modes that bite in production:
- The formula returns a Number or Text — Flow shows a runtime error, not the friendly message.
- The author writes `IF(condition, TRUE, FALSE)` — works, but is verbose and reads as if validation logic is conditional. Use the boolean expression directly.

### Concept 2 — `isRequired` vs `<validationRule>` (and why both are needed)

`isRequired = true` blocks Next when the input is empty. It does **not** validate format. An empty Email field with `isRequired = true` → blocked. The string `"asdf"` in the same field → allowed (because non-empty), unless a `<validationRule>` also enforces format.

| Need | `isRequired` | `<validationRule>` |
|---|---|---|
| Block empty values | Yes | Optional (formula could check `NOT(ISBLANK(...))`) |
| Block malformed values | No | Yes |
| Block out-of-range values | No | Yes |
| Cross-field check | No | Yes (on the second field) |

Use `isRequired` for required-ness and `<validationRule>` for format. They are complementary, not interchangeable.

### Concept 3 — Re-evaluation timing: Next-click vs reactive

Default behaviour: validation rules evaluate **only when the user clicks Next**. The user can type a malformed value, tab away, and not see an error until they hit Next. This is fine for short forms. For long forms it's bad UX — the user fixes one error, clicks Next, sees the next error, clicks Next, sees the third.

Reactive Screen Components (Winter '24+) re-evaluate validation on each component change. Adopt them when:
- The form has 5+ inputs.
- Inputs depend on each other (cross-field).
- The user benefits from immediate feedback (e.g. password strength, date range).

Reactive validation is opt-in per component; standard input components support it natively, custom LWCs must implement reactivity via `FlowAttributeChangeEvent` and the `@api validate()` hook.

### Concept 4 — Component-level vs screen-level vs record-level

Three tiers, each with a clear scope:

| Tier | Lives in | Scope | Triggers |
|---|---|---|---|
| **Component-level** | `<validationRule>` on the input | Single input (or cross-field on this screen) | Click Next, or live if reactive |
| **Screen-level** | Decision element after the screen | Cross-screen logic (uses prior-screen variables) | When Decision is reached |
| **Record-level** | Validation Rule on the object | Always, regardless of UI | DML (Update Records / Create Records) |

The order of preference is component → screen → record. Component-level catches errors closest to the user, screen-level handles dependencies the input doesn't know about, record-level is the last-resort safety net.

---

## Common Patterns

### Pattern 1 — Per-Input Inline Validation

**When to use:** Standard input field with a single-field constraint (regex, range, length).

**How it works:**

1. Set `isRequired = true` if the field is mandatory.
2. Add `<validationRule>` with a formula returning BOOLEAN.
3. Reference the component value as `{!ComponentApiName}`.
4. Write a user-facing `errorMessage` (no jargon, no formula syntax).

```xml
<validationRule>
    <formulaExpression>AND(
        ISNUMBER({!Age}),
        VALUE({!Age}) &gt;= 18,
        VALUE({!Age}) &lt;= 120
    )</formulaExpression>
    <errorMessage>Age must be a number between 18 and 120.</errorMessage>
</validationRule>
```

**Why not the alternative:** Putting this in a Decision after the screen forces the user to click Next, see a screen-level error message (or worse, a fault path), then click Back. Component-level keeps the error attached to the field that caused it.

### Pattern 2 — Cross-Field on the Second Field

**When to use:** Two fields on the same screen with a relational constraint (`EndDate > StartDate`, `ConfirmEmail = Email`, `Quantity * UnitPrice <= AccountCreditLimit`).

**How it works:**

Put the validation rule on the **second** field (the one whose validity depends on the other). When the user clicks Next, both fields are populated, and the rule sees both values.

```xml
<!-- StartDate field: no cross-field rule needed -->
<fields>
    <name>StartDate</name>
    <dataType>Date</dataType>
    <isRequired>true</isRequired>
</fields>

<!-- EndDate field: rule references both -->
<fields>
    <name>EndDate</name>
    <dataType>Date</dataType>
    <isRequired>true</isRequired>
    <validationRule>
        <formulaExpression>{!EndDate} &gt; {!StartDate}</formulaExpression>
        <errorMessage>End Date must be after Start Date.</errorMessage>
    </validationRule>
</fields>
```

**Why not the alternative:** Putting the rule on `StartDate` doesn't work — when the user is filling in StartDate, EndDate may still be empty, so the rule errors or short-circuits. The rule belongs on the dependent field.

### Pattern 3 — Reactive Validation for Multi-Step Forms

**When to use:** Long forms (5+ fields), or forms where the user benefits from live feedback (password strength, IBAN check, dependent picklists).

**How it works:**

1. Confirm Reactive Screens is enabled (default on Winter '24+ orgs).
2. Use standard reactive input components (Text, Number, Date, etc.).
3. The `<validationRule>` formula is unchanged — Flow re-evaluates it on each change.
4. For a custom LWC, implement `@api validate()` returning `{isValid: boolean, errorMessage: string}` — this is the contract the Flow runtime calls.

```javascript
// custom LWC screen component
import { LightningElement, api } from 'lwc';

export default class IbanInput extends LightningElement {
    @api value;

    @api
    validate() {
        if (!this.value || !this._isValidIban(this.value)) {
            return { isValid: false, errorMessage: 'Enter a valid IBAN.' };
        }
        return { isValid: true };
    }

    _isValidIban(v) { /* check digits */ return true; }
}
```

**Why not the alternative:** Without reactivity, the user types the entire form, clicks Next, then plays whack-a-mole with one error per click.

### Pattern 4 — Screen-Level Decision for Cross-Screen Validation

**When to use:** Validation that needs data from a previous screen (e.g. "the Account Tier picked on Screen 1 limits the Quantity on Screen 2").

**How it works:**

Put a Decision element **after** the second screen with the cross-screen check. If invalid, route back to the second screen via a Loop or via re-rendering the screen with an error variable.

```
[Screen 1: pick Account Tier] → [Screen 2: enter Quantity]
        → [Decision: Quantity within Tier limit?]
              ├── Yes → continue
              └── No  → [Screen 2 again, prepopulated, with error variable shown via display text]
```

This is the **only** legitimate use of Decision-as-validation. Component-level can't do it because the component on Screen 2 doesn't have direct access to the Screen 1 variable in its formula context (it does, but the Decision is clearer and easier to maintain for this case).

---

## Decision Guidance

| Validation shape | Recommended approach | Reason |
|---|---|---|
| Single-field format (email, regex, range) | Component-level `<validationRule>` | Closest to the user, blocks Next inline |
| Field is required | `isRequired = true` (combined with `<validationRule>` for format) | `isRequired` handles emptiness; format is separate |
| Cross-field on same screen (EndDate > StartDate) | `<validationRule>` on the second (dependent) field | Both values are populated when Next is clicked |
| Cross-screen (Quantity limited by Tier picked earlier) | Decision element after the dependent screen, route back on failure | Cross-screen variable scope is clearer in a Decision |
| Live feedback while typing | Reactive Screen Components (Winter '24+) + standard `<validationRule>` | Avoids click-Next-fix-click-Next cycle |
| Custom UI component (e.g. IBAN, postcode lookup) | Custom LWC implementing `@api validate()` | Standard `<validationRule>` doesn't apply to custom LWCs |
| Defence-in-depth against API-level inserts | Object-level Validation Rule (in addition to component-level) | The flow's screen validation isn't run during Apex / API DML |

---

## Recommended Workflow

1. **Inventory inputs per screen.** For each Screen element, list every input component, its type, and whether it's `isRequired`. Save as a table.
2. **Define the validation contract per input.** For each input, write the boolean condition that means "valid" and the user-facing error message. If the condition references another field, note whether that field is on the same screen (cross-field) or earlier (cross-screen).
3. **Translate each contract to `<validationRule>` XML or LWC `@api validate()`.** Use `templates/flow/RecordTriggered_Skeleton.md` style as a reference for XML shape; the formula language is the same as Validation Rules.
4. **Place cross-field rules on the second (dependent) field.** Verify that the formula references both fields with `{!FirstField}` and `{!SecondField}`.
5. **Place cross-screen checks in a Decision after the dependent screen, with a route-back path.** Do not try to cram them into a per-input rule.
6. **Confirm reactivity if relevant.** If the org is on Winter '24+ and the form is long or interdependent, ensure standard reactive components are used; for custom LWCs, confirm they emit `FlowAttributeChangeEvent` and implement `@api validate()`.
7. **Add object-level Validation Rules for defence-in-depth.** Any field the flow writes to should also have a Validation Rule on the object so an Apex / API inserter can't bypass the flow.
8. **Verify accessibility.** Standard input components associate the error message with the field via `aria-describedby` automatically; for custom LWCs, confirm the implementation does the same so screen readers announce the error (see `flow-screen-flow-accessibility`).

---

## Review Checklist

Run through these before marking screen-flow validation work complete:

- [ ] Every required input has `isRequired = true`.
- [ ] Every formatted input has a `<validationRule>` whose formula returns BOOLEAN.
- [ ] No formula uses `IF(cond, TRUE, FALSE)` — the boolean expression is used directly.
- [ ] Every cross-field rule is on the second (dependent) field, not the first.
- [ ] No "validation" Decision element appears immediately after a screen unless it is genuinely cross-screen.
- [ ] Every error message is user-facing prose (no formula syntax, no field API names, no "ERROR_CODE_42").
- [ ] Every custom LWC input implements `@api validate()` returning `{isValid, errorMessage}`.
- [ ] Every field the flow writes to also has a record-level Validation Rule on the object (defence-in-depth).
- [ ] If the org is Winter '24+ and the form is long, reactive components are used.
- [ ] Accessibility: error messages are programmatically associated with the input (standard components handle this; custom LWCs use `aria-describedby`).

---

## Salesforce-Specific Gotchas

1. **The formula must return BOOLEAN, not Text or Number.** A formula returning the error message as text — `IF(LEN({!Email}) > 5, "", "Email too short")` — does not validate; it always returns a string, which is truthy, and Next is allowed regardless. Use `LEN({!Email}) > 5` directly.
2. **`isRequired` does not validate format.** A field marked `isRequired = true` allows the string `" "` (a single space) — non-empty, so the requirement is satisfied. Add a `<validationRule>` like `LEN(TRIM({!Field})) > 0` if you need true non-blank enforcement.
3. **Decision-after-screen is bad UX, not a validation pattern.** When the Decision fires, the user has already clicked Next — the only way back is a manual Back click or a programmatic re-render. Component-level rules block Next inline before the user moves on.
4. **Validation re-evaluates on Next, not in real-time, unless the component is reactive.** Pre–Winter '24 components and non-reactive flows hold all errors until the click. If the user expects live feedback, you need reactive components.
5. **Custom LWC screen components don't inherit `<validationRule>`.** Authors copy-paste a `<validationRule>` element under a custom component's `<extensionName>` block — it is silently ignored. Custom LWCs must implement `@api validate()` returning `{isValid: boolean, errorMessage: string}`; the Flow runtime calls this on Next.
6. **Cross-field rule on the wrong field short-circuits.** Putting `EndDate > StartDate` on the StartDate field means when the user enters StartDate first (with EndDate still null), the formula compares against null and the result is unpredictable. Always put the rule on the dependent (later) field.
7. **Object-level Validation Rules still fire when the flow does Update Records.** A flow's screen validation doesn't replace the object's Validation Rule — both run. If they contradict, the user passes the flow validation and then the object Validation Rule throws, surfacing as a flow runtime error. Keep the two formulas consistent.
8. **Picklist validation must compare against the API name, not the label.** `{!Status} = "Closed Won"` works only if "Closed Won" is the API name. Translated labels in the user's locale won't match. Use the Decision builder's picklist-aware compare or hardcode the API name.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Validated input components | Per-input `<validationRule>` blocks with boolean formula + user-facing error message, plus `isRequired` where applicable. |
| Cross-field rules on the second field | Validation formulas on the dependent field referencing both fields, fired on Next. |
| Screen-level Decision fallback | Decision element after the dependent screen for cross-screen checks, with a route-back-to-screen path on failure. |
| Custom LWC `@api validate()` contracts | For custom screen components, the JS hook returning `{isValid, errorMessage}` plus `FlowAttributeChangeEvent` for reactivity. |
| Defence-in-depth Validation Rules | Object-level Validation Rules covering the same fields, in case an Apex / API inserter bypasses the flow. |

---

## Related Skills

- `flow/flow-screen-flows` — Screen Flow design fundamentals; this skill plugs into the validation step of that workflow.
- `flow/flow-screen-flow-accessibility` — How errors are announced by screen readers; component-level rules + `aria-describedby` are the contract.
- `flow/flow-reactive-screen-components` — Live re-evaluation of validation rules on each component change (Winter '24+).
- `flow/flow-screen-lwc-components` — Building custom LWC screen components, including the `@api validate()` hook.
- `flow/flow-decision-element-patterns` — Decision element shape; relevant for screen-level cross-screen validation only.
- `admin/validation-rules-and-formulas` — Object-level Validation Rules (the defence-in-depth tier under screen validation).

## Official Sources Used

- Salesforce Help — Screen Flow Input Components reference: https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screen_input.htm
- Salesforce Metadata API Developer Guide — Flow type, `<validationRule>` schema on Screen input fields: https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_visual_workflow.htm
- Salesforce Help — Validate Screen Component Input in a Flow: https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_input_validation.htm
- Salesforce Release Notes — Reactive Screen Components (Winter '24): https://help.salesforce.com/s/articleView?id=release-notes.rn_automate_flow_builder_reactive_screens.htm
- Salesforce Developer — Custom LWC Screen Components and the `@api validate()` Contract: https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-screen.html
- WCAG 2.1 Success Criterion 3.3.1 (Error Identification): https://www.w3.org/TR/WCAG21/#error-identification
- Salesforce Architects — Well-Architected Framework (Reliable, Operationally Excellent): https://architect.salesforce.com/well-architected
