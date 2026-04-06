# LLM Anti-Patterns — Agent Console Requirements

Common mistakes AI coding assistants make when generating or advising on Agent Console Requirements.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Standard Lightning Page Template for Console Case Pages

**What the LLM generates:** "Create a new Lightning page for the Case object, add the Highlights Panel and related list components, then assign the page to your console app and the relevant profiles."

**Why it happens:** The LLM has strong training signal for the general Lightning App Builder flow (create page → add components → assign), which works correctly for standard Lightning apps. The console-specific requirement to select the Pinned Header template is a detail that is easy to omit because the assignment step works syntactically without it.

**Correct pattern:**

```
When creating a Case page for the Lightning Service Console:
1. In App Builder, create a new Lightning page → App Page
2. On the template picker, select "Header and Right Sidebar" (the Pinned Header template)
3. Place the Highlights Panel component in the "Header" region — NOT the main canvas
4. Add Knowledge Accordion to the Right Sidebar region if applicable
5. Assign the page to the console app and relevant profiles
```

**Detection hint:** If the output describes "add Highlights Panel to the page" without specifying the Header region or Pinned Header template, the template selection step is missing.

---

## Anti-Pattern 2: Assuming Run Macros Permission Is Included in Standard Profiles

**What the LLM generates:** "Agents with the Service Cloud User profile can run macros from the utility bar. Just create and publish the macros and they will appear for all agents."

**Why it happens:** The LLM generalizes that profile-level CRM access (edit cases, send emails) extends to automation features. The Run Macros permission is an explicit platform permission that is absent from all standard profiles, including Service Cloud User. This absence is a non-obvious Salesforce-specific detail that LLMs miss because the pattern (feature X requires permission Y) is not consistently documented in the training corpus.

**Correct pattern:**

```
Macros require an explicit user permission not in any standard profile:

1. Create a permission set: "Agent Productivity — Macros"
2. Add user permission: "Run Macros" (and optionally "Manage Macros" for leads/admins)
3. Assign the permission set to all console agent users
4. Verify by testing macro execution as a non-admin agent user in a sandbox
```

**Detection hint:** Any output that says agents can run macros without mentioning permission set assignment or the Run Macros permission should be flagged.

---

## Anti-Pattern 3: Treating the Lightning Service Console as a Normal Lightning App

**What the LLM generates:** "The Lightning Service Console is a Lightning App configured for support agents. You can add the case list view to the navigation bar, and agents will use the standard navigation to open cases."

**Why it happens:** The LLM conflates the Lightning App configuration framework (which is general) with the console-specific split-view navigation model. Standard Lightning app navigation replaces the current page when a record is clicked. Console split-view navigation opens records as tabs without replacing the current context. The behavioral difference is architecturally significant and often missed.

**Correct pattern:**

```
Lightning Service Console uses split-view navigation, not standard page navigation:

- Records open as PRIMARY TABS (case) or SUBTABS (related account/contact)
- Clicking a case in the split-view list does NOT navigate away from the current tab
- Multiple primary tabs remain open simultaneously (up to 10)
- Subtab objects must be explicitly configured: App Manager → console app → Subtab Objects
- Do NOT use standard Lightning navigation item links for console workflows
  — configure the split-view list panel as the primary case entry point
```

**Detection hint:** Outputs describing "navigation bar items" or "standard list views" for case access in the console are likely applying standard Lightning App navigation logic instead of console split-view.

---

## Anti-Pattern 4: Adding the Open CTI Softphone to the Utility Bar for All Agents

**What the LLM generates:** "Add the Open CTI Softphone to the utility bar so all agents can access phone functionality. It will automatically connect to your telephony system."

**Why it happens:** The LLM treats utility bar component inclusion as purely additive — adding a component either works or does nothing. In reality, the Open CTI Softphone requires (1) an installed CTI adapter managed package, (2) an active Call Center definition referencing the adapter, and (3) agents assigned to the Call Center. Without these prerequisites, the component renders as a blank grey panel with no error message. The LLM also misses that agents not assigned to the Call Center should not have the component added if it causes visual confusion.

**Correct pattern:**

```
Open CTI Softphone prerequisites before adding to utility bar:
1. Confirm CTI adapter (managed package) is installed from AppExchange
2. Confirm a Call Center definition file is imported and active in Setup → Call Centers
3. Confirm agents who need phone access are assigned to the Call Center
   (Setup → Call Centers → Manage Call Center Users)
4. The Softphone component renders only for agents assigned to the Call Center
   — for agents not assigned, the component slot is empty (not broken)
5. If NO telephony integration exists, OMIT this component entirely
```

**Detection hint:** Any recommendation to add Open CTI Softphone without first confirming a CTI adapter is installed and a Call Center is configured should be flagged.

---

## Anti-Pattern 5: Scoping Macros Only to What Agents Currently Do Manually

**What the LLM generates:** "Interview agents about what they do manually today and create macros to automate those steps. Start small — create 3-5 macros and add more over time."

**Why it happens:** The LLM applies a conservative "crawl before you walk" framing that is appropriate for some implementations but misses the compounding productivity cost of under-investment in macros at go-live. Agents form habits in the first two weeks on a new system. If they launch without a complete macro library, they develop manual habits that persist even after macros are added later.

**Correct pattern:**

```
Macro requirements should be gathered proactively, not reactively:

1. Shadow agents (or review case history) to identify the top 15 repeated action sequences
2. Document all 15 as candidate macros during requirements — before build begins
3. Prioritize the top 10 for go-live; defer 5 to post-launch if needed
4. Include in requirements: macro name, trigger scenario, ordered steps, sharing scope
5. Build and test all go-live macros before UAT — do not defer to post-go-live
6. Reserve Manage Macros permission for team leads who can create/share new macros
   without admin involvement as workflows evolve
```

**Detection hint:** Outputs recommending 3-5 macros to "start with" or "add more later" without a structured inventory process are likely under-scoping the macro catalog. Confirm that at least 10 macro candidates were identified before accepting the requirements as complete.

---

## Anti-Pattern 6: Ignoring the 200-Record Split-View List Limit

**What the LLM generates:** "Configure the console with a default list view showing all open cases. Agents can filter from there as needed."

**Why it happens:** The LLM treats list views as infinitely scrollable and does not surface the 200-record display limit specific to the console split-view panel. In low-volume environments this works. In high-volume contact centers with 500+ open cases in a queue, 300 cases are silently hidden from agents with no warning.

**Correct pattern:**

```
Split-view list panel has a hard limit of 200 records displayed:

Requirements must include:
1. Pre-filtered list views per agent tier or queue — NOT a catch-all open cases view
2. Filters that partition the queue into <200-record segments:
   - By queue membership (agent's assigned queue only)
   - By priority (High/Critical only for first-pass views)
   - By creation date window (Last 7 days, not all-time)
3. Document the expected queue depth per tier: if any queue exceeds 200 cases regularly,
   add a secondary filtered view for the overflow
4. Do not rely on agents to self-filter an unfiltered view — they will miss cases
```

**Detection hint:** Any output that recommends a default "all open cases" or unfiltered list view for the console split-view panel in a contact center with 50+ agents should be flagged as missing the 200-record limit constraint.
