# Gotchas — Flow Screen Input Validation Patterns

Non-obvious Salesforce platform behaviours that cause real production problems when validating screen-flow inputs.

---

## Gotcha 1: The formula must return BOOLEAN — anything else fails silently or breaks at runtime

**What happens:** A `<validationRule>` whose `<formulaExpression>` returns a string, number, or null does not behave as the author expects. In some org versions Flow accepts the metadata at design time but the validation never blocks Next; in other versions the user sees a runtime error like `"Validation rule formula returned an invalid type"`.

**When it occurs:** Authors who think of validation as "if invalid, return the message" write `IF(LEN({!Email}) > 5, "", "Too short")` — both branches return Text. The same mistake appears with `IF(cond, 1, 0)` (Number) or `IF(cond, NULL, "Too short")`.

**How to avoid:** Always return BOOLEAN directly. The expression `LEN({!Email}) > 5` is the entire formula. The user-facing string lives in `<errorMessage>`, never inside the formula. A useful test: if your formula contains `IF(...)` and one branch returns a string, it is wrong.

---

## Gotcha 2: `isRequired` does not validate format — only emptiness

**What happens:** A field marked `isRequired = true` accepts the string `" "` (a single space) — it is non-empty, so the requirement is satisfied. The user can also enter `asdf` in an Email field marked `isRequired = true` — non-empty, allowed.

**When it occurs:** Authors think `isRequired` means "must contain a valid value". It only means "must contain *some* value".

**How to avoid:** Combine `isRequired = true` with a `<validationRule>` that enforces format. For non-blank enforcement, use `LEN(TRIM({!Field})) > 0`. For email, see `examples.md` Example 1. The two attributes are orthogonal — required-ness vs format — and you almost always need both.

---

## Gotcha 3: Decision-after-screen is not "validation" — the user has already moved on

**What happens:** Author places a Decision element immediately after a screen, branches on a condition derived from the screen's inputs, and routes the "invalid" branch back to the same screen. The user clicks Next, the screen flickers, an error appears (often as a banner or a Display Text on the re-rendered screen), and they click Next again.

**When it occurs:** Authors port a server-side validation mindset (validate after submit, render errors) into Screen Flow design. It works mechanically but is bad UX, breaks accessibility, and makes the error message detached from the field.

**How to avoid:** Use `<validationRule>` on the input component itself. The only legitimate post-screen Decision validation is for cross-screen checks where the rule needs data from an earlier screen (see SKILL.md Pattern 4).

---

## Gotcha 4: Validation re-evaluates on Next, not in real time — unless the component is reactive

**What happens:** The user types `asdf` into Email, tabs away to the next field, types something there, returns to Email — no error appears. The error appears only when they click Next. For long forms this is a frustrating cycle: fix one error, click Next, see the next, click Next, see a third.

**When it occurs:** Pre-Winter '24 orgs, or non-reactive components (some custom LWCs, some legacy components). Even on Winter '24+, components must be explicitly reactive — standard inputs are reactive by default; custom LWCs must implement `FlowAttributeChangeEvent` and `@api validate()`.

**How to avoid:** For long forms (5+ inputs) or interdependent inputs, use reactive Screen Components. For custom LWCs, implement reactivity (see `examples.md` Example 10). Document in the design that validation is Next-time evaluated unless explicitly reactive.

---

## Gotcha 5: Custom LWC screen components do not honour `<validationRule>`

**What happens:** Author copy-pastes a `<validationRule>` block under a custom LWC's `<extensionName>` element in the flow XML. The metadata saves without error. At runtime the rule is silently ignored — Next is allowed regardless of the formula's value.

**When it occurs:** Any time a custom LWC is used as a screen input. The `<validationRule>` schema applies to standard input field types (`<fields>` elements with a `<dataType>`), not to custom screen extensions.

**How to avoid:** Custom LWCs must implement the `@api validate()` contract:

```javascript
@api
validate() {
    if (/* invalid */) {
        return { isValid: false, errorMessage: 'Friendly message here.' };
    }
    return { isValid: true };
}
```

The Flow runtime calls `validate()` on Next; returning `{isValid: false}` blocks navigation and renders the error message under the component. This is the only validation contract custom LWCs honour.

---

## Gotcha 6: Cross-field rules on the wrong (first) field short-circuit

**What happens:** Author places `EndDate > StartDate` on the StartDate component. When the user is filling StartDate first, EndDate is null. The comparison `date > null` is unpredictable — the rule may evaluate to false (blocking the user immediately, before they have a chance to enter EndDate) or throw a runtime error.

**When it occurs:** Whenever a cross-field rule is on the first (independent) field instead of the second (dependent) field.

**How to avoid:** Always put cross-field rules on the dependent field. Add `NOT(ISNULL(...))` guards in the formula so partial entry doesn't break it. See `examples.md` Example 4.

---

## Gotcha 7: Object-level Validation Rules still fire on Update Records — even when the flow validation passes

**What happens:** The flow's screen validation accepts the input. The flow's Update Records / Create Records element runs. The object's record-level Validation Rule rejects the record. The user sees a flow runtime error (often unhelpful) — the message is the Validation Rule's, not the screen's.

**When it occurs:** When the flow validates `Discount <= 35` but the object's Validation Rule says `Discount <= 25` (different threshold). Or when the Validation Rule references fields that the flow doesn't populate.

**How to avoid:** Keep flow validation and object Validation Rules consistent. When a flow writes to a field, audit the field's record-level Validation Rules and ensure the screen formula is at least as strict. Treat the object Validation Rule as the authority and the screen rule as a UX wrapper.

---

## Gotcha 8: Picklist comparison must use API name, not label

**What happens:** Author writes `{!Status} = "Closed Won"` thinking it compares against the displayed text. In a multilingual org, the user sees "Cerrado Ganado" or "成约" but the variable holds the API name "Closed_Won" — the equality fails for everyone whose locale isn't English.

**When it occurs:** Any picklist used in a `<validationRule>` formula on a multilingual org, or any org where labels diverge from API names.

**How to avoid:** Always compare against the API name (the developer-facing value). The Flow Builder picklist editor shows the API name when you click "View API Name". Hardcode the API name in formulas, never the label.

---

## Gotcha 9: `REGEX()` syntax differs subtly from JavaScript regex

**What happens:** Author copy-pastes a JS regex like `/^\+?[0-9]{10,15}$/` into a `REGEX()` formula. It either fails to compile (the leading `/` is invalid) or doesn't match what the JS version matches.

**When it occurs:** Any time a regex is used in a `<validationRule>`. Flow's `REGEX()` uses Java regex syntax, no leading/trailing `/`, and backslashes must be escaped *twice* in some contexts (XML metadata file vs Flow Builder UI).

**How to avoid:** Strip the leading/trailing `/`. In XML metadata, escape backslashes as `\\` (so a literal `\d` in the regex is `\\\\d` in XML). Test the regex in Flow Builder's formula editor (which shows live errors) before promoting to deployment.

---

## Gotcha 10: Reactive validation triggers cause perceived lag with heavy formulas

**What happens:** The screen has 10 reactive inputs, each with a `<validationRule>` that calls `REGEX()` against a long string. Every keystroke re-evaluates all rules. The user perceives lag, especially on mobile.

**When it occurs:** Reactive screens with many components and complex formulas. Worse on mobile devices (slower JS engine).

**How to avoid:** For heavy validation (regex, multi-condition AND), make the component non-reactive (validation only on Next). Reserve reactive validation for cheap checks (length, range). Don't put `REGEX()` against a 10 KB string in a reactive rule.

---

## Gotcha 11: Standard error message rendering does not translate via Custom Labels by default

**What happens:** Author hardcodes `<errorMessage>End Date must be after Start Date.</errorMessage>` in English. In a French-locale org, French users see English error text.

**When it occurs:** Any multilingual org. The error message string is not automatically wrapped in a translation lookup.

**How to avoid:** Use a Custom Label resource and reference it via `{!$Label.EndDateAfterStartDate}` in the `<errorMessage>` element (where supported). For older API versions where this doesn't work, route validation through a Decision that selects the right localized string and surfaces it via Display Text — heavier, but the only way to localize.

---

## Gotcha 12: Accessibility — error messages must be programmatically associated with the input

**What happens:** A custom LWC renders an error message in a `<div>` next to the input. Sighted users see the error; screen-reader users don't — the error is not announced because it isn't associated with the input via `aria-describedby`.

**When it occurs:** Custom LWC screen components that render error text without proper ARIA attributes. Standard Salesforce input components handle this automatically.

**How to avoid:** In custom LWCs, use `<lightning-input>` (which handles the association via `message-when-pattern-mismatch` and friends) or manually set `aria-describedby="error-message-id"` on the input and render the error in `<div id="error-message-id" role="alert">`. See `flow-screen-flow-accessibility` for full WCAG 2.1 SC 3.3.1 compliance.
