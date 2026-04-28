# LLM Anti-Patterns — Flow Screen Input Validation Patterns

Common mistakes AI coding assistants make when generating or advising on Flow screen-flow input validation. Use this list to self-check generated output before returning it.

---

## Anti-Pattern 1: Putting validation in a Decision element after the screen

**What the LLM generates:** A flow XML / design with a screen capturing input, immediately followed by a Decision element checking the input and looping back to the screen on failure.

```xml
<screens><name>EmailScreen</name>...</screens>
<decisions>
    <name>ValidateEmail</name>
    <rules>
        <conditions>
            <leftValueReference>EmailScreen.Email</leftValueReference>
            <operator>Contains</operator>
            <rightValue><stringValue>@</stringValue></rightValue>
        </conditions>
        <connector><targetReference>NextScreen</targetReference></connector>
    </rules>
    <defaultConnector><targetReference>EmailScreen</targetReference></defaultConnector>
</decisions>
```

**Why it happens:** LLMs trained on traditional server-side validation patterns (PHP, Rails, classic servlets) default to "validate after submit" thinking. Decision elements are also more visually prominent in flow design materials, so the model reaches for them first.

**Correct pattern:**

```xml
<screens>
    <name>EmailScreen</name>
    <fields>
        <name>Email</name>
        <isRequired>true</isRequired>
        <validationRule>
            <formulaExpression>AND(LEN({!Email}) &gt; 5, CONTAINS({!Email}, "@"))</formulaExpression>
            <errorMessage>Enter a valid email address.</errorMessage>
        </validationRule>
    </fields>
</screens>
```

**Detection hint:** Look for a `<decisions>` element immediately after a `<screens>` element where the conditions reference variables defined on that screen, and the default connector loops back to the same screen. That's the anti-pattern signature.

---

## Anti-Pattern 2: Validation formula returning a string instead of BOOLEAN

**What the LLM generates:** A formula that returns the error message string conditionally, thinking the empty string means "valid".

```
IF(LEN({!Email}) > 5, "", "Email is too short")
```

**Why it happens:** Familiarity with form-validation libraries (e.g. Formik, React Hook Form, Yup) where the validator returns the error string or `null`/`undefined`. The model ports that mental model to Salesforce formulas without checking the contract.

**Correct pattern:**

```
LEN({!Email}) > 5
```

The error string belongs in `<errorMessage>`, not in the formula. The formula returns BOOLEAN.

**Detection hint:** Search the formula for `IF(`. If either branch of the IF is a string literal, the formula likely returns Text instead of Boolean. Also flag any formula containing `"Error"`, `"Invalid"`, `"must be"`, or other user-facing prose — that text belongs in the error message element.

---

## Anti-Pattern 3: Using `IF(condition, TRUE, FALSE)` instead of the boolean expression directly

**What the LLM generates:** A formula wrapping a clearly boolean expression in an `IF(...)`:

```
IF(LEN({!Email}) > 5, TRUE, FALSE)
```

**Why it happens:** Models trained on imperative-language idioms wrap conditions in if-statements out of habit. It's syntactically valid but reads as if the validation logic is conditional on something else, and adds noise.

**Correct pattern:**

```
LEN({!Email}) > 5
```

The expression is already a boolean. Wrapping it in `IF(_, TRUE, FALSE)` is redundant.

**Detection hint:** Regex `IF\s*\(.*,\s*TRUE\s*,\s*FALSE\s*\)` or `IF\s*\(.*,\s*FALSE\s*,\s*TRUE\s*\)`. Flag and rewrite to the bare expression (or its negation).

---

## Anti-Pattern 4: Suggesting `<validationRule>` on a custom LWC without explaining the `@api validate()` contract

**What the LLM generates:** A custom LWC screen component XML with a `<validationRule>` element copy-pasted under the `<extensionName>` block, as if standard input validation applies.

```xml
<fields>
    <name>IbanInput</name>
    <extensionName>c:ibanInput</extensionName>
    <validationRule>  <!-- silently ignored -->
        <formulaExpression>LEN({!IbanInput}) > 15</formulaExpression>
        <errorMessage>IBAN too short.</errorMessage>
    </validationRule>
</fields>
```

**Why it happens:** The `<validationRule>` element looks like a generic schema attribute and the model assumes it applies to all input components. The reality — that custom LWCs honour only the `@api validate()` JS hook — is a specific platform fact often missing or buried in training data.

**Correct pattern:** Implement validation in the LWC's JavaScript:

```javascript
import { LightningElement, api } from 'lwc';

export default class IbanInput extends LightningElement {
    @api value;

    @api
    validate() {
        if (!this.value || this.value.length < 15) {
            return { isValid: false, errorMessage: 'IBAN must be at least 15 characters.' };
        }
        return { isValid: true };
    }
}
```

The Flow runtime calls `validate()` on Next; returning `{isValid: false}` blocks navigation and renders the message.

**Detection hint:** Look for `<extensionName>c:...</extensionName>` followed by `<validationRule>...</validationRule>` in the same `<fields>` block. That's the anti-pattern. The fix: remove the `<validationRule>`, add an `@api validate()` method to the LWC.

---

## Anti-Pattern 5: Omitting the accessibility consideration for error message announcement

**What the LLM generates:** A custom LWC implementation that renders the error message in a plain `<div>` next to the input, with no ARIA association:

```html
<template>
    <input type="text" value={value} oninput={handleChange} />
    <div if:true={errorMessage}>{errorMessage}</div>
</template>
```

**Why it happens:** Models generate visually correct UIs by default; ARIA attributes are an extra step that's often skipped unless explicitly requested. The model treats accessibility as a separate "polish" concern rather than a baseline requirement.

**Correct pattern:** Use `<lightning-input>` (which handles ARIA automatically) or manually associate the error with `aria-describedby`:

```html
<template>
    <lightning-input
        value={value}
        message-when-pattern-mismatch={errorMessage}>
    </lightning-input>
</template>
```

Or, with a raw input:

```html
<template>
    <input
        type="text"
        value={value}
        aria-describedby="error-message"
        aria-invalid={hasError} />
    <div id="error-message" role="alert">{errorMessage}</div>
</template>
```

**Detection hint:** In any custom LWC screen component output, check for `aria-describedby` and `role="alert"`. Their absence with an error-rendering div nearby is the anti-pattern. Also flag raw `<input>` instead of `<lightning-input>` — the latter handles ARIA for you.

---

## Anti-Pattern 6: Cross-field validation rule placed on the wrong (first) field

**What the LLM generates:** A flow with `EndDate > StartDate` placed on the StartDate component rather than EndDate.

```xml
<fields>
    <name>StartDate</name>
    <validationRule>
        <formulaExpression>{!EndDate} &gt; {!StartDate}</formulaExpression>  <!-- wrong field -->
        <errorMessage>End Date must be after Start Date.</errorMessage>
    </validationRule>
</fields>
<fields><name>EndDate</name></fields>
```

**Why it happens:** Models default to "validate the first field" because that's the order the human is filling them in. They don't reason about which field is the dependent one.

**Correct pattern:** Cross-field rule on the *dependent* (second) field:

```xml
<fields><name>StartDate</name></fields>
<fields>
    <name>EndDate</name>
    <validationRule>
        <formulaExpression>AND(NOT(ISNULL({!StartDate})), NOT(ISNULL({!EndDate})), {!EndDate} &gt; {!StartDate})</formulaExpression>
        <errorMessage>End Date must be after Start Date.</errorMessage>
    </validationRule>
</fields>
```

**Detection hint:** For any cross-field formula referencing two field variables `{!A}` and `{!B}`, identify which field the rule lives under. If it lives under the field appearing later in the formula's logical order (e.g. the formula compares `B > A` but the rule is on `A`), that's the anti-pattern.

---

## Anti-Pattern 7: Hardcoded error message strings in a multilingual org

**What the LLM generates:** Error messages hardcoded in English without using Custom Labels:

```xml
<errorMessage>End Date must be after Start Date.</errorMessage>
```

**Why it happens:** Most training examples are English-only. Localization is rarely shown alongside validation examples.

**Correct pattern:** Reference a Custom Label so the message localizes per user:

```xml
<errorMessage>{!$Label.EndDateAfterStartDateError}</errorMessage>
```

**Detection hint:** Hardcoded English-text `<errorMessage>` elements in any flow targeting a multilingual org. Recommend wrapping in a Custom Label.

---

## Anti-Pattern 8: Using JavaScript regex syntax in `REGEX()`

**What the LLM generates:** A `REGEX()` call with leading/trailing slashes (JS style) or with single backslashes for escapes:

```
REGEX({!Phone}, "/^\+?[0-9]{10,15}$/")
```

or

```
REGEX({!Phone}, "^\+?[0-9]{10,15}$")  <!-- single backslash, may not work in XML -->
```

**Why it happens:** JavaScript regex is the most common pattern in training data; the model uses its syntax by default.

**Correct pattern:** Salesforce `REGEX()` uses Java regex syntax — no leading/trailing slashes, and double-escape backslashes when in XML metadata files:

```
REGEX({!Phone}, "^\\+?[0-9]{10,15}$")
```

**Detection hint:** Search for `REGEX\(.*"/.*/"` (leading slash) or single-backslash escapes in XML contexts. Recommend stripping slashes and double-escaping.
