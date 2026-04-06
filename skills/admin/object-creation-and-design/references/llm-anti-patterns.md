# LLM Anti-Patterns — Object Creation and Design

Common mistakes AI coding assistants make when generating or advising on Salesforce custom object creation.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Defaulting to Public Read/Write OWD without security analysis

**What the LLM generates:** "Create the custom object with Public Read/Write sharing. This keeps things simple."

**Why it happens:** LLMs optimize for simplicity and default to the most permissive sharing model. The org-wide default (OWD) should be set based on data sensitivity analysis. Starting with Public Read/Write means all users can see and edit all records. Tightening OWD later requires reconfiguring sharing rules and testing, which is harder than starting restrictive.

**Correct pattern:**

```
OWD selection during object creation:
1. Ask: "Should every user in the org be able to see and edit every record?"
   - If NO → start with Private.
   - If read-only access is fine for most → Public Read Only.
   - If truly open → Public Read/Write.
2. Start restrictive, then open up with sharing rules as needed.
   It is much easier to add sharing rules than to restrict them later.
3. Consider whether this object will hold:
   - PII or sensitive data → Private.
   - Reference data (countries, product catalog) → Public Read Only.
   - Collaboration data (team notes) → Public Read/Write may be fine.
```

**Detection hint:** If the output sets OWD to Public Read/Write without discussing data sensitivity, the sharing model is being chosen by default. Search for `security`, `sensitivity`, or `sharing analysis` near the OWD setting.

---

## Anti-Pattern 2: Forgetting to create a custom tab for the object

**What the LLM generates:** "Create the custom object. Users can now navigate to it."

**Why it happens:** LLMs assume the object is automatically accessible in the UI. A custom object does not appear in any app's navigation until a custom tab is created (Setup → Tabs → Custom Object Tabs) and the tab is added to a Lightning app's navigation items.

**Correct pattern:**

```
After creating the custom object:
1. Create a custom tab:
   Setup → Tabs → Custom Object Tabs → New.
   Select the object, choose a tab style (icon and color).
2. Add the tab to the relevant Lightning app:
   Setup → App Manager → [App] → Edit → Navigation Items.
   Move the new tab from Available to Selected.
3. Verify tab visibility:
   Tab visibility is controlled by profiles (Setup → Profiles → [Profile] → Tab Settings).
   Set to "Default On" for profiles that need the tab.
```

**Detection hint:** If the output creates a custom object without a subsequent tab creation step, users cannot navigate to it. Search for `Tab` or `custom tab` after the object creation instructions.

---

## Anti-Pattern 3: Not enabling optional features (Activities, History, Reports) at creation time

**What the LLM generates:** "Create the custom object with the default settings."

**Why it happens:** LLMs skip the optional feature checkboxes during object creation. Features like Allow Activities, Track Field History, Allow Reports, Allow Search, and Allow in Chatter Groups are best enabled during creation. While most can be enabled later, Field History Tracking only starts tracking from the moment it is enabled -- no retroactive history.

**Correct pattern:**

```
During custom object creation, evaluate each option:
| Feature                     | Default | Recommendation                        |
|-----------------------------|---------|---------------------------------------|
| Allow Reports               | On      | Keep on (almost always needed).       |
| Allow Activities            | Off     | Enable if Tasks/Events relate to this object. |
| Track Field History         | Off     | Enable if audit trail is needed — no retroactive tracking. |
| Allow in Chatter Groups     | Off     | Enable for collaboration objects.     |
| Allow Sharing               | On      | Keep on if Private OWD is possible.   |
| Allow Search                | On      | Keep on unless the object is internal-only. |

Field History Tracking: enable during creation if there is ANY
chance you will need change history. Cannot be backfilled later.
```

**Detection hint:** If the output creates the object with "default settings" without evaluating Activities, History, or Search, features may be missed. Search for `Allow Activities` or `Track Field History` in the creation steps.

---

## Anti-Pattern 4: Using abbreviations or unclear API names for the object

**What the LLM generates:** "Create the object with API name `CRR__c` for Customer Revenue Record."

**Why it happens:** LLMs use abbreviations for brevity. Object API names are permanent -- they cannot be changed after creation. Cryptic abbreviations make the org harder to maintain as the team grows. Future developers, admins, and integrations will struggle with `CRR__c` vs `Customer_Revenue_Record__c`.

**Correct pattern:**

```
Object naming conventions:
1. Label: human-readable, title case. Example: "Customer Revenue Record".
2. Plural Label: "Customer Revenue Records".
3. API Name (Object Name): descriptive, underscored.
   Example: Customer_Revenue_Record__c (Salesforce appends __c).
4. Rules:
   - No abbreviations unless universally understood (SLA, PO, SKU).
   - No leading numbers.
   - Alphanumeric and underscores only.
   - API name CANNOT be changed after creation.
   - Match the label as closely as possible.
```

**Detection hint:** If the object API name is 3-4 characters or uses non-obvious abbreviations, the naming is unclear. Regex: `^[A-Z]{2,4}__c$` for suspiciously short API names.

---

## Anti-Pattern 5: Creating a custom object when a standard object fits the need

**What the LLM generates:** "Create a custom object called 'Support Ticket' to track customer issues."

**Why it happens:** LLMs default to custom objects because the creation process is straightforward to describe. Salesforce provides standard objects (Case, Lead, Opportunity, Campaign, etc.) that come with built-in business logic, automation, reporting, and UI features. Using a custom object when a standard one fits means losing all that built-in functionality.

**Correct pattern:**

```
Before creating a custom object, check standard objects:
| Business Need             | Standard Object | Built-in Features                    |
|---------------------------|-----------------|--------------------------------------|
| Customer issues/tickets   | Case            | Escalation, entitlements, email-to-case |
| Sales deals               | Opportunity     | Stages, forecasting, products, quotes |
| Prospective customers     | Lead            | Conversion, web-to-lead, campaigns   |
| Marketing efforts         | Campaign        | Members, ROI tracking, hierarchy     |
| Products and pricing      | Product2        | Price books, schedules               |

Only create a custom object when:
- No standard object covers the need.
- The standard object's built-in behavior conflicts with the requirement.
- The data model is domain-specific (e.g., Inspections, Equipment).
```

**Detection hint:** If the output creates a custom object whose purpose closely matches a standard object's functionality, the choice should be questioned. Match the object's description against standard object purposes.
