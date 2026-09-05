# Examples — Service Console Configuration

## Example 1: Creating a Service Console App for a Tier-1 Support Team

**Context:** A company's Tier-1 support team handles inbound cases and works Contacts and Accounts as reference records. They use Omni-Channel for case routing and a CTI adapter for phone. Agents currently use a standard Lightning app and lose context every time they open a contact from a case.

**Problem:** With Standard Navigation, clicking a Contact link inside a Case navigates the agent away from the case entirely, erasing their work context. Agents must use the browser back button and frequently lose unsaved changes.

**Solution:**

```
App Manager > New Lightning App
  Display Name: Support Console
  App Type: Console Navigation   ← critical — not Standard Navigation
  Navigation Items: Cases, Accounts, Contacts, Knowledge (in this order)
  Default landing tab: Cases (set explicitly, not inherited from tab order)
  Utility Bar (its own FlexiPage, owned by this app):
    - History (decorator width 340)
    - Omni-Channel (decorator height 480)
    - Macros (decorator width 360)
    - Open CTI Softphone (decorator height 480)
  User Profiles: Service Cloud Agent profile, via PermissionSet.applicationVisibilities

Workspace mappings (what Setup labels "navigation rules"):
  standard-Case       → no fieldName            → primary (workspace) tab
  standard-Account    → no fieldName            → primary (workspace) tab
  standard-Contact    → fieldName = AccountId   → subtab of the Account in Contact.AccountId
  standard-Knowledge  → no fieldName            → primary (workspace) tab
```

**Why it works:** Console Navigation enables split view — the list panel persists while the agent works records in the main workspace. Each Case opens as a primary workspace tab. When the agent clicks a Contact, `WorkspaceMapping.fieldName = AccountId` sends it to the workspace showing that Contact's Account rather than opening a fourth primary tab. Agents keep multiple cases open as separate workspace tabs and switch between them without losing state.

**The part that is easy to get wrong:** the mapping is field-driven, not focus-driven. A Contact whose `AccountId` is null has no parent workspace and still opens as a primary tab. If the requirement is really "subtab of whatever case I am on", that is not what this metadata does — the Case would have to be the lookup, and Contact has no Case lookup. Say so during design rather than discovering it in UAT.

---

## Example 2: A Macro That Sends the SLA Escalation Email

**Context:** Agents frequently need to notify a customer when a case is escalated. Without a macro they open the Email quick action, retype the subject, paste a stock body, and send — an error-prone, 90-second process.

**Problem:** Agents skip the email step roughly 20% of the time under load. The email is a contractual SLA notification.

**Solution — a `Macro` plus ordered `MacroInstruction` rows, loaded as data.** There is no Metadata API type for either object, so these ship as CSV through Data Loader or the Bulk API, `Macro` first (to get the Id) and `MacroInstruction` second.

```csv
MacroId,SortOrder,Operation,Target,Value,ValueRecord
a1B8d000000ABCDEAO,0,Select,Tab.Case,,
a1B8d000000ABCDEAO,1,Select,QuickAction.Case.Email,,
a1B8d000000ABCDEAO,2,Set,Field.EmailTemplate,,00X8d000001PqRsEAK
a1B8d000000ABCDEAO,3,Set,Field.EmailMessage.Subject,Your case has been escalated,
a1B8d000000ABCDEAO,4,Set,Field.EmailMessage.ToAddress,{!Case.ContactEmail},
a1B8d000000ABCDEAO,5,Submit,QuickAction.Case.Email,,
```

**How to read the rows:**

| Row | Why it has to be there |
|---|---|
| `0 Select Tab.Case` | `Target` is a hierarchy and "A target isn't available if its parent isn't" — the tab is the root of the grammar |
| `1 Select QuickAction.Case.Email` | The email is a quick action, not an `Operation`. `QuickAction.Case.Email` is a documented target with its own `Field.EmailMessage.*` children |
| `2 Set Field.EmailTemplate` via `ValueRecord` | `Value` and `ValueRecord` are mutually exclusive — an Id goes in `ValueRecord`, literal text in `Value` |
| `3–4 Set Field.EmailMessage.*` | `Set` is one of only five operations: `Select`, `Set`, `Insert`, `Submit`, `Close` |
| `5 Submit` | There is no "Save Record" operation; submitting the quick action is what commits it |

`SortOrder` is 0-based, and "If there's an incorrect sequence of macro instructions, the macro doesn't execute" — a gap or duplicate silently kills the whole macro rather than skipping a step.

**Why it works:** the macro drives the same quick action the agent would drive by hand, in the active workspace tab, so nothing about the console layout has to change. Verify after loading:

```sql
SELECT SortOrder, Operation, Target, Value FROM MacroInstruction
WHERE Macro.Name = 'Escalate to Tier 2' ORDER BY SortOrder
```

Then watch `MacroUsage` for a week: `ExecutionState != 'SUCCESS'` with `FailureReason = 'ACCESS'` is a permission gap, `UNSUPPORTED` is a target the object does not offer.

**What a macro cannot do here:** bind itself to a keystroke. `CustomShortcut` has no field that references a `Macro`, and custom shortcuts need a developer-registered `addEventListener()` handler in the Console Integration Toolkit first.

---

## Anti-Pattern: Treating "Subtab of Current Workspace" as a Setting That Exists

**What practitioners do:** An admin reads the Setup wording — "Workspace Tab", "Subtab of current workspace", "Subtab of the workspace with matching object" — and writes a design document, a change request, or hand-authored XML around those three choices, looking for the element that carries them.

**What goes wrong:** There is no such element. `CustomApplication.workspaceConfig` holds `mappings`, and each `WorkspaceMapping` has exactly two fields: `tab` (required) and `fieldName` (optional, "If not specified, `tab` opens as a primary tab"). The behaviour is *the presence or absence of a lookup field name*, and the parent workspace is resolved from record data. Designs written against the three-choice model produce requirements nobody can implement — most often "open this as a subtab of whichever case I am looking at" for an object that has no lookup to Case.

**Correct approach:** convert every "subtab" requirement into a sentence of the form "*`<child object>` opens under the record in `<child object>.<lookup field>`, and that parent object's tab is also in this app.*" If no such lookup exists, the requirement is not buildable as a mapping and the conversation has to happen at design time. Then write it out — one `mappings` entry per `<tabs>` entry, `fieldName` present or deliberately absent — and run `scripts/check_service_console_configuration.py`, which fails a `fieldName` that is not a field on the mapped object.

---

## Anti-Pattern: Configuring a Utility Bar and Expecting It to Belong to One App

**What practitioners do:** An admin widens the Macros panel and adds a Notes utility for the Tier-1 console, having reached the utility bar through *that app's* edit screen in App Manager.

**What goes wrong:** The Tier-2 console's footer changes too. The utility bar is not part of the app — the app holds only "the developer name of the utility bar associated with this app", and the guide warns that utility bars are shared: "if you change the utility bar in one app, it automatically changes in all apps associated with it." Reaching a shared component through one app's edit screen hides the coupling completely.

**Correct approach:** give each console app its own `UtilityBar` FlexiPage, named after the app. Before editing any existing one, run `SELECT DeveloperName, Label, UtilityBar FROM AppDefinition WHERE UtilityBar != null` and check whether two apps share an Id. If they do, clone the FlexiPage under a new name and repoint one app before making the change.
