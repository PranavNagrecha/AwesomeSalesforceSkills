# Well-Architected Notes — Global Actions and Quick Actions

## Relevant Pillars

- **Operational Excellence** — Quick actions reduce the number of clicks and screens users navigate to complete frequent tasks. Well-designed action layouts with predefined values directly reduce operational friction and human error. Misconfigured actions (wrong type, missing fields, invisible due to layout issues) generate support tickets and erode trust in the platform.
- **User Experience** — Quick actions are a primary UX lever for keeping users in context and on the record they are working. An action that surfaces the right fields and pre-fills reasonable defaults reduces cognitive load. Actions that are too long, have too many required fields, or fail silently due to missing required fields create frustration.

## Architectural Tradeoffs

**Global vs Object-Specific:** Global actions trade context for reach. They appear everywhere but cannot leverage source-record data. Object-specific actions are more powerful (predefined values, context) but only appear on one object's record page. The choice is driven by whether the action's context is always a specific record (use object-specific) or needs to be accessible from any page (use global).

**Custom (LWC/VF) vs Declarative Action Types:** Custom action types using LWC or Visualforce provide full UI control but introduce code debt, require developer involvement to change, and have surface-specific restrictions (e.g., LWC global actions only work in Field Service mobile). Declarative Create/Update/Flow action types are self-service for admins and deployable via change sets. Prefer declarative types unless the UX requirement cannot be met otherwise.

**Where a Default Belongs:** the same value can be set three ways — a field
default, a predefined value on the action, or a before-save Flow. The Metadata
API guide fixes the precedence between the first two: "If a field on an action
has both a predefined value and a default value set, the action uses the
predefined value, not the default value." That makes an action override an
invisible fork in the data. Prefer the field default when every creation path
should agree; use a predefined value only when *this* action genuinely means
something different (an escalation action that pins `Origin` to `Phone`), and a
before-save Flow when the rule must hold for API and data-load traffic too.
Document the choice — a value that appears from nowhere is the hardest kind of
configuration to inherit.

**Action Layout Field Count:** A compact action layout (4–6 fields) is faster to complete, works better on mobile, and has higher completion rates. An action layout with 15+ fields is effectively an inline edit page and should be reconsidered — possibly redesigned as a Flow or a full record edit.

## Anti-Patterns

1. **Duplicating page layout fields in action layouts** — Treating the action layout as a copy of the page layout creates a maintenance burden (two places to update per field change) and violates the purpose of the action (compact, context-specific data entry). Keep action layouts minimal: only the fields required to create a valid record.

2. **Using global actions when object-specific actions with predefined values would work** — Teams sometimes choose global actions for simplicity, then complain that parent lookups are blank and data integrity suffers. When there is a clear source record, always use an object-specific action with predefined values to auto-link the new record.

3. **Adding too many actions to a page layout** — Every action added to a page layout's mobile section that pushes total count beyond ~5 effectively hides subsequent actions behind a "More" menu. Teams add actions liberally during project delivery and never audit. The result is an overloaded action bar that users stop trusting. Apply governance: new actions require an existing action to be removed or deprioritized.

## Official Sources Used

- Metadata API Developer Guide v67.0 (Summer '26), `QuickAction` type — [PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) (the field table and `QuickActionType` enum behind `references/metadata-examples.md` examples 1–6 and the Core Concepts metadata table; `targetRecordType`'s three valid values in gotcha 6; `optionsCreateFeedItem` being Required and Create/Update/LogACall-only in gotcha 10; the eight-field usability recommendation)
- Metadata API Developer Guide v67.0, `FieldOverride` — [PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) (`literalValue` "Supported for picklists only" and `formula`'s API 43.0 picklist support in gotcha 7; the predefined-value-beats-default precedence in gotcha 8 and in Architectural Tradeoffs above)
- Metadata API Developer Guide v67.0, `QuickActionLayout` / `QuickActionLayoutColumn` / `QuickActionLayoutItem` — [PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) (the `LayoutSectionStyle` and `UiBehavior` enumerations, and the scope of `Required` in gotcha 9)
- Metadata API Developer Guide v67.0, `Layout` → `PlatformActionList`, `PlatformActionListItem`, `QuickActionList` — [PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf) (the two independent action lists and the `PlatformActionListContext` / `PlatformActionType` enumerations in gotcha 11 and `references/metadata-examples.md` section 7; the `FlexiPage` counterparts)
- Apex Reference Guide, `QuickAction` class and `QuickAction.DescribeAvailableQuickActionResult` — [PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf) (`describeAvailableQuickActions('Account' | 'Global')` as the post-deploy verification step; the `'Account.QuickCreateContact'` vs `'Global.CreateNewContact'` naming convention; `getQuickActionName()` for proving a record came from an action)
- Object Reference for the Salesforce Platform, Macro instruction target grammar and EmailMessage — [PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf) (the `QuickAction.<EntityApiName>.<QuickActionName>` dot-notation grammar corroborating the file-naming convention; "To update an email's data before it's sent, use Quick Action predefined values or a QuickActionDefaultsHandler", which is why `admin/case-feed-send-email-action` owns that path)
- LWC Developer Guide: `lightning__GlobalAction` Target — https://developer.salesforce.com/docs/platform/lwc/guide/targets-lightning-global-action.html (gotcha 2, the Field Service mobile restriction on custom global actions)
- Salesforce App Admin Guide: Object-Specific versus Global Actions — https://developer.salesforce.com/docs/atlas.en-us.salesforce1appadmin.meta/salesforce1appadmin/s1_admin_guide_actions_obj_vs_global.htm (the scope comparison table in SKILL.md Core Concepts)
- Salesforce App Admin Guide: Action Layouts — https://developer.salesforce.com/docs/atlas.en-us.salesforce1appadmin.meta/salesforce1appadmin/s1_admin_guide_actions_layouts.htm (gotcha 1, action layout as a separate artefact from the page layout)
- Salesforce Help: Set Predefined Field Values for Quick Action Fields — https://help.salesforce.com/s/articleView?id=platform.predefined_field_values.htm&language=en_US&type=5 (the Setup-side name for `fieldOverrides` and the "Specific Value" control that maps to `literalValue`)
- Salesforce Help: Quick Actions — https://help.salesforce.com/s/articleView?id=platform.actions_overview.htm&language=en_US&type=5 (Setup navigation paths in SKILL.md and `references/examples.md`)
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (the Operational Excellence and User Experience framing at the top of this file)
