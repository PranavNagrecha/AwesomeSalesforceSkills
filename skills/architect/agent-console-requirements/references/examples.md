# Examples — Agent Console Requirements

## Example 1: Tier-1 Support Console for a SaaS Company

**Context:** A SaaS company with 60 Tier-1 agents handling technical support cases via email and web form. Agents work 30-50 cases per day each. The org has Service Cloud licenses for all agents and an Omni-Channel routing setup with two queues (Technical Support and Billing). No telephony integration.

**Problem:** Without explicit requirements, the admin built a standard Lightning App with a basic case list view. Agents had to navigate away from cases to check the linked Account, losing their current case context. The utility bar was populated with 12 components "just in case," which slowed console startup and confused agents with tools they never used. No macros were created, so agents typed the same email responses and status updates manually on every case.

**Solution:**

```
Console Requirements — Tier-1 Technical Support

LICENSING
- All 60 agents: Service Cloud User license
- Permission Set: "Tier-1 Console Access" — grants Run Macros permission
- No CTI adapter; Open CTI Softphone excluded from utility bar

PAGE TEMPLATES
- Case (Technical): Pinned Header template
  - Pinned Header region: Highlights Panel
    - Fields: Case Number, Status, Priority, Subject, Account Name
  - Right Sidebar: Knowledge Accordion (search articles in-context)
  - Main Canvas: Case Details (top), Related: Emails, Files, Case Comments
- Case (Billing): Pinned Header template
  - Pinned Header region: Highlights Panel
    - Fields: Case Number, Status, Subject, Account Name, Entitlement
  - Right Sidebar: none (billing agents use external billing system)

SUBTAB OBJECTS
- Account: opens as subtab under Case primary tab
- Contact: opens as subtab under Case primary tab

UTILITY BAR (5 components)
1. Omni-Channel — required (agents accept work via Omni-Channel queues)
2. History — required (agent returns to accidentally closed case)
3. Macros — required (macro runner access)
4. Notes — optional (quick note before opening a record)
5. [No CTI, no other items]

SPLIT-VIEW LIST VIEWS (per agent group)
- Tier-1 Technical: "My Open Technical Cases" — Status != Closed, RecordType = Technical, Owner = Me, sorted Priority DESC
- Tier-1 Billing: "My Open Billing Cases" — Status != Closed, RecordType = Billing, Owner = Me, sorted CreatedDate ASC

MACRO CATALOG (top 10)
1. "Acknowledge Receipt" — Update Status → In Progress; Send Email (template: Case Acknowledged); Add Case Comment "Acknowledged via macro"
2. "Request Info" — Send Email (template: Request More Information); Update Status → Waiting on Customer
3. "Resolve and Close" — Update Status → Resolved; Update Resolution field; Send Email (template: Case Resolved)
4. "Escalate to Tier-2" — Update RecordType → Tier-2; Update Queue → Tier-2 Technical; Add Case Comment "Escalated by Tier-1"
5. "Mark Duplicate" — Update Status → Closed — Duplicate; Add Case Comment "Duplicate of [manual entry]"
... (10 total documented in full macro catalog artifact)
```

**Why it works:** Every macro replaces 3-5 manual steps. The utility bar has exactly the 5 components agents actually use. The Pinned Header template keeps Case Number and Status always visible regardless of scroll position. Subtab configuration means agents check Account details without abandoning the Case tab.

---

## Example 2: Multi-Tier Console with Phone Integration

**Context:** A financial services firm with 25 Tier-1 generalists and 15 Tier-2 specialists sharing a single console app. Tier-1 handles general inquiries via phone and email; Tier-2 handles complex account disputes via email only. An Open CTI adapter for the firm's Avaya PBX is already installed and configured.

**Problem:** The admin created two separate console apps (one per tier), which meant every page layout and macro change had to be applied twice. The Open CTI Softphone was added to both apps by default, but Tier-2 agents do not use the phone — so they had a broken grey panel in their utility bar. Tier-1 agents had 10 utility bar items, which caused a 4-6 second console startup delay on each login.

**Solution:**

```
Console Requirements — Multi-Tier Financial Services Console

SINGLE CONSOLE APP: "Service Console"
- Used by both Tier-1 and Tier-2

LICENSING
- Tier-1 (25 agents): Service Cloud User license + Run Macros permission set
- Tier-2 (15 agents): Service Cloud User license + Run Macros permission set
- CTI: Tier-1 only assigned to Call Center definition (Avaya adapter)
  - NOTE: Open CTI Softphone in utility bar only renders for agents assigned
    to the Call Center; Tier-2 agents see no component (expected behavior)

PAGE TEMPLATES
- Case (General Inquiry) — for Tier-1:
  - Pinned Header: Highlights Panel (Case Number, Status, Priority, Account Name, Phone)
  - Right Sidebar: Knowledge Accordion
  - Assigned to: Tier-1 Console profile via App Builder
- Case (Account Dispute) — for Tier-2:
  - Pinned Header: Highlights Panel (Case Number, Status, Dispute Amount, Account Name)
  - Right Sidebar: none
  - Main Canvas: Case Details, Related: Account History (custom), Email Messages
  - Assigned to: Tier-2 Console profile via App Builder

UTILITY BAR (6 components — shared bar)
1. Omni-Channel
2. History
3. Macros
4. Open CTI Softphone (renders for Tier-1 Call Center members; blank for Tier-2 — confirmed acceptable)
5. Notes
6. (6th slot reserved for future AI copilot panel)
NOTE: Previous 10-component bar reduced to 6; startup time tested at < 2 seconds

SUBTAB OBJECTS
- Account: subtab under Case
- Contact: subtab under Case
- Financial Account (custom object): subtab under Case for Tier-2 dispute workflows

MACRO CATALOG
Tier-1 Macros (shared):
1. "Log Call and Acknowledge" — Log Call (Quick Action); Update Status → In Progress; Send Email (acknowledged template)
2. "Transfer to Tier-2" — Update RecordType → Account Dispute; Change Queue → Tier-2 Disputes; Add Comment

Tier-2 Macros (Tier-2 profile only):
1. "Request Supporting Documents" — Send Email (documents template); Update Status → Waiting on Customer; Set Follow-up Date +5 days
2. "Dispute Resolved — Credit Issued" — Update Status → Resolved; Update Resolution; Send Email (credit confirmation template)
```

**Why it works:** A single console app with profile-driven layout assignments eliminates the dual-maintenance problem. The Open CTI Softphone component gracefully renders blank for agents not in the Call Center definition — no error, no broken state. The utility bar reduction from 10 to 6 components measurably improved startup time. Tier-2 macros are scoped to the Tier-2 profile so they do not pollute the Tier-1 macro list.

---

## Anti-Pattern: Building the Console Without a Macro Inventory

**What practitioners do:** Configure the Lightning Service Console (app, page layouts, utility bar) and defer macro creation to "after go-live when we know what agents actually need."

**What goes wrong:** Agents go live without macros and immediately develop inconsistent workarounds. Some agents create personal macros; others skip the macro runner and perform actions manually. By week 3 there are 40 private macros of varying quality, no shared macros, and agents are doing the same tasks in different ways — producing inconsistent case comments, email replies, and status values. Cleaning this up requires a full macro audit and retraining.

**Correct approach:** Spend 2-3 hours during requirements gathering shadowing agents or reviewing case history to identify the top 10-15 repeated action sequences. Document each as a candidate macro with ordered steps before the console is built. The admin can create all macros during the configuration phase so agents launch with a complete shared macro library on day one.
