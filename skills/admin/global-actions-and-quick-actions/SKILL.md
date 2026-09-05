---
name: global-actions-and-quick-actions
description: "Use this skill when configuring object-specific quick actions or global actions in Salesforce: choosing between action types, editing action layouts, pre-filling fields with predefined values, and adding actions to Lightning page layouts or mobile navigation. Trigger keywords: quick action, global action, action layout, pre-fill fields, predefined values, Salesforce mobile actions. NOT for building an LWC that runs as a quick action — use lwc/lwc-quick-actions. NOT for converting Classic JavaScript or URL buttons — use admin/custom-button-to-action-migration. NOT for Dynamic Actions visibility rules on a Lightning record page — use admin/dynamic-forms-and-actions. Also covers the QuickAction metadata type: quickAction-meta.xml, quickActionLayout, fieldOverrides, targetObject, targetParentField, targetRecordType, flowDefinition, and the Layout platformActionList and quickActionList entries that place an action."
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
  - "quick action deployed successfully but doesn't appear on the record page"
  - "pre-fill a lookup on a quick action from the current record"
  - "field added to the page layout is missing from the quick action popup"
  - "predefined field value on a global action won't save"
  - "quick action button hidden behind the More menu in Lightning"
  - "write the quickAction-meta.xml for a Create action"
  - "targetRecordType rejected on a Case quick action"
  - "launch a screen flow from a button on a record page"
  - "add an action to the Salesforce mobile action bar"
  - "action layout vs page layout — which one controls the quick action form"
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
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
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

## Questions to Ask Before Configuring

Ask these before opening Setup. Each one maps to a gotcha in `references/gotchas.md`; skipping them produces an action that deploys cleanly and does the wrong thing.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Which record is the user looking at when they press this?" | A named record means object-specific and `targetParentField` can link the new record; "any page" means global and the user must pick the parent by hand | The scope decision, and whether parent linkage is free or manual |
| "Which fields must the user type, and which should we set for them?" | Typed fields go on the action layout; set fields become `fieldOverrides` and can be omitted from the layout entirely | The split between layout items and predefined values |
| "Is each pre-set field a picklist?" | `literalValue` is picklists only; every other type needs `formula` with a quoted string (gotcha 7) | The correct override element per field, before the deploy fails |
| "Do any of these fields already have a default value?" | A predefined value overrides the field default, so the action's records diverge from every other creation path (gotcha 8) | A conscious decision instead of a later data-quality investigation |
| "Which page layouts, and which surfaces — record bar, Classic publisher, mobile, list view?" | `platformActionList` and `quickActionList` are separate lists, and `actionListContext` picks the bar (gotcha 11) | The exact Layout edits, deployable in the same change |
| "Is this object already on Dynamic Actions?" | If yes, the FlexiPage action list drives the bar and Layout edits are dead configuration | A redirect to `admin/dynamic-forms-and-actions` before wasted work |
| "How many actions are already in front of this one?" | Position decides discoverability; `sortOrder` is the only lever (gotcha 5) | An agreed `sortOrder`, and which existing action loses its slot |

What a proper configuration adds over just creating the action: the record it creates is linked and pre-filled without user typing, the pre-set values are written with the element the field type actually accepts, and the action ships in the same deployment as every Layout that surfaces it — so it is visible to real users on the first release rather than the second.

---

## Core Concepts

### Action Types

These are the six action types an admin picks in Setup day to day. Choosing the wrong one at creation forces deletion and recreation. The full `QuickActionType` enum in the Metadata API also carries `Post`, `SocialPost` and `Canvas` — see the metadata table below:

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
- Formula fields, roll-up summary fields, and auto-number fields cannot be added to action layouts. (UNVERIFIED 2026-09-04: not stated in the Metadata API guide's QuickActionLayout section; confirm in Setup before relying on it.)

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

### The Metadata Behind the Setup Screens

Every Setup field maps to one element of the `QuickAction` metadata type. Read this table when reviewing a diff or writing the XML by hand; `references/metadata-examples.md` has the full deployable files.

| Setup control | Element | Notes from the Metadata API guide |
|---|---|---|
| Action Type | `type` | Required. `Canvas`, `Create`, `Flow`, `LightningComponent`, `LogACall`, `Post`, `SendEmail`, `SocialPost`, `Update`, `VisualforcePage` |
| Target Object | `targetObject` | "The object for which the action is created and performed" |
| (implicit parent link) | `targetParentField` | "Links the target object to the parent object" — object-specific actions only |
| Record Type | `targetRecordType` | Only `Business Account`, `Person Account`, `Master` — see gotcha 6 |
| Label / Standard Label | `label` / `standardLabel` | `standardLabel` uses the `QuickActionLabel` enum so the platform supplies a translated label |
| Create a feed item | `optionsCreateFeedItem` | **Required**; applies only to Create, Update and Log a Call |
| Success Message | `successMessage` | API 36.0+ |
| Edit Layout | `quickActionLayout` | `layoutSectionStyle` (required) + `quickActionLayoutColumns` → `quickActionLayoutItems` (`field`, `emptySpace`, `uiBehavior`) |
| Predefined Field Values | `fieldOverrides` | `field` + `formula` or `literalValue` |
| Flow | `flowDefinition` | API name of the flow |
| Lightning / Visualforce / Canvas | `lightningComponent` / `page` / `canvas` | plus `height` and `width` in pixels |

Files live in `quickActions/`, suffix `.quickAction`. Object-specific actions are addressed with dot notation — the platform uses `Account.QuickCreateContact` for an entity-level action and `Global.CreateNewContact` for a global one, per the Apex `describeQuickActions` signature.

The action's placement is not part of the action. It lives on the `Layout` (`platformActionList` for the Lightning and mobile bar, `quickActionList` for the Classic publisher) or, when Dynamic Actions are on, on the `FlexiPage`.

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

1. **Scope and surface** — answer the Questions table above; decide object-specific vs global, and list every page layout (or FlexiPage) that must carry the action. If the object is on Dynamic Actions, stop and route to `admin/dynamic-forms-and-actions`
2. **Split the fields** — put user-typed fields in `quickActionLayout` with the right `uiBehavior`, and everything you set for the user in `fieldOverrides`; check each override's field type against `literalValue` (picklists only) vs `formula`
3. **Write or configure the action** — copy the matching shape from `references/metadata-examples.md` (Create with parent link, global Log a Call, Update, Flow, custom component, Person Account), or build it in Setup and retrieve it
4. **Place it** — add the action to `platformActionList` with an explicit `sortOrder`, and to `quickActionList` too if Classic is still in use; keep the action and its layouts in one deployment
5. **Check statically** — run `python3 scripts/check_global_actions_and_quick_actions.py --manifest-dir force-app/main/default` and clear every ERROR; treat `unplaced` INFOs as release blockers unless the action is deliberately parked
6. **Verify as a user, not as an admin** — run `QuickAction.describeAvailableQuickActions('<Object>')` and `('Global')` in anonymous Apex as a test user on the target profile, then open a record and confirm the pre-filled values and the action's position in the bar
7. **Record it** — fill in `templates/global-actions-and-quick-actions-template.md` with the layout placement, the overrides, and the profiles that can see it

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

4. **The first ~5 actions in the mobile/Lightning section display directly; the rest go to "More"** (UNVERIFIED 2026-09-04: the count is not in the extracted guides; observed behaviour, not a documented limit) — Users often cannot find actions that are listed 6th or later. Keep the highest-frequency actions in the first five positions.

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

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing or reviewing `.quickAction-meta.xml`, the Layout action lists, package.xml, or the deploy and verification commands |
| `references/gotchas.md` | An action deployed but is invisible, a predefined value is ignored or rejected, or a record from the action differs from every other creation path |
| `references/examples.md` | You want a worked end-to-end configuration (create-child, quick update, global log-a-call) with the Setup clicks spelled out |
| `references/well-architected.md` | Deciding global vs object-specific, declarative vs custom component, or how many actions a record page should carry |
| `references/llm-anti-patterns.md` | Reviewing AI-generated quick action guidance before acting on it |
| `templates/global-actions-and-quick-actions-template.md` | Documenting a finished action: type, layout fields, overrides, placement, profile access, test results |
| `scripts/check_global_actions_and_quick_actions.py` | Static-checking retrieved metadata before a deploy |

---

## Related Skills

- `admin/app-and-tab-configuration` — Lightning app configuration; action bar visibility is affected by the Lightning app's navigation items
- `flow/screen-flows` — When the quick action type is "Flow", the referenced flow must be a screen flow; this skill covers building screen flows
- `admin/object-creation-and-design` — Object and field design that determines what can be referenced in quick actions and predefined values
- `admin/dynamic-forms-and-actions` — Dynamic Actions on a Lightning record page: this skill defines the actions, that skill controls when each one is visible
- `admin/record-types-and-page-layouts` — The full `Layout` metadata shape and record-type-to-layout assignment; read it before hand-editing a layout file
- `admin/custom-button-to-action-migration` — Replacing Classic JavaScript, URL, and list buttons with actions
- `admin/case-feed-send-email-action` — The Case Feed Send Email action and its `QuickActionDefaultsHandler`, which is the supported way to shape an outbound email before it sends
- `lwc/lwc-quick-actions` — Building the component behind a custom action: the required target, `recordId`, and closing the modal
