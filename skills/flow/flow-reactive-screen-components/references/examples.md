# Examples — Flow Reactive Screen Components

## Example 1: Live total

**Context:** Order quantity * price

**Problem:** User had to click Next to see total

**Solution:**

Formula `Quantity * Price`; display component references formula

**Why it works:** Instant feedback


---

## Example 2: Show/hide state field

**Context:** Country → State dependent

**Problem:** State always visible

**Solution:**

Visibility rule `{!Country.value} == 'US'`

**Why it works:** Clean progressive disclosure

