# Examples — Service Console Configuration

## Example 1: Creating a Service Console App for a Tier-1 Support Team

**Context:** A company's Tier-1 support team handles inbound cases and works Contacts and Accounts as reference records. They use Omni-Channel for case routing and a CTI adapter for phone. Agents currently use a standard Lightning app and lose context every time they open a contact from a case.

**Problem:** With Standard Navigation, clicking a Contact link inside a Case navigates the agent away from the case entirely, erasing their work context. Agents must use the browser back button and frequently lose unsaved changes.

**Solution:**

```
App Manager > New Lightning App
  Display Name: Service Console
  App Type: Console Navigation   ← critical — not Standard Navigation
  Navigation Items: Cases, Contacts, Accounts, Knowledge (in this order)
  Utility Bar:
    - History (panel width 340, height 480)
    - Omni-Channel (panel width 300, height 480, Load on Start = true)
    - Macros (panel width 340, height 480)
    - Open CTI Softphone (panel width 300, height 480, Load on Start = false)
  User Profiles: Service Cloud Agent profile

Console Navigation Rules (edit app > Console Navigation tab):
  Case        → Workspace Tab
  Contact     → Subtab of current workspace
  Account     → Subtab of current workspace
  Knowledge   → Subtab of current workspace
```

**Why it works:** Console Navigation enables split view — the sidebar list view persists while the agent works records in the main workspace. Each Case opens as a primary workspace tab. When the agent clicks a Contact from the Case, it opens as a subtab inside that Case workspace, preserving the Case context. Agents can have multiple cases open simultaneously as separate workspace tabs and switch between them without losing state.

---

## Example 2: Creating a Macro for "Escalate to Tier 2"

**Context:** Agents frequently need to perform three steps when escalating a case: change Status to "Escalated", change Owner to the Tier-2 queue, and send a standard email to the customer. Without a macro, agents do this manually across multiple page sections — an error-prone, 90-second process.

**Problem:** Agents skip the email step roughly 20% of the time due to the cognitive load of remembering all three actions under pressure. The email is a contractual SLA notification.

**Solution:**

```
Setup > Macros > New Macro
  Macro Name: Escalate to Tier 2
  Description: Updates Status, reassigns Owner, sends SLA email

Macro Instructions (in order):
  1. Select: Object = Case
     Action: Update Field
     Field: Status
     Value: Escalated

  2. Select: Object = Case
     Action: Update Field
     Field: Owner
     Value: [Tier 2 Support Queue ID]

  3. Select: Object = Case
     Action: Send Email
     Email Template: [Escalation Notification template]
     From: [Support email address]
     To: Case Contact Email

  4. Select: Object = Case
     Action: Save Record
```

Then in Keyboard Shortcuts (console app settings), bind a shortcut key to this macro so agents can escalate with a single keystroke.

**Why it works:** Macros execute all instructions in sequence against the currently active workspace record. The Save step ensures the field changes are committed before the email fires. Because the macro is surfaced in the Macros utility panel, agents never need to navigate away from the active case.

---

## Anti-Pattern: Configuring a Utility Bar on a Standard Navigation App and Expecting Console-Only Items to Work

**What practitioners do:** An admin adds the History and Omni-Channel utilities to an existing standard-navigation app for service agents, reasoning that the utility bar should work the same regardless of app type.

**What goes wrong:** The History utility does not appear in the Setup utility picker when editing a standard-navigation app — or if added via metadata, it silently fails to render. Omni-Channel utility renders, but agents cannot see incoming work requests in split view because there is no split view in standard navigation. The agent experience is incomplete and confusing.

**Correct approach:** Create a new Lightning app with Console Navigation. Only console apps unlock split view, workspace tabs, subtabs, and the History utility. Migrate agents to the new console app and retire the standard app for this team.
