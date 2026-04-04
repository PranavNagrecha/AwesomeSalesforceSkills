---
name: global-actions-and-quick-actions
description: "Use this skill when configuring object-specific quick actions or global actions in Salesforce: choosing between action types, editing action layouts, pre-filling fields with predefined values, and adding actions to Lightning page layouts or mobile navigation. Trigger keywords: quick action, global action, action layout, pre-fill fields, predefined values, Salesforce mobile actions. NOT for Flow-triggered actions or Next Best Action recommendations (use flow/* or agentforce skills). NOT for Apex-defined actions."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
  - User Experience
tags:
  - quick-actions
  - global-actions
  - action-layout
  - mobile
  - productivity
triggers:
  - "how do I add a quick action button to a record page in Lightning"
  - "what is the difference between a global action and an object-specific quick action"
  - "how do I pre-fill fields in a quick action with values from the current record"
  - "quick action fields not showing up on mobile or Lightning Experience"
  - "how to add actions to the Salesforce mobile app action bar"
  - "action layout vs page layout — which one controls what appears in the quick action popup"
inputs:
  - "The object (or global context) where the action should appear"
  - "The action type required (Create, Update, Log a Call, Custom, Flow)"
  - "Fields that need to appear in the action form, and any that should be pre-filled"
  - "Target surfaces: Lightning Experience, Salesforce mobile app, or both"
outputs:
  - "Configured quick action attached to the correct object or global publisher layout"
  - "Action layout with the correct fields for the action's purpose"
  - "Predefined field values configured to reduce user data-entry effort"
  - "Action added to Lightning page layout in the mobile-and-Lightning actions section"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# Global Actions and Quick Actions

This skill activates when an admin needs to create, configure, or troubleshoot global or object-specific quick actions — including editing action layouts, setting predefined field values, and surfacing actions in Lightning Experience or the Salesforce mobile app.

---

## Before Starting

Gather this context before working on quick actions:

- **Where should the action appear?** Global actions appear in the global header and home page; object-specific actions appear on a specific object's record page. The object determines where Setup → Object Manager → Actions is found.
- **What should the action do?** Choose the correct action type before creating (see Core Concepts below). The type cannot be changed after creation.
- **Who needs to see the action?** Actions are added to page layouts. Multiple profiles using different page layouts may need separate layout updates.
- **Mobile or desktop or both?** The "Salesforce Mobile and Lightning Experience Actions" section of a page layout controls both. If you want desktop-only, there is no built-in filter — the same actions list applies to both surfaces.

---

## Core Concepts

### Action Types

Salesforce provides six action types. Choosing the wrong one at creation forces deletion and recreation:

| Action Type | Creates a new record | Updates current record | Logs activity | Launches UI |
|---|---|---|---|---|
| **Create** | Yes | No | No | No |
| **Update** | No | Yes | No | No |
| **Log a Call** | No | No | Yes | No |
| **Custom (VF / LWC)** | Configurable | Configurable | No | Yes |
| **Flow** | Configurable | Configurable | No | Yes |
| **Send Email** | No | No | No | Yes |

**Create actions** are the most common. They create a child or related record (e.g., create a Contact from an Account). When object-specific, the parent record is automatically linked. When global, no parent context is available.

**Update actions** modify fields on the current record without opening the full edit page. Useful for quick status changes or stage updates.

**Log a Call actions** create a completed Task record with subject, description, and date fields. Available on objects that support Activity tracking.

**Flow actions** launch a screen-flow UI within the action dialog. The flow receives the record ID as an input variable if the action is object-specific.

### Global Actions vs Object-Specific Actions

| | Global Actions | Object-Specific Actions |
|---|---|---|
| **Setup location** | Setup → Global Actions | Setup → Object Manager → [Object] → Buttons, Links, and Actions |
| **Parent record context** | Not available | Available via merge fields and predefined values |
| **Where they appear** | Global header, Home page, Chatter | Record pages only |
| **Page layout ownership** | Global Publisher Layouts | Object's page layout |
| **Mobile availability** | Yes, via global header | Yes, via record page |

The key behavioral difference: object-specific actions can reference the source record's fields in predefined values (e.g., pre-fill `Account Name` on a new Contact from an Account record). Global actions cannot because there is no guaranteed source record.

### Action Layouts

Every quick action has its own **action layout** — a separate, independent layout that controls which fields appear inside the quick action dialog. This is distinct from the page layout, which controls field visibility on the record detail page.

Key points:
- Adding a field to a page layout does **not** make it appear in a quick action. Fields must be added to the action layout separately.
- Action layouts are edited in Setup: navigate to the action, then click **Edit Layout** on the action detail page.
- Action layouts are compact by design — best practice is 4–8 fields maximum. More fields defeats the purpose of a quick action.
- Required fields must appear on the action layout or Salesforce will prevent saving.
- Formula fields, roll-up summary fields, and auto-number fields cannot be added to action layouts.

### Predefined Values (Pre-filling Fields)

Predefined values let you auto-populate action layout fields so users do not have to enter them manually. This is configured per-action under **Predefined Field Values**.

Behavior:
- Predefined values support literal values and **merge field formulas** that reference the source record.
- For object-specific actions, `{!ObjectName.FieldAPIName}` syntax resolves at runtime to the parent record's field value.
- For global actions, only static literal values are supported — no source-record merge fields.
- Pre-filled values are editable by the user at action time unless the field is removed from the action layout (hidden but still set).
- A field can receive a predefined value without appearing on the action layout. This is intentional: the field is set silently in the background.

**Example predefined value formula** on a Contact quick action on Account:
```
Account Name: {!Account.Name}
Record Type: Customer Contact
```

### Adding Actions to Page Layouts

An action is not visible to users until it is added to a page layout. Two sections of the page layout editor are relevant:

1. **Salesforce Classic Publisher** — Legacy section. Avoid for new work.
2. **Salesforce Mobile and Lightning Experience Actions** — The correct section for all Lightning and mobile configurations. Actions dragged here appear in both Lightning Experience and the mobile app.

For **global actions**, they go into the **Global Publisher Layout** (Setup → Global Publisher Layouts), not an object's page layout.

Steps to add an object-specific quick action to a Lightning record page:
1. Open Setup → Object Manager → [Object] → Page Layouts → [Layout Name].
2. Drag **Mobile & Lightning Actions** palette items into the "Salesforce Mobile and Lightning Experience Actions" section.
3. Save the page layout.
4. If the layout already has actions, confirm the action is not buried behind the "More" overflow — the first 5 actions in this section appear directly on the highlights panel; subsequent actions go under a "More" dropdown.

---

## Common Patterns

### Pattern 1: Create-Child Quick Action with Pre-filled Parent Lookup

**When to use:** You need users to quickly create a related record (e.g., new Opportunity from an Account) without navigating away.

**How it works:**
1. In Object Manager → Account → Buttons, Links, and Actions → New Action.
2. Action Type: Create. Target Object: Opportunity. Label: "New Opportunity".
3. In the action layout, add fields: Opportunity Name, Close Date, Stage. Remove all other fields.
4. Under Predefined Field Values, set `Account Name` to `{!Account.Name}`.
5. Add the action to the Account's "Salesforce Mobile and Lightning Experience Actions" section in the page layout.

**Why not a manual navigate:** Users stay in context. The Opportunity is already linked to the Account via the predefined account lookup.

### Pattern 2: Update Action for Quick Status Change

**When to use:** A field (like Case Status or Lead Status) needs to be changed without opening the full record edit.

**How it works:**
1. Object Manager → [Object] → New Action. Action Type: Update.
2. Add only the status field to the action layout.
3. Add a predefined value for the new status if it should always be a specific value (e.g., "Closed").
4. Add to page layout.

**Why not inline edit:** Inline edit on a record detail page requires the field to be on the page layout and the user to click the field. A quick action is discoverable as a button and works well for mobile.

### Pattern 3: Global Quick Action for Object-Agnostic Record Creation

**When to use:** Users need to log a Call or create a Task from any page (home, Chatter feed, report) without being on a specific record.

**How it works:**
1. Setup → Global Actions → New Action. Action Type: Log a Call.
2. Add fields: Subject, Description, Date.
3. The action appears in the global header (bell/quick action icon in Lightning).
4. Users can manually relate the log to a record after creation via the "What" and "Who" fields.

**Why not object-specific:** The user may not be on the record when they need to log. Global actions are accessible from anywhere.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Action must pre-fill from the current record's fields | Object-specific action + predefined values | Global actions have no source-record context |
| Action should be accessible from any Salesforce page | Global action + Global Publisher Layout | Object-specific actions only appear on their object's record pages |
| Action launches a Flow | Object-specific Flow action (pass record ID) | Flows that mutate the current record need the record ID as input |
| Action should only appear for one profile/role | Use page layout assignments to restrict | Actions are surfaced via page layouts; profile → layout assignment controls visibility |
| Action should create a related child record | Create action on the parent object | Pre-fill the parent lookup using predefined values with merge fields |
| You need to update a single field quickly | Update action | Narrower UX than full edit; works well on mobile |

---


## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

Before marking quick action configuration complete:

- [ ] Action type is correct for the use case (cannot change after creation)
- [ ] Action layout has only the fields needed — remove unnecessary fields
- [ ] Required fields are on the action layout (absent required fields block saves)
- [ ] Predefined values are set for parent record linkages and any constant defaults
- [ ] Action has been added to the correct page layout section: "Salesforce Mobile and Lightning Experience Actions"
- [ ] Page layout is assigned to the correct profiles
- [ ] Action tested in both Lightning Experience (desktop) and mobile app if both are in use
- [ ] For global actions: action appears in the Global Publisher Layout

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Action layout ≠ page layout** — Adding a field to the object's page layout does not add it to the action's form. You must edit the action layout separately via the action's Edit Layout button. This trips up admins who expect one layout to control everything.

2. **LWC global quick actions are Field Service mobile only** — According to the Lightning Web Components Developer Guide, LWC components exposed as `lightning__GlobalAction` targets are available only in the Field Service mobile app, not in standard Lightning Experience on desktop or mobile. Using a Visualforce or Aura component is the correct approach for global custom actions in regular Lightning Experience.

3. **Actions do not appear without a page layout assignment** — Creating an action and editing its layout is not sufficient; the action must also be dragged into the page layout's actions section and the page layout must be assigned to the user's profile. If an action is missing for some users but visible to others, check page layout assignments.

4. **The first ~5 actions in the mobile/Lightning section display directly; the rest go to "More"** — Users often cannot find actions that are listed 6th or later. Keep the highest-frequency actions in the first five positions.

5. **Predefined values using merge fields only work for object-specific actions** — If you attempt to use `{!ObjectName.Field}` syntax on a global action predefined value, Salesforce will throw a validation error at save time. Global action predefined values must be static literals or formulas without source-record references.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Configured quick action | Action of the correct type, attached to the object or global context |
| Action layout | Compact form with only the necessary fields, required fields present |
| Predefined values | Pre-filled parent lookups and constant defaults reducing user effort |
| Page layout update | Action visible in the "Salesforce Mobile and Lightning Experience Actions" section |

---

## Related Skills

- `admin/app-and-tab-configuration` — Lightning app configuration; action bar visibility is affected by the Lightning app's navigation items
- `flow/screen-flows` — When the quick action type is "Flow", the referenced flow must be a screen flow; this skill covers building screen flows
- `admin/object-creation-and-design` — Object and field design that determines what can be referenced in quick actions and predefined values
