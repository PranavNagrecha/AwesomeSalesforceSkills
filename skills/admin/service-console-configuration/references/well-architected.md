# Well-Architected Notes — Service Console Configuration

## Relevant Pillars

- **Operational Excellence** — The primary pillar. The Service Console is explicitly an agent productivity surface. Every configuration decision (navigation rules, macros, utility bar layout, keyboard shortcuts) directly affects agent efficiency, average handle time, and error rate. A poorly configured console increases training burden, reduces first-contact resolution, and drives up escalation rates.
- **Performance** — Loading too many utility items with "Load on Start = true" increases console initialization time. Macros that update multiple fields and send emails in a single action reduce roundtrip time compared to agents doing each step manually, but macros with long instruction chains can time out. Workspace tabs should be managed — deep subtab hierarchies can slow rendering.
- **Reliability** — Macros that silently fail due to missing permissions or incorrect instruction ordering cause agents to miss SLA-critical actions (e.g., escalation emails). Permission configuration for Macros must be validated before go-live.
- **Security** — Quick Text entries and Macro instructions that auto-populate emails or field values must be reviewed for data exposure. A macro that sends a customer email containing internal-only case notes is a data leak. Quick Text entries surfaced in external chat channels should not include internal identifiers.

## Architectural Tradeoffs

**Single console app vs multiple console apps:**
Sharing one console app across multiple teams reduces configuration overhead but couples their navigation rules, utility bar, and profile assignments. Teams with meaningfully different navigation patterns (e.g., Tier-1 agents vs field service dispatchers) should have separate console apps. The overhead of two apps is lower than the ongoing friction of a single app that fits neither team well.

**Macros vs Flow automation:**
Macros are agent-triggered and synchronous — the agent initiates them and waits. They are appropriate for actions that agents consciously decide to perform (escalate, close, send a specific email). Platform-triggered automation (case status change triggers an email) belongs in Flow or Process Builder, not Macros. Do not use Macros to replace automation that should fire without agent involvement.

**Utility bar item auto-load:**
Setting `Load on Start = true` on heavy utilities (CTI softphone, Omni-Channel) improves agent readiness but increases page load time for every session. Evaluate which utilities are used immediately on login vs on-demand. Agents who handle both email and chat simultaneously benefit from Omni-Channel loading on start; agents who only use CTI for outbound calls can leave the softphone as manual-open.

## Anti-Patterns

1. **Using a standard-navigation app for a service team "because it's already configured"** — The sunk cost of existing navigation items and utility bar settings does not justify the productivity loss from forcing case-handling agents to work in standard navigation. Console navigation is the designed architecture for concurrent record work. Create a new console app.

2. **Creating macros for actions that should be automated** — If every agent in the org runs the "Set Status to Closed" macro at the end of every call, that action belongs in a Flow triggered by a field condition or quick action, not a macro. Macros should cover contextual, agent-decided actions — not universal process steps that could be automated away entirely.

3. **Overloading the utility bar with too many items** — The utility bar is a fixed footer; too many items makes it visually cluttered and increases session load time. Audit which utilities agents actually use daily. Items used rarely (e.g., Notes) can be removed from the utility bar and accessed from the record page directly.

## Official Sources Used

- Salesforce Help — Features Available in Lightning Console Apps: https://help.salesforce.com/s/articleView?id=sf.console2_features_available.htm
- Salesforce Help — Set Up the Lightning Service Console (Trailhead reference): https://trailhead.salesforce.com/content/learn/modules/service_console
- Salesforce Help — Keyboard Shortcuts for Lightning Console Apps: https://help.salesforce.com/s/articleView?id=sf.console2_keyboard_shortcuts.htm
- Salesforce Help — Macros (Service Console Macros): https://help.salesforce.com/s/articleView?id=sf.macros_def.htm
- Salesforce Help — Quick Text: https://help.salesforce.com/s/articleView?id=sf.quick_text_overview.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
