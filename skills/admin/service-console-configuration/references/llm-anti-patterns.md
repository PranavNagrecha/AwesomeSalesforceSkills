# LLM Anti-Patterns — Service Console Configuration

Common mistakes AI coding assistants make when generating or advising on Service Console Configuration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending "Edit the Existing App to Enable Console Navigation"

**What the LLM generates:** "Go to Setup > App Manager, click Edit on your existing Lightning app, and change the Navigation Style to Console to enable split view."

**Why it happens:** LLMs infer that navigation type is a mutable setting like most other app properties. They also conflate App Manager's Edit screen (which does allow changing many properties) with the fixed `navType` field.

**Correct pattern:**

```
Console Navigation is set at app creation time and cannot be changed afterward.
To enable console navigation for an existing team:
1. Create a new Lightning app and select "Console Navigation" during the setup wizard.
2. Recreate the navigation items and utility bar from the old app.
3. Assign the same profiles.
4. Migrate agents to the new app.
```

**Detection hint:** Look for phrases like "edit the existing app and set navigation to console" or "change the navigation type." These are not valid Setup actions.

---

## Anti-Pattern 2: Adding the History Utility to a Standard Navigation App

**What the LLM generates:** "Add the History utility to your app's utility bar so agents can quickly see their recently visited records."

**Why it happens:** The History utility exists and is a common utility bar recommendation. LLMs do not differentiate between utility items that are console-only vs available in all app types — and then state the restriction as settled fact.

> UNVERIFIED (2026-09-05): the "History is console-only" restriction is Salesforce Help content. Neither
> `api_meta.txt` nor `object_reference.txt` names a History utility item at all — the Metadata API
> documents the FlexiPage *structure* but not the catalogue of standard utility components — and
> help.salesforce.com cannot be fetched to confirm it. The anti-pattern below is that an assistant asserts
> either answer without checking; the fix is to check, not to assert the opposite.

**Correct pattern:**

```
Do not state the availability of a named utility item from memory. Instead:
1. Retrieve a utility bar that already works in the target org:
   sf project retrieve start --metadata FlexiPage:<ExistingUtilityBar>
2. Copy the exact <componentName> strings from it.
3. If a component name is not present in any retrieved bar of that app type,
   say so and test it in a sandbox rather than claiming it is supported.
```

**Detection hint:** Look for any confident statement about which utility components a given app type supports, or a hand-authored `<componentName>` that was not copied out of a retrieve. Both are guesses presented as facts.

---

## Anti-Pattern 3: Conflating Quick Text and Macros

**What the LLM generates:** "Create a macro to insert a standard reply into the case email. Add the macro to the Macros utility so agents can select it when composing emails."

**Why it happens:** Both Macros and Quick Text serve agent productivity in the console, and both surface in the utility bar. LLMs confuse their roles — Macros automate multi-step record actions; Quick Text provides reusable text snippets.

**Correct pattern:**

```
Use Quick Text for reusable text snippets inserted into email, chat, or feed:
  - QuickText records; Channel is a MULTIPICKLIST, so one record can serve
    Email and Chat and the portal at once (object_reference L238905-238913)
  - Channel values come from the QuickTextChannel StandardValueSet, so there is
    no fixed five-value list to quote (api_meta L142921)
  - Set IsInsertable explicitly: it defaults true from the Quick Text page and
    the API, but false for records produced by Einstein Reply Recommendations

Use Macros for multi-step record actions driven by quick actions:
  - A Macro plus ordered MacroInstruction rows, SortOrder 0-based
  - Operation is only Select / Set / Insert / Submit / Close (+ IF/ELSEIF/ELSE/ENDIF
    from API 46.0) - there is no "Send Email" or "Post to Chatter" operation
  - Target follows the grammar Tab.<Entity> > QuickAction.<Entity>.<Name> >
    Field.<Entity>.<Field>; INSERT into text uses the .cursor / .end suffixes
  - Macros are NOT text insertion tools; they drive quick actions
```

**Detection hint:** Look for instructions to "create a macro to insert text" or "use a macro as a template." Text insertion belongs to Quick Text, not Macros.

---

## Anti-Pattern 4: Assuming Omni-Channel Utility Works Without Prior Omni-Channel Setup

**What the LLM generates:** "Add the Omni-Channel utility to your Service Console utility bar. Agents will then see their queue and incoming cases in the widget."

**Why it happens:** LLMs describe the end-state of a working Omni-Channel setup without listing the prerequisite steps. Omni-Channel setup is a multi-step process that precedes the utility bar item.

**Correct pattern:**

```
Prerequisites before adding Omni-Channel utility:
1. Enable Omni-Channel: Setup > Omni-Channel Settings > Enable Omni-Channel
2. Create a Service Channel for Cases (and other routable objects)
3. Create a Routing Configuration
4. Create a Queue and assign the routing configuration
5. Create a Presence Configuration and assign to agent profiles
6. Verify agent user has a presence configuration

Only after these steps does the Omni-Channel utility widget function for agents.
```

**Detection hint:** Look for Omni-Channel utility recommendations without mention of enabling Omni-Channel, creating Service Channels, or configuring Presence Configurations.

---

## Anti-Pattern 5: Writing Navigation Rules as a Three-Choice Setting

**What the LLM generates:** "Set all your navigation rules to Workspace Tab so agents can always get back to any record they opened."

**Why it happens:** The Setup UI labels the choices "Workspace Tab", "Subtab of current workspace", and "Subtab of the workspace with matching object", and those phrases dominate the blog posts an LLM has read. None of them is a metadata value, so the model reproduces a mental model the API cannot implement — and the unmapped default (primary tab for everything) then looks like the safe answer.

**Correct pattern:**

```
There is no "Subtab of current workspace" setting. The metadata is
CustomApplication > workspaceConfig > mappings, and each mapping has exactly two
fields: tab (required) and fieldName (optional). "If not specified, tab opens as
a primary tab" (api_meta L40044-40046).

  <workspaceConfig>
      <mappings><tab>standard-Case</tab></mappings>                          <!-- primary tab -->
      <mappings><fieldName>AccountId</fieldName><tab>standard-Contact</tab></mappings>
  </workspaceConfig>

fieldName is a lookup ON the subtab's own object POINTING AT the parent, and the
parent is resolved from record data - not from whichever tab is focused. So:
  - "Contact as a subtab of the Account" is buildable: Contact.AccountId exists.
  - "Contact as a subtab of whatever Case I am on" is NOT buildable: Contact has
    no lookup to Case. Raise this at design time, not in UAT.
  - A Contact whose AccountId is null still opens as a primary tab.

mappings is documented as required for each tab in the app, so write an entry for
every <tabs> value, including the ones that should stay primary.
```

**Detection hint:** Look for the strings "Subtab of current workspace", "Subtab of the workspace with matching object", `navRules`, `consoleComponents`, or "navigation rules section" in generated output. None of these exists in the Metadata API; their presence means the model is describing a UI it has not reconciled with the metadata.

---

## Anti-Pattern 6: Creating Macros for Actions That Should Be Automated

**What the LLM generates:** "Create a macro called 'Close Case' that sets Status to Closed and Owner to the archive queue. Agents should run it at the end of every call."

**Why it happens:** Macros are visible and concrete to configure. LLMs reach for them as a general action-automation tool without considering whether the action should be agent-triggered or platform-triggered.

**Correct pattern:**

```
Macros are for agent-decided, contextual actions — not universal process enforcement.
If every agent runs the same macro at the end of every case, the action belongs in a Flow:
  - Use a Screen Flow on a Case quick action for guided closure
  - Use a Record-Triggered Flow to auto-update Owner when Status changes to Closed

Reserve Macros for:
  - Escalation workflows that agents choose based on judgment
  - Specific email responses that vary by situation
  - Non-obvious multi-step actions that would otherwise be error-prone
```

**Detection hint:** Look for macros described as "required for every case" or "run at the end of every call." These signal process automation that should be a Flow, not a Macro.
