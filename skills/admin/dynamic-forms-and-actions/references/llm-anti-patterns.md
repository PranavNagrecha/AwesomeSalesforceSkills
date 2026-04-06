# LLM Anti-Patterns — Dynamic Forms and Actions

Common mistakes AI coding assistants make when generating or advising on Salesforce Dynamic Forms and Dynamic Actions.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Assuming Dynamic Forms work on all standard objects

**What the LLM generates:** "Enable Dynamic Forms on the Lead record page by clicking 'Upgrade Now' in Lightning App Builder."

**Why it happens:** LLMs apply Dynamic Forms universally. Dynamic Forms rollout to standard objects has been incremental. Account, Contact, Opportunity, and Case received support over several releases, but not all standard objects support Dynamic Forms. The admin must verify support for the specific object in Lightning App Builder.

**Correct pattern:**

```
Before enabling Dynamic Forms:
1. Open the Lightning record page in Lightning App Builder.
2. Click on the Record Detail component.
3. If "Upgrade Now" button appears → Dynamic Forms is supported.
4. If no upgrade option appears → the object does not yet support
   Dynamic Forms. Use page layouts with record types instead.

Supported standard objects (verify in your org's release):
- Account, Contact, Opportunity, Case, Lead, plus others added per release.
- Custom objects: all supported.
- Some standard objects (e.g., Event, Task) may not support Dynamic Forms.
```

**Detection hint:** If the output enables Dynamic Forms on a standard object without verifying support, it may fail. Search for `Upgrade Now` or `verify` combined with the object name.

---

## Anti-Pattern 2: Mixing up visibility filter logic between AND and OR conditions

**What the LLM generates:** "Set visibility to show the field when Record Type = 'Enterprise' or User Profile = 'Sales Rep'. Add both conditions."

**Why it happens:** LLMs describe multiple visibility conditions but do not clarify whether they combine as AND or OR. In Lightning App Builder, multiple visibility conditions on a single component default to AND logic. To achieve OR logic, the admin must select "Any condition is met" in the filter settings.

**Correct pattern:**

```
Visibility filter logic in Dynamic Forms:
- Default: "All conditions are met" (AND logic).
  Field shows only when ALL conditions are true.
- Alternative: "Any condition is met" (OR logic).
  Field shows when ANY condition is true.

To configure:
1. Select the field component in Lightning App Builder.
2. In the Properties panel, click "Set Visibility."
3. Add conditions.
4. Change the filter logic dropdown:
   - "All Conditions Are Met" = AND
   - "Any Condition Is Met" = OR
5. For complex logic (A AND (B OR C)), you may need to use
   a formula-based visibility filter or separate field components.
```

**Detection hint:** If the output adds multiple visibility conditions without specifying whether the logic is AND or OR, the behavior is ambiguous. Search for `All conditions` or `Any condition` in the visibility configuration.

---

## Anti-Pattern 3: Advising Dynamic Forms as a replacement for all page layout assignments

**What the LLM generates:** "Convert all your page layouts to Dynamic Forms and delete the page layouts."

**Why it happens:** LLMs position Dynamic Forms as a complete replacement for page layouts. Page layouts still control: related lists, mobile-specific layouts (partially), button/action placement (without Dynamic Actions), and profile-to-layout assignment. Deleting page layouts breaks these features.

**Correct pattern:**

```
Dynamic Forms replaces FIELD sections on page layouts, not everything:

Still controlled by page layouts:
- Related lists on the record page.
- Mobile-specific field ordering (partially).
- Record type assignment matrix (profile → record type → page layout).
- Page layout assignment to profiles (even with Dynamic Forms,
  a page layout must be assigned).

Dynamic Forms controls:
- Which fields appear on the record detail.
- Field visibility conditions (value-based, profile-based, permission-based).
- Field section organization on the Lightning record page.

You still need page layouts even when using Dynamic Forms.
```

**Detection hint:** If the output says to "delete page layouts" after enabling Dynamic Forms, it will break related lists and other layout-dependent features. Search for `delete page layout` or `replace page layout entirely`.

---

## Anti-Pattern 4: Ignoring Dynamic Actions when configuring Dynamic Forms

**What the LLM generates:** "Set up Dynamic Forms for conditional field visibility. The action buttons will stay as-is."

**Why it happens:** LLMs treat Dynamic Forms and Dynamic Actions as separate projects. When converting to Dynamic Forms, the admin should also evaluate Dynamic Actions to control which buttons (Edit, Clone, Delete, custom actions) appear based on record context. Missing Dynamic Actions means all actions always show, even when irrelevant.

**Correct pattern:**

```
Configure Dynamic Forms AND Dynamic Actions together:
1. Dynamic Forms: conditional field visibility.
2. Dynamic Actions: conditional action button visibility.
   - In Lightning App Builder, click on the Highlights Panel component.
   - Enable Dynamic Actions if available for the object.
   - Add visibility conditions per action:
     - Show "Submit for Approval" only when Status = 'Draft'.
     - Show "Escalate" only when Priority = 'High'.
     - Hide "Delete" for non-admin profiles.
3. If the page layout's "Salesforce Mobile and Lightning Experience Actions"
   section is customized, those overrides are replaced by Dynamic Actions.
```

**Detection hint:** If the output configures Dynamic Forms without mentioning Dynamic Actions, the action bar is left unconsidered. Search for `Dynamic Actions` in the output.

---

## Anti-Pattern 5: Using Dynamic Forms visibility to enforce data security

**What the LLM generates:** "Hide the Salary field from non-HR users using Dynamic Forms visibility rules. This secures the data."

**Why it happens:** LLMs conflate UI visibility with data security. Dynamic Forms visibility is a UI-layer control -- it hides fields on the page but does NOT enforce Field-Level Security. Users can still access hidden fields through reports, APIs, list views, and SOQL. FLS on profiles or permission sets is the security enforcement layer.

**Correct pattern:**

```
Dynamic Forms visibility ≠ Field-Level Security:

- Dynamic Forms visibility: UI convenience. Hides fields on the record page.
  Does NOT prevent access via reports, API, Data Loader, or SOQL.

- Field-Level Security (FLS): actual security enforcement.
  Prevents field access across ALL channels (UI, API, reports, SOQL).

For sensitive fields (salary, SSN, health data):
1. Set FLS to NOT visible on non-authorized profiles/permission sets.
2. THEN use Dynamic Forms visibility for UX cleanup on authorized users
   (e.g., show salary field only on HR record type).

Never rely on Dynamic Forms alone for data security.
```

**Detection hint:** If the output uses Dynamic Forms visibility to "secure" or "protect" a field without also configuring FLS, the field is not actually secured. Search for `secure`, `protect`, or `restrict access` combined with `Dynamic Forms` without `FLS` or `Field-Level Security`.
