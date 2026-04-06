# LLM Anti-Patterns — Custom Field Creation

Common mistakes AI coding assistants make when generating or advising on Salesforce custom field creation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Skipping Field-Level Security after field creation

**What the LLM generates:** "Create the custom field on Account. Users will now be able to see and edit it."

**Why it happens:** LLMs focus on field creation and assume the field is immediately visible. In Salesforce, a new custom field is not visible to users unless Field-Level Security (FLS) is explicitly granted on profiles or permission sets AND the field is added to the page layout. Creating the field is only the first step.

**Correct pattern:**

```
After creating the custom field:
1. Set Field-Level Security:
   - Setup → Object Manager → [Object] → Fields → [Field] → Set Field-Level Security.
   - Grant "Visible" (and optionally "Read-Only") per profile.
   - Or add the field to a Permission Set with the appropriate FLS.
2. Add the field to page layouts:
   - During field creation, check "Add to all page layouts" if appropriate.
   - Or manually add to specific page layouts via Page Layout editor.
3. Verify: log in as a test user with the target profile to confirm visibility.
```

**Detection hint:** If the output creates a field without a subsequent FLS configuration step, users may not see the field. Search for `Field-Level Security` or `FLS` or `Set Field-Level Security` after the creation step.

---

## Anti-Pattern 2: Recommending Text fields when a more specific type exists

**What the LLM generates:** "Create a Text field to store the customer's phone number."

**Why it happens:** LLMs default to Text as a safe catch-all. Salesforce provides specific field types (Phone, Email, URL, Date, Currency, Number) that enable built-in formatting, validation, click-to-dial, and reporting features. Using Text for structured data loses these platform capabilities.

**Correct pattern:**

```
Choose the most specific field type:
- Phone numbers → Phone field type (enables click-to-dial in Lightning).
- Email addresses → Email field type (validates format, enables click-to-email).
- URLs → URL field type (renders as clickable link).
- Dates → Date or Date/Time field type (enables date filters in reports).
- Money amounts → Currency field type (respects org currency settings).
- Counts/quantities → Number field type (enables SUM in reports).

Use Text only for truly unstructured data (notes, descriptions, identifiers).
```

**Detection hint:** If the output recommends a Text field for data that has a dedicated Salesforce field type (phone, email, URL, date, currency), the type choice is suboptimal. Check if the field's purpose matches a built-in type.

---

## Anti-Pattern 3: Using the wrong relationship type (Lookup vs Master-Detail)

**What the LLM generates:** "Create a Lookup relationship from Invoice Line Item to Invoice. This will let you roll up totals."

**Why it happens:** LLMs conflate Lookup and Master-Detail relationships. Roll-up summary fields are only available on Master-Detail relationships (natively). A Lookup relationship does not support roll-up summaries without custom code or Flow-based roll-ups. Conversely, LLMs sometimes recommend Master-Detail when a Lookup is more appropriate (the child should be independently ownable).

**Correct pattern:**

```
Relationship type decision:
- Master-Detail: child record cannot exist without a parent, inherits
  parent's sharing, parent deletion cascades to children, and enables
  native roll-up summary fields. Child OwnerId is controlled by parent.
- Lookup: child record can exist independently, has its own OwnerId
  and sharing settings, and parent deletion can be configured
  (clear field, block deletion, or delete child).

If you need roll-up summaries with a Lookup, use:
- Declarative Lookup Rollup Summaries (DLRS) app.
- Flow-based rollup (Record-Triggered Flow on child).
- Apex trigger.
```

**Detection hint:** If the output mentions "roll-up summary" on a Lookup field, or recommends Master-Detail when the child needs independent ownership, the relationship type is wrong. Search for `roll-up` combined with `Lookup`.

---

## Anti-Pattern 4: Ignoring the field API name convention and __c suffix

**What the LLM generates:** "Create a field named 'Customer Revenue' with API name 'CustomerRevenue'."

**Why it happens:** LLMs sometimes omit the `__c` suffix or use spaces/special characters in the API name. Salesforce automatically appends `__c` to custom field API names, and API names only allow alphanumeric characters and underscores. The LLM should advise on the developer name (without __c, which Salesforce adds) but should reference the full API name (with __c) in formulas, code, and metadata.

**Correct pattern:**

```
When creating the field:
- Label: Customer Revenue
- Field Name (developer name): Customer_Revenue
  (Salesforce appends __c automatically → Customer_Revenue__c)
- In formulas, Apex, and API references, use the full API name:
  Account.Customer_Revenue__c
- Do not include spaces, hyphens, or special characters in the developer name.
- Choose the developer name carefully — it cannot be changed after creation
  without creating a new field and migrating data.
```

**Detection hint:** If the output references a custom field without the `__c` suffix in formulas or code, or suggests an API name with spaces, the naming is incorrect. Regex: `[A-Z][a-z]+[A-Z]` without trailing `__c` in code context.

---

## Anti-Pattern 5: Recommending a field type change on an existing field with data

**What the LLM generates:** "Change the field type from Text to Number to enable calculations."

**Why it happens:** LLMs suggest field type changes without warning about data loss. Salesforce restricts which field type conversions are allowed, and some conversions cause irreversible data loss (e.g., converting from Text Area to Text truncates content, converting to Checkbox loses non-boolean values). Some conversions are blocked entirely.

**Correct pattern:**

```
Field type changes with data carry risks:
1. Check the Field Type Conversion chart in Salesforce Help to confirm
   the conversion is allowed.
2. Backup existing data before any type change.
3. Conversions that may cause data loss:
   - Rich Text → Text: formatting lost.
   - Text → Number: non-numeric values become blank.
   - Picklist → Text: loses picklist validation.
4. If the conversion is not allowed or too risky:
   - Create a new field with the correct type.
   - Migrate data from the old field to the new field.
   - Update all references (formulas, flows, reports, code).
   - Deprecate the old field.
```

**Detection hint:** If the output recommends changing a field type without mentioning data loss risks or the conversion compatibility chart, the advice is incomplete. Search for `change the field type` without `data loss` or `backup`.

---

## Anti-Pattern 6: Forgetting to add the field to reports and list views

**What the LLM generates:** "Create the field and add it to the page layout. The field is now available for users."

**Why it happens:** LLMs focus on the record page and forget that users also consume fields through reports, list views, and search results. A new field must be added to relevant report types (if custom), list views, and search layouts to be fully usable.

**Correct pattern:**

```
After creating the field and setting FLS:
1. Page layout: add to relevant section(s).
2. Reports: the field is automatically available in standard report types.
   For custom report types, add the field in Setup → Report Types → [Type] → Edit Layout.
3. List views: users can add the field themselves, or the admin can
   add it to shared/org-wide list views.
4. Search layouts: if the field should appear in search results,
   edit the object's search layout in Object Manager.
5. Compact layout: if the field should appear in the record highlights
   panel or mobile view, add it to the compact layout.
```

**Detection hint:** If the output stops at page layout placement without mentioning reports, list views, or search layouts, the field's discoverability is incomplete. Search for `report` or `list view` or `compact layout` after the creation steps.
