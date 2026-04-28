# Examples — Flow Screen Input Validation Patterns

Concrete examples of `<validationRule>` formulas and the corresponding component XML for the most common screen-flow input validation cases. All formulas return BOOLEAN — `TRUE` allows Next, `FALSE` blocks Next and shows the error message inline.

---

## Example 1: Email format validation (single-field)

**Context:** A lead capture screen flow asks for an Email input. The field is required and must look like a real email address before the user proceeds.

**Problem:** Without a `<validationRule>`, the user can type `asdf` and click Next; the bad email is then written to the Lead record. `isRequired = true` blocks empty strings but not `asdf`.

**Solution:**

```xml
<fields>
    <name>Email</name>
    <dataType>String</dataType>
    <fieldType>InputField</fieldType>
    <isRequired>true</isRequired>
    <fieldText>Email Address</fieldText>
    <validationRule>
        <formulaExpression>AND(
            LEN({!Email}) &gt; 5,
            CONTAINS({!Email}, "@"),
            CONTAINS({!Email}, "."),
            NOT(BEGINS({!Email}, "@")),
            NOT(ENDS({!Email}, "@"))
        )</formulaExpression>
        <errorMessage>Enter a valid email address.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** `AND(...)` returns boolean — the four sub-conditions cover length, presence of `@`, presence of `.`, and non-degenerate `@` placement. Inline at the field, fired on Next.

---

## Example 2: Phone number validation (regex)

**Context:** A service-request screen captures a Phone input. The org accepts E.164 format (+ followed by 10–15 digits).

**Problem:** Free-text phone numbers come in dozens of formats — `(415) 555-1212`, `+1 415 555 1212`, `4155551212`, etc. — and downstream systems reject anything not E.164.

**Solution:**

```xml
<fields>
    <name>Phone</name>
    <dataType>String</dataType>
    <fieldType>InputField</fieldType>
    <isRequired>true</isRequired>
    <validationRule>
        <formulaExpression>REGEX({!Phone}, "^\\+?[0-9]{10,15}$")</formulaExpression>
        <errorMessage>Enter a phone number in E.164 format: + followed by 10 to 15 digits.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** `REGEX(text, pattern)` returns BOOLEAN. The pattern `^\+?[0-9]{10,15}$` allows an optional `+` then 10–15 digits anchored to start and end of string.

---

## Example 3: Age range with type-safety

**Context:** Onboarding flow captures Age. Must be a positive integer between 18 and 120.

**Problem:** A Number input may be empty (null), and `VALUE()` on a null/non-numeric throws.

**Solution:**

```xml
<fields>
    <name>Age</name>
    <dataType>Number</dataType>
    <isRequired>true</isRequired>
    <scale>0</scale>
    <validationRule>
        <formulaExpression>AND(
            NOT(ISNULL({!Age})),
            {!Age} &gt;= 18,
            {!Age} &lt;= 120
        )</formulaExpression>
        <errorMessage>Age must be between 18 and 120.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** Number-typed components return a Number resource directly — no `VALUE()` cast needed. The `NOT(ISNULL(...))` guard prevents null comparisons returning unpredictably.

---

## Example 4: Cross-field — End Date after Start Date

**Context:** A booking screen has StartDate and EndDate inputs. EndDate must be strictly later than StartDate.

**Problem:** If the rule is on StartDate, EndDate is null when the user is filling StartDate, so the comparison short-circuits incorrectly. The rule must live on the *dependent* field.

**Solution:**

```xml
<!-- StartDate field: no cross-field rule -->
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
        <formulaExpression>AND(
            NOT(ISNULL({!StartDate})),
            NOT(ISNULL({!EndDate})),
            {!EndDate} &gt; {!StartDate}
        )</formulaExpression>
        <errorMessage>End Date must be after Start Date.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** When the user clicks Next, both fields are populated. The rule on the second field sees both values and the comparison is well-defined.

---

## Example 5: Cross-field — Confirm Email matches Email

**Context:** A registration screen requires the user to type their email twice to catch typos.

**Problem:** Same as Example 4 — the rule belongs on the second (Confirm) field, not the first.

**Solution:**

```xml
<fields>
    <name>Email</name>
    <dataType>String</dataType>
    <isRequired>true</isRequired>
</fields>

<fields>
    <name>ConfirmEmail</name>
    <dataType>String</dataType>
    <isRequired>true</isRequired>
    <validationRule>
        <formulaExpression>{!ConfirmEmail} = {!Email}</formulaExpression>
        <errorMessage>The two email addresses must match.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** Direct boolean comparison; both fields populated at Next.

---

## Example 6: Conditional requirement — Phone required only when ContactMethod = "Phone"

**Context:** A contact preferences screen has a ContactMethod picklist (Email / Phone / SMS) and a Phone input. Phone is required only when ContactMethod = "Phone" or "SMS".

**Problem:** `isRequired = true` is unconditional. We need conditional requiredness.

**Solution:** Leave `isRequired = false` and enforce in the validation rule:

```xml
<fields>
    <name>Phone</name>
    <dataType>String</dataType>
    <isRequired>false</isRequired>
    <validationRule>
        <formulaExpression>OR(
            NOT(OR({!ContactMethod} = "Phone", {!ContactMethod} = "SMS")),
            AND(
                NOT(ISBLANK({!Phone})),
                REGEX({!Phone}, "^\\+?[0-9]{10,15}$")
            )
        )</formulaExpression>
        <errorMessage>Phone is required and must be in E.164 format when contact method is Phone or SMS.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** The outer `OR` says "valid if either (a) the trigger condition isn't met, or (b) the trigger is met AND the field is filled in correctly". This is the canonical conditional-required pattern.

---

## Example 7: Picklist must be one of an allowed subset

**Context:** A Stage picklist on a renewal screen offers seven values, but only three are valid for renewals (the other four are for new business).

**Problem:** You can't dynamically filter the picklist values from XML; instead, validate that the chosen value is in the allowed subset.

**Solution:**

```xml
<fields>
    <name>RenewalStage</name>
    <dataType>String</dataType>
    <fieldType>DropdownBox</fieldType>
    <isRequired>true</isRequired>
    <validationRule>
        <formulaExpression>OR(
            {!RenewalStage} = "Renewing",
            {!RenewalStage} = "Negotiating",
            {!RenewalStage} = "Closed Won"
        )</formulaExpression>
        <errorMessage>Select a renewal-eligible stage.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** API names (not labels). If the org is multilingual, labels translate but API names don't.

---

## Example 8: Numeric range with currency-aware comparison

**Context:** A pricing screen lets the user enter a Discount percentage; allowed range is 0–35.

**Solution:**

```xml
<fields>
    <name>Discount</name>
    <dataType>Number</dataType>
    <scale>2</scale>
    <isRequired>true</isRequired>
    <validationRule>
        <formulaExpression>AND(
            NOT(ISNULL({!Discount})),
            {!Discount} &gt;= 0,
            {!Discount} &lt;= 35
        )</formulaExpression>
        <errorMessage>Discount must be between 0% and 35%.</errorMessage>
    </validationRule>
</fields>
```

---

## Example 9: Long text minimum length (free-text justification)

**Context:** An expense-approval flow requires the user to enter a justification with at least 30 non-whitespace characters.

**Solution:**

```xml
<fields>
    <name>Justification</name>
    <dataType>String</dataType>
    <fieldType>LargeTextArea</fieldType>
    <isRequired>true</isRequired>
    <validationRule>
        <formulaExpression>LEN(TRIM({!Justification})) &gt;= 30</formulaExpression>
        <errorMessage>Justification must be at least 30 characters.</errorMessage>
    </validationRule>
</fields>
```

**Why it works:** `TRIM()` strips leading/trailing whitespace so a string of 30 spaces doesn't satisfy the rule.

---

## Example 10: Reactive validation with a custom LWC (IBAN check)

**Context:** A bank-account capture screen needs to validate an IBAN string. The validation requires modulus arithmetic that the formula language can't easily express, so a custom LWC is used.

**Solution:** The custom LWC implements `@api validate()` and emits `FlowAttributeChangeEvent` for reactivity.

```javascript
// force-app/main/default/lwc/ibanInput/ibanInput.js
import { LightningElement, api } from 'lwc';
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

export default class IbanInput extends LightningElement {
    @api value;

    handleChange(event) {
        this.value = event.target.value;
        // emit so reactive screens see the new value
        this.dispatchEvent(new FlowAttributeChangeEvent('value', this.value));
    }

    @api
    validate() {
        if (!this.value || this.value.length < 15) {
            return { isValid: false, errorMessage: 'IBAN is required.' };
        }
        if (!this._isValidIban(this.value)) {
            return { isValid: false, errorMessage: 'IBAN failed mod-97 check.' };
        }
        return { isValid: true };
    }

    _isValidIban(iban) {
        // rearrange: move first 4 chars to end, replace letters A-Z with 10-35
        const rearranged = iban.slice(4) + iban.slice(0, 4);
        const numeric = rearranged.replace(/[A-Z]/g, ch => ch.charCodeAt(0) - 55);
        // mod 97 must equal 1
        let remainder = 0;
        for (const digit of numeric) {
            remainder = (remainder * 10 + parseInt(digit, 10)) % 97;
        }
        return remainder === 1;
    }
}
```

```xml
<!-- ibanInput.js-meta.xml -->
<?xml version="1.0" encoding="UTF-8"?>
<LightningComponentBundle xmlns="http://soap.sforce.com/2006/04/metadata">
    <apiVersion>62.0</apiVersion>
    <isExposed>true</isExposed>
    <targets>
        <target>lightning__FlowScreen</target>
    </targets>
    <targetConfigs>
        <targetConfig targets="lightning__FlowScreen">
            <property name="value" type="String" role="inputOutput" />
        </targetConfig>
    </targetConfigs>
</LightningComponentBundle>
```

**Why it works:** The Flow runtime calls `validate()` on Next; if it returns `{isValid: false}`, Flow blocks navigation and renders `errorMessage` under the component. `FlowAttributeChangeEvent` is what makes the component reactive — without it, dependent components don't update.

---

## Anti-Pattern A: Validation in a Decision after the screen

**What practitioners do:** Add a Decision element directly after a screen with the input, branching on whether the input is valid; the "invalid" branch routes back to the same screen via a label.

```
[Screen: Email] → [Decision: Email contains @?]
                       ├── Yes → continue
                       └── No  → [Screen: Email] (loop back)
```

**What goes wrong:**
- The user has already clicked Next — the experience is "click Next, screen flickers, error appears as a banner, click Next again". Compare to component-level: the user types, clicks Next, sees the error attached to the field, fixes it, clicks Next once.
- The error message lives in a Display Text component or a fault path, not under the field — accessibility tools can't associate it with the input.
- Maintaining the loop-back is brittle; deleting or renaming the screen breaks the Decision.

**Correct approach:** Move the check to a `<validationRule>` on the Email component. The Decision is appropriate only when the validation needs data from a *prior* screen (cross-screen validation, Pattern 4 in SKILL.md).

---

## Anti-Pattern B: Returning a string instead of boolean

**What practitioners do:** Write `IF(LEN({!Email}) > 5, "", "Email too short")` thinking the empty string means "valid".

**What goes wrong:** Both branches return Text, not Boolean. Flow accepts the formula at design time but at runtime the truthiness of a non-empty string allows Next regardless of the actual input. Worse, the empty string sometimes coerces and worse-still some org versions show a runtime error.

**Correct approach:** Return BOOLEAN directly: `LEN({!Email}) > 5`. Put the user-facing string in `<errorMessage>`, not in the formula.

---

## Anti-Pattern C: Cross-field rule on the wrong field

**What practitioners do:** Put `EndDate > StartDate` on the StartDate component, "because StartDate is the one being entered first".

**What goes wrong:** When StartDate is being filled, EndDate is null. The comparison `null > date` is unpredictable — sometimes Flow evaluates to false (blocking), sometimes to a runtime error. The rule belongs on the dependent (later) field where both values are populated by Next-click time.

**Correct approach:** See Example 4 — rule on EndDate, referencing both `{!StartDate}` and `{!EndDate}` with `NOT(ISNULL(...))` guards.
