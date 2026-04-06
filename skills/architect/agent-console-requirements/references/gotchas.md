# Gotchas — Agent Console Requirements

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Pinned Header Template Is Not the App Builder Default

**What happens:** An admin creates a new Lightning page for the Case object in App Builder, selects the console app as the assignment target, and the page is deployed. Agents report that the Highlights Panel scrolls off the screen when they view long case records. The case number and status disappear, and agents cannot see key identifiers while working the lower sections of the page.

**When it occurs:** Every time a new console case page is created without explicitly choosing the Pinned Header template in the App Builder template picker. The wizard defaults to a standard two-column or three-column template, not the Pinned Header. This only affects console apps — standard Lightning apps do not use Pinned Header — so admins unfamiliar with console-specific templates miss it.

**How to avoid:** When creating a new Lightning page for a console app, choose "App Page" and on the template picker step explicitly select "Header and Right Sidebar" (the Pinned Header variant) rather than the default column templates. After assignment, verify that the Highlights Panel is placed in the header region (labeled "Header" in the canvas), not the main body. Test by opening a long case record in the console and scrolling — the header should remain pinned.

---

## Gotcha 2: Utility Bar Components Load at Console Startup, Not on Demand

**What happens:** An admin adds 10+ utility bar components to the console app — Open CTI Softphone, Omni-Channel, History, Notes, Macros, Recent Items, Chatter, Flow, a custom LWC, and a third-party app. Agents report the console takes 8-12 seconds to load after login. The issue persists across browsers and machines, suggesting it is not a local hardware problem.

**When it occurs:** Every console session startup. Unlike main-area Lightning components that lazy-load when the page scrolls into view, utility bar components initialize immediately when the console app loads. Each component makes its own API calls, renders its DOM, and holds memory for the full session. More components compound the startup cost linearly. Custom LWCs in the utility bar with synchronous `@wire` calls or `connectedCallback` API calls are the worst offenders.

**How to avoid:** Cap the utility bar at 6-8 components during requirements. Require justification for every item: if an agent cannot articulate a use case for the component in the first 5 minutes of their shift, it should not be in the utility bar. Review custom LWCs being added to the utility bar — they must use asynchronous `@wire` calls and must not perform heavy DOM work in `connectedCallback`. Test console startup time with the full utility bar configured before go-live.

---

## Gotcha 3: Run Macros Is Not Included in Any Standard Profile

**What happens:** Agents go live on the console, the macro catalog is built and shared, but agents report they cannot find or run macros. The Macro component is in the utility bar and the macros are published, but the runner shows no macros available.

**When it occurs:** When the Run Macros user permission is not explicitly assigned. This permission is absent from all standard Salesforce profiles — System Administrator, Standard User, and even Service Cloud User profiles do not include it by default. Because macros are treated as a separate automation layer, Salesforce gates them behind an explicit permission that must be added via a custom permission set.

**How to avoid:** Include "Run Macros" permission set assignment as a required item in the pre-go-live checklist during requirements gathering. Create a dedicated permission set (e.g., "Agent Productivity — Macros") that includes Run Macros and optionally Manage Macros. Assign this permission set to all console agents at the same time as the console app permission set. Test macro execution with a non-admin agent user before go-live.

---

## Gotcha 4: Subtab Object Configuration Is Separate from Page Layout Assignment

**What happens:** The admin assigns a polished Pinned Header case page in App Builder and assigns it to the console app. Agents open cases, but clicking the Account link from a case opens a brand new primary tab rather than a subtab. After a few hours of work, agents have 8-10 primary tabs open (Cases and Accounts interleaved), consuming all available primary tab slots.

**When it occurs:** When Subtab Objects are not configured in the console app setup. Lightning App Builder page assignment and console subtab object configuration are two separate settings. Creating and assigning a page to the console app does not automatically make related records open as subtabs.

**How to avoid:** During requirements, produce an explicit list of Subtab Objects: which related objects should open as subtabs under the primary Case tab (typically Account, Contact, Asset, and any relevant custom objects). Configure these in the console app setup: App Manager → Edit Console App → Navigation Items → Subtab Objects. Verify by opening a Case in the console and clicking a related Account — it should appear as a subtab within the Case primary tab, not as a new top-level tab.

---

## Gotcha 5: Macros Cannot Branch or Execute Conditionally

**What happens:** During requirements, agents request a "smart macro" that sends a different email template depending on the case priority — a Standard Acknowledgment for Medium priority and an Urgent Escalation for High priority. The admin attempts to configure this in the macro builder and discovers it is not possible.

**When it occurs:** Any time requirements scope macros to include conditional logic, loops, or branching based on field values. The macro engine is a linear instruction runner — it executes steps in order without evaluating conditions. It cannot evaluate field values at runtime to choose different branches.

**How to avoid:** During requirements gathering, be explicit with stakeholders that macros are linear sequences. Where conditional behavior is needed, two options exist: (1) create two separate macros (one per scenario) and let agents choose the correct one, or (2) implement a Lightning Flow invoked via a Quick Action that provides branching logic — the macro can call the Quick Action, but the branching happens inside the Flow. Document which macro candidates require conditional logic early enough to route them to the Flow or Apex path during design.
