# Gotchas: Formula Fields

---

## Formula Fields Do Not Preserve History

**What happens:** A business user expects a formula to show the value that was true when the record was closed. Instead, it keeps recalculating based on current parent data and "rewrites history."

**When it bites you:** Closed-won metrics, renewal snapshots, compliance indicators, and lifecycle milestones.

**How to avoid it:** If history matters, store the value in a real field via Flow or Apex at the right lifecycle moment.

**Example:**
```text
Bad fit: Renewal_Risk_Snapshot__c as a formula
Better fit: Renewal_Risk_Snapshot__c populated when Stage changes to Closed Won
```

---

## Cross-Object Convenience Becomes Reporting Debt

**What happens:** A few helpful parent references turn into a network of chained formulas across Account, Contact, Opportunity, and custom objects. Reports become harder to understand and slower to evolve.

**When it bites you:** Mature orgs with years of admin-added helper formulas.

**How to avoid it:** Keep cross-object formulas intentional, shallow, and documented. Move heavy logic to stored fields when usage grows.

**Example:**
```text
Acceptable: Contact -> Account.Owner.Name
Risky: Child -> Parent -> Grandparent -> Great-grandparent decision logic
```

---

## Blank Handling Depends on Field Type

**What happens:** Admins assume blank text, zero numbers, and unchecked checkboxes all behave the same. The formula returns unexpected values.

**When it bites you:** Discount math, scoring, compliance flags, and display labels.

**How to avoid it:** Test each field type explicitly and handle `0`, null, and empty text deliberately.

**Example:**
```text
Revenue__c = 0 is not the same business meaning as Revenue__c being blank
```

---

## Decorative Functions Get Overused

**What happens:** `IMAGE()` and `HYPERLINK()` start as helpful UI enhancements, then become critical to understanding business state. Mobile, reports, and downstream users do not always consume them cleanly.

**When it bites you:** Executive dashboards, integrations, and large report exports.

**How to avoid it:** Keep the underlying business value in a plain formula or real field, and make the decorative formula secondary.

**Example:**
```text
Store Status__c = "At Risk"
Optionally show Risk_Icon__c with IMAGE() for page UX
```
