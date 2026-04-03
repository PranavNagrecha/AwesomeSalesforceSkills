# Well-Architected Notes — Global Actions and Quick Actions

## Relevant Pillars

- **Operational Excellence** — Quick actions reduce the number of clicks and screens users navigate to complete frequent tasks. Well-designed action layouts with predefined values directly reduce operational friction and human error. Misconfigured actions (wrong type, missing fields, invisible due to layout issues) generate support tickets and erode trust in the platform.
- **User Experience** — Quick actions are a primary UX lever for keeping users in context and on the record they are working. An action that surfaces the right fields and pre-fills reasonable defaults reduces cognitive load. Actions that are too long, have too many required fields, or fail silently due to missing required fields create frustration.

## Architectural Tradeoffs

**Global vs Object-Specific:** Global actions trade context for reach. They appear everywhere but cannot leverage source-record data. Object-specific actions are more powerful (predefined values, context) but only appear on one object's record page. The choice is driven by whether the action's context is always a specific record (use object-specific) or needs to be accessible from any page (use global).

**Custom (LWC/VF) vs Declarative Action Types:** Custom action types using LWC or Visualforce provide full UI control but introduce code debt, require developer involvement to change, and have surface-specific restrictions (e.g., LWC global actions only work in Field Service mobile). Declarative Create/Update/Flow action types are self-service for admins and deployable via change sets. Prefer declarative types unless the UX requirement cannot be met otherwise.

**Action Layout Field Count:** A compact action layout (4–6 fields) is faster to complete, works better on mobile, and has higher completion rates. An action layout with 15+ fields is effectively an inline edit page and should be reconsidered — possibly redesigned as a Flow or a full record edit.

## Anti-Patterns

1. **Duplicating page layout fields in action layouts** — Treating the action layout as a copy of the page layout creates a maintenance burden (two places to update per field change) and violates the purpose of the action (compact, context-specific data entry). Keep action layouts minimal: only the fields required to create a valid record.

2. **Using global actions when object-specific actions with predefined values would work** — Teams sometimes choose global actions for simplicity, then complain that parent lookups are blank and data integrity suffers. When there is a clear source record, always use an object-specific action with predefined values to auto-link the new record.

3. **Adding too many actions to a page layout** — Every action added to a page layout's mobile section that pushes total count beyond ~5 effectively hides subsequent actions behind a "More" menu. Teams add actions liberally during project delivery and never audit. The result is an overloaded action bar that users stop trusting. Apply governance: new actions require an existing action to be removed or deprioritized.

## Official Sources Used

- Salesforce Help: Quick Actions — https://help.salesforce.com/s/articleView?id=platform.actions_overview.htm&language=en_US&type=5
- Salesforce App Admin Guide: Object-Specific versus Global Actions — https://developer.salesforce.com/docs/atlas.en-us.salesforce1appadmin.meta/salesforce1appadmin/s1_admin_guide_actions_obj_vs_global.htm
- Salesforce App Admin Guide: Action Layouts — https://developer.salesforce.com/docs/atlas.en-us.salesforce1appadmin.meta/salesforce1appadmin/s1_admin_guide_actions_layouts.htm
- Salesforce Help: Set Predefined Field Values for Quick Action Fields — https://help.salesforce.com/s/articleView?id=platform.predefined_field_values.htm&language=en_US&type=5
- LWC Developer Guide: lightning__GlobalAction Target — https://developer.salesforce.com/docs/platform/lwc/guide/targets-lightning-global-action.html
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
