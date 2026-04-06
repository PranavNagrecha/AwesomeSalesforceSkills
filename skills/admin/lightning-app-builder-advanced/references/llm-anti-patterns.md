# LLM Anti-Patterns — Lightning App Builder Advanced

Common mistakes AI coding assistants make when generating or advising on Lightning App Builder Advanced.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Declaring recordId in LWC targetConfig Design Properties

**What the LLM generates:** An LWC component `.js-meta.xml` file that includes `<property name="recordId" type="String" />` inside a `<targetConfig targets="lightning__RecordPage">` block, treating it like a configurable design attribute.

**Why it happens:** LLMs learn from older Aura component examples where exposing `id` or `recordId` as a design attribute in `.design` files was a common pattern. They incorrectly transfer this pattern to LWC.

**Correct pattern:**

```xml
<!-- WRONG — do not include recordId in targetConfig -->
<targetConfig targets="lightning__RecordPage">
    <property name="recordId" type="String" label="Record ID" />
</targetConfig>

<!-- CORRECT — recordId is injected automatically; declare @api in JS only -->
<targetConfig targets="lightning__RecordPage">
    <!-- no recordId property here -->
</targetConfig>
```

In the component's JavaScript:
```javascript
import { LightningElement, api } from 'lwc';
export default class MyComponent extends LightningElement {
    @api recordId;   // injected by framework — no targetConfig declaration needed
}
```

**Detection hint:** Search for `name="recordId"` or `name="objectApiName"` inside `<targetConfig>` blocks in `.js-meta.xml` files.

---

## Anti-Pattern 2: Treating Visibility Filters as Security Controls

**What the LLM generates:** Guidance such as "set a visibility filter to hide the Salary field from non-managers — this ensures non-managers cannot see salary data."

**Why it happens:** LLMs conflate UI rendering control with data access control. The framing of "hide" sounds like protection, but visibility filters only affect what the LAB canvas renders.

**Correct pattern:**

```
WRONG:
"Use a visibility filter (Profile = Manager) on the Salary field component to secure salary data."

CORRECT:
1. Set FLS on the Salary__c field to remove read access from all profiles except Manager.
2. Optionally, add a visibility filter (Profile = Manager) on the field component for UX purposes.
Step 1 is mandatory for security. Step 2 is optional UX cleanup only.
```

**Detection hint:** Any advice that uses the phrase "hide to secure", "visibility rule to prevent access", or "filter to restrict" should be flagged for FLS review.

---

## Anti-Pattern 3: Recommending Multiple Page Layouts Instead of Dynamic Forms + Formula Fields

**What the LLM generates:** "Create three separate page layouts — one for each record type — and assign them to the corresponding profiles. This way each user sees only the relevant fields."

**Why it happens:** Multiple page layouts is the pre-Dynamic Forms pattern. LLMs trained on older Salesforce content default to layout proliferation without considering that Dynamic Forms achieves the same goal on a single page with visibility rules.

**Correct pattern:**

```
When the object supports Dynamic Forms:
1. Enable Dynamic Forms on the record page.
2. Use field component visibility rules (record type, profile, field value) to show/hide fields.
3. Use formula fields as visibility proxies for complex multi-condition logic.

Result: one page, one layout, declarative field visibility. Fewer deployments to maintain.

Only use multiple page layouts when Dynamic Forms is unsupported for the target object.
```

**Detection hint:** If the LLM response includes "create a separate page layout for each X" and the object is known to support Dynamic Forms, question whether multiple layouts are necessary.

---

## Anti-Pattern 4: Enabling Dynamic Actions Without Removing Page-Layout Action Bar Assignments

**What the LLM generates:** Steps to enable Dynamic Actions that stop at clicking the "Enable Dynamic Actions" button in LAB, without mentioning the cleanup of page-layout action bar assignments.

**Why it happens:** LLMs describe the feature activation step correctly but miss the side-effect interaction between Dynamic Actions and the pre-existing page-layout action section, because this interaction is a post-activation gotcha not mentioned in the feature documentation headline.

**Correct pattern:**

```
INCOMPLETE (LLM default):
1. Open LAB for the record page.
2. Click the action bar component.
3. Enable Dynamic Actions.

COMPLETE:
0. BEFORE enabling: check page layout assignments for the target object.
   Identify all layouts assigned to the profiles using this page.
   Clear the "Salesforce Mobile and Lightning Experience Actions" section
   from those layouts, OR plan to remove the duplicate entries immediately after activation.
1. Open LAB for the record page.
2. Click the action bar component and enable Dynamic Actions.
3. Verify no duplicate buttons appear by previewing the page as affected profiles.
```

**Detection hint:** If Dynamic Actions instructions do not include a step about page-layout action cleanup, the guidance is incomplete.

---

## Anti-Pattern 5: Using Aura lightning:template Pattern for LWC Custom Templates

**What the LLM generates:** An LWC component with `implements="lightning:template"` in its HTML template, or instructions to create a custom page template as an LWC component.

**Why it happens:** LWC has replaced most Aura use cases, so LLMs default to LWC for new component work. They do not account for the fact that `lightning:template` is an Aura-only interface with no LWC equivalent.

**Correct pattern:**

```xml
<!-- WRONG: LWC cannot implement lightning:template -->
<!-- my-template.html -->
<template implements="lightning:template">
    ...
</template>

<!-- CORRECT: Must be Aura -->
<!-- MyPageTemplate.cmp -->
<aura:component implements="lightning:template" description="Custom page template">
    <flexipage:region name="main" defaultWidth="LARGE" />
    <flexipage:region name="sidebar" defaultWidth="SMALL" />
</aura:component>
```

LWC components can be placed *inside* template regions as content components. Only the template container itself must be Aura.

**Detection hint:** Any instruction to create a custom LAB page template using LWC (`.html`, `export default class ... LightningElement`) should be flagged. Custom templates require Aura (`.cmp`).

---

## Anti-Pattern 6: Assuming All Standard Objects Support Dynamic Forms

**What the LLM generates:** Instructions to enable Dynamic Forms for any standard object (e.g., User, Product2, PricebookEntry) without checking eligibility.

**Why it happens:** LLMs know Dynamic Forms is a major feature and assume it applies broadly. The supported standard object list has expanded over releases but has never included all standard objects.

**Correct pattern:**

```
Before advising Dynamic Forms for a standard object:
1. Check the current Salesforce Help article "Dynamic Forms Considerations" for the current supported standard object list.
2. If the object is not listed, Dynamic Forms is unavailable.
3. Fallback options: multiple page layouts, or formula fields surfaced as read-only components.
```

**Detection hint:** If the LLM confidently recommends Dynamic Forms for User, Product2, Lead (pre-Summer '23), Task, or Event without a caveat about eligibility, verify the current supported object list before following that advice.
