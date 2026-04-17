# Examples — LWC Internationalization

## Example 1: Hardcoded strings audit

**Context:** New component 'Save' label

**Problem:** Non-English users saw English

**Solution:**

Custom Label `c.Action_Save` with translations

**Why it works:** One place to update per locale


---

## Example 2: Locale-aware number

**Context:** Currency display

**Problem:** Hard-coded $ didn't work in EU

**Solution:**

`<lightning-formatted-number format-style="currency" currency-code="EUR">`

**Why it works:** Platform handles locale separators

