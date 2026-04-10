# Well-Architected Notes — CPQ Custom Actions

## Relevant Pillars

- **Operational Excellence** — Custom actions reduce rep error rates by surfacing the right operation at the right moment in the QLE workflow. Poorly designed actions (missing conditions, unclear labels, too many buttons) create confusion and increase support tickets. Keeping actions lean, purposeful, and well-labeled is an operational excellence concern.
- **Security** — URL actions that pass record IDs to external systems must be evaluated for data exposure risk. The CPQ merge field tokens embed Salesforce record IDs in outbound URLs — ensure the external URL target uses HTTPS, and that the CSP Trusted Sites list is tightly scoped. Flows launched via custom actions run in the context of the clicking user and are subject to standard Salesforce FLS and CRUD — never assume elevated permissions inside the Flow.
- **Reliability** — The five-action-per-context hard limit, silent drop behavior, and runtime failures from inactive Flows are all reliability risks. Reliable CPQ action design requires active count monitoring, Flow activation gates in deployment pipelines, and documented rollback procedures when actions conflict.
- **Performance** — Custom actions of type `Calculate` or `Save` trigger the CPQ pricing engine or save operation, which can be expensive on large quotes. Adding multiple `Calculate` buttons at the Line Item level (one per row) means reps can inadvertently trigger many recalculations. Prefer `Global` location for actions that trigger quote-level operations.

## Architectural Tradeoffs

**Flow action vs. URL action:** Flow actions keep all logic inside the Salesforce platform boundary and respect FLS/CRUD. URL actions are simpler to configure but move context (and potentially sensitive data) outside the Salesforce security boundary. Prefer Flow actions for any logic that reads or writes Salesforce data. Reserve URL actions for pure navigation to external reference tools where no Salesforce data is written.

**Consolidation vs. proliferation:** As business requirements grow, teams tend to add more custom action buttons rather than extending existing Flows. The five-action limit forces discipline — teams that consolidate related actions into a single Flow with a choice screen at the start have more flexibility and a cleaner rep UX. Teams that proliferate individual action records hit the limit and then face a refactoring project.

**Conditional visibility vs. always-visible with in-Flow guard:** Condition records on custom actions are evaluated at page load and do not update dynamically. An alternative is to make the button always visible and implement the condition check as the first element in the Flow, displaying a message if the condition is not met. This is simpler to implement but results in more button clicks that end in "not allowed" messages. Choose based on how often reps would click the button inappropriately.

## Anti-Patterns

1. **Creating more than five actions per context without consolidation** — Exceeding the five-action limit produces silent rendering failures that are difficult to diagnose. The correct approach is to consolidate multiple related operations into a single Flow with a branching choice screen, keeping the visible button count within limits.
2. **Using Flow conditional logic or Apex triggers to control custom action visibility** — Neither Flows nor Apex triggers affect CPQ custom action rendering. The CPQ component reads its own condition engine at page load. Implementing visibility control outside the CPQ condition framework wastes development effort and produces no result.
3. **Assuming custom actions are available on the Lightning record page** — Custom actions render only within CPQ-managed screens (QLE, configurator, amendment). Building rep workflows that depend on accessing a custom action from the standard Quote record page will fail because the QLE overlay hides standard Lightning actions.

## Official Sources Used

- Salesforce CPQ Custom Actions Help — https://help.salesforce.com/s/articleView?id=sf.cpq_custom_actions.htm
- Add a Linking Custom Action to the QLE — https://help.salesforce.com/s/articleView?id=sf.cpq_custom_actions_linking.htm
- Apex Developer Guide (Invocable Methods) — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_classes_annotation_InvocableMethod.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Content Security Policy (CSP) Trusted Sites — https://help.salesforce.com/s/articleView?id=sf.csp_trusted_sites.htm
