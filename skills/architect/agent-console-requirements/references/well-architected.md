# Well-Architected Notes — Agent Console Requirements

## Relevant Pillars

- **User Experience** — The console workspace is the primary environment where support agents spend their entire working day. Poor layout decisions (wrong page template, overloaded utility bar, missing subtab objects) directly reduce agent productivity and increase average handle time. Well-Architected demands that the console be designed around real agent workflows, not default configurations.
- **Operational Excellence** — A well-structured macro catalog and standardized page layouts reduce training time, enforce consistent case handling processes, and make onboarding new agents faster. Poorly designed consoles create undocumented workarounds that are invisible to supervisors and hard to maintain as the team scales.
- **Scalability** — Console performance degrades predictably with the number of utility bar components, open primary tabs, and simultaneous users. Requirements that account for agent concurrency, tab limits, and utility bar constraints produce a console that performs well at 10 agents and still performs at 200.
- **Security** — The Pinned Header template and page layout assignments control which fields agents see on a case page. Incorrect layout assignments can expose sensitive fields (SLA data, internal cost fields, entitlement details) to agents who should not see them. Permission sets for macros and console access must be scoped to the correct agent populations.
- **Reliability** — A console that crashes, hangs on startup, or produces broken utility bar components (grey CTI panel, non-rendering Omni-Channel widget) causes agents to fall back to manual processes or log out and back in — both of which reduce case throughput. Requirements that validate component prerequisites (CTI adapter configured, Omni-Channel licensed) before components are added to the utility bar prevent post-go-live reliability issues.

## Architectural Tradeoffs

**Single console app vs multiple console apps per tier:** A single console app with profile-driven page layout assignments is almost always preferable to multiple apps. Multiple apps create a maintenance multiplication problem — every layout, utility bar, or subtab change must be applied N times. The tradeoff is that a single app requires careful profile/permission-set segmentation in Lightning App Builder to deliver the right layout to the right agent. For most organizations (up to 5 tiers), a single console app is the correct call. More than 5 tiers with fundamentally different workflow tooling may justify separate apps, but this threshold is rarely reached.

**Macros vs Flow vs Apex for agent automation:** Macros are the correct first choice for any sequential UI action sequence that runs on a single case record and requires no conditional logic. Flow (invoked as a Quick Action or screen flow from the console) is correct when conditional branching, loops, or multi-object writes are needed. Apex (invoked from a Flow or Quick Action) is correct when complex DML or integration callouts are needed. Requirements that push macro candidates into Flow or Apex without justification add unnecessary development complexity and remove the admin-maintained, no-deploy-required nature of macros.

**Pinned Header with right sidebar vs full-width layout:** The Pinned Header with right sidebar sacrifices horizontal screen real estate on the main canvas for the Knowledge Accordion. For knowledge-heavy workflows (agents regularly look up articles during case resolution), this is the right tradeoff. For workflows where agents rarely reference Knowledge — such as highly scripted billing dispute processes — the right sidebar takes space away from case detail fields and the full-width Pinned Header (without sidebar) may serve agents better. Capture this distinction per case record type during requirements.

## Anti-Patterns

1. **Copy-pasting a non-console Lightning page into the console app** — Taking an existing Case Lightning page built for standard use and assigning it to the console app without switching the template. The page renders but lacks the Pinned Header template, causing the Highlights Panel to scroll off-screen. Agents lose case context continuously. Prevention: always create console pages from scratch using the Pinned Header template, not by reassigning existing standard pages.

2. **Adding utility bar components as a hedge against future needs** — Populating the utility bar with every possible component "in case agents might need it someday," resulting in 10-15 utility bar items and 6-10 second startup times. Console startup performance is a direct function of utility bar component count. Every component needs a clear, present-day use case to earn a place in the utility bar.

3. **Deferring macro creation to post-go-live** — Launching the console without a shared macro library forces agents to develop inconsistent personal macros or skip automation entirely. By the time the gap is recognized, agents have formed habits that are hard to change and the organization has no visibility into how cases are actually being handled. Macro requirements must be gathered and built before go-live.

## Official Sources Used

- Lightning Service Console Overview — https://help.salesforce.com/s/articleView?id=sf.console2_overview.htm
- Set Up Lightning Service Console — https://help.salesforce.com/s/articleView?id=sf.console2_lex_app_setup_overview.htm
- Customize Lightning Service Console Pages — https://help.salesforce.com/s/articleView?id=sf.console2_lex_pages.htm
- Macros in Service Cloud — https://help.salesforce.com/s/articleView?id=sf.macros_overview.htm
- Utility Bar in Lightning Apps — https://help.salesforce.com/s/articleView?id=sf.console2_utilities.htm
- Open CTI Developer Guide — https://help.salesforce.com/s/articleView?id=sf.cloud_cti_api_overview.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/well-architected/overview
