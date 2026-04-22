# LLM Anti-Patterns — LWC Record Picker

Common mistakes AI coding assistants make with lightning-record-picker.

## Anti-Pattern 1: Building a custom combobox lookup

**What the LLM generates:** Custom LWC with `lightning-combobox` + Apex search + styled dropdown.

**Why it happens:** Model's training data predates the GA of lightning-record-picker.

**Correct pattern:**

```
<lightning-record-picker
    label="Account"
    object-api-name="Account"
    onchange={handleChange}>
</lightning-record-picker>

Base component: searchable, paginated, keyboard-accessible, SLDS-styled.
Building your own duplicates 200 lines with worse a11y.
```

**Detection hint:** LWC component matching pattern `*lookup*.js` combining lightning-combobox + Apex @wire search.

---

## Anti-Pattern 2: Omitting matching-info for custom search fields

**What the LLM generates:** `display-info` with multiple fields; no `matching-info`.

**Why it happens:** Model assumes display fields automatically search.

**Correct pattern:**

```
matching-info explicitly declares search fields. Without it, only the
primary field matches. Mirror display fields in matching-info:

matchingInfo = {
    primaryField: { fieldPath: 'Name' },
    additionalFields: [{ fieldPath: 'Email' }]
};

Otherwise users typing an email address find nothing.
```

**Detection hint:** Picker markup with custom `display-info` additionalFields but no `matching-info` binding.

---

## Anti-Pattern 3: Building a multi-select picker from the single-select base

**What the LLM generates:** Repeated `<lightning-record-picker>` instances, state kept in an array.

**Why it happens:** Model stretches the base to fit.

**Correct pattern:**

```
lightning-record-picker is single-select only. For multi-select:
- Use lightning-record-picker for selection → push to a pill list
  rendered via lightning-pill-container
- Or build a custom combobox wrapping the picker

Don't repeat the picker N times — state sync becomes fragile and a11y
is worse than one proper component.
```

**Detection hint:** `<template for:each>` iterating over `<lightning-record-picker>` instances.

---

## Anti-Pattern 4: Using filter as a security gate

**What the LLM generates:** `filter={hideSensitiveAccounts}` assuming the user cannot see filtered-out records.

**Why it happens:** Model conflates UI filter with security.

**Correct pattern:**

```
The filter is a UX convenience, not a security boundary. A
determined user can bypass by using Global Search or SOQL from a
report. For actual security, use Sharing Rules, Apex managed
sharing, or restriction rules.
```

**Detection hint:** Comment or PR notes treating the `filter` prop as enforcement.

---

## Anti-Pattern 5: Preselecting without setting display-info

**What the LLM generates:** Sets `value={preselectedId}` but leaves display-info default.

**Why it happens:** Model forgets preselection render requirements.

**Correct pattern:**

```
For preselection to render correctly, display-info must define the
primaryField the picker should show for the preselected record.
Without it, the chip may show the Id or blank.

displayInfo = { primaryField: 'Name' };
```

**Detection hint:** Picker with `value` bound but no `display-info`.
