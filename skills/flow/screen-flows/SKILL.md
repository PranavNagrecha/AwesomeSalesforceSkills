---
name: screen-flows
description: "Use when designing or reviewing interactive Flow screen experiences, including navigation, validation, screen component choice, custom LWC screen components, and user-safe commit timing. Triggers: 'screen flow validation', 'back button behavior in flow', 'custom flow screen component', 'screen flow UX'. NOT for building the custom LWC that renders on a screen — use flow/flow-screen-lwc-components. NOT for per-field validation that blocks Next — use flow/flow-screen-input-validation-patterns."
category: flow
salesforce-version: "Spring '25+"
well-architected-pillars:
  - User Experience
  - Reliability
  - Operational Excellence
tags:
  - screen-flows
  - flow-ux
  - screen-components
  - flow-validation
  - navigation
triggers:
  - "how should i design a screen flow"
  - "screen flow validation is confusing"
  - "back button behavior in flow"
  - "custom lwc screen component in flow"
  - "when should screen flow save data"
  - "convert checkbox group selections to a collection"
  - "loop over multi-select picklist values in a flow"
inputs:
  - "how many screens the interview needs and where data should be committed"
  - "which standard or custom screen components are required"
  - "how validation, back navigation, cancel, and mobile usage should work"
outputs:
  - "screen-flow UX recommendation for navigation, validation, and commit timing"
  - "review findings for weak screen design or risky save placement"
  - "guidance for using standard components versus custom LWC screen components"
dependencies: []
version: 2.1.1
author: Pranav Nagrecha
updated: 2026-10-20
---

Use this skill when the Flow is interactive and the quality of the user journey matters as much as the automation logic. Screen flows succeed when they guide the user through a deliberate sequence, validate at the right moments, and commit data only where the consequences are clear. They become fragile when navigation, validation, and side effects are all mixed together casually.

The three most common screen-flow design failures: (1) DML happens on screen 2 of 6, so clicking Back from screen 5 leaves half-committed data, (2) custom LWC screen component's validation doesn't integrate with the Flow runtime, so users hit Next through invalid inputs, (3) screen count grows from 3 to 11 over iterative "just one more screen" additions until the flow is unusable on mobile. This skill exists to prevent those.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.

Gather if not available:
- How many decision points and data-entry steps are truly necessary for the user to complete the task?
- Which fields can rely on standard screen components, and which require a custom LWC because the runtime UX truly differs?
- At what point should the flow create or update data, and what should happen if the user clicks Back, Cancel, or Next with invalid inputs?
- Who is the target user (internal employee on desktop, field agent on mobile, Experience Cloud customer)?
- Will this flow be embedded as a Quick Action, Lightning Record Page component, utility bar flow, or standalone URL?

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Where does the first record change happen, and can the user still go Back after it? | Early DML makes Back and Cancel misleading (Gotcha 1). | A commit point after the review screen, or a stated staging reason. |
| Which inputs are standard components and which need a custom LWC? | Custom components must carry the validation contract (Gotcha 2). | A gap list per custom component and an owner. |
| How many screens, and on which surface? | Surface and count set the Back/Cancel semantics (Gotchas 3 and 7). | A screen budget per surface. |
| Are Back and Finish enabled on the right screens? | `allowBack` and `allowFinish` are per-screen properties (Gotchas 5 and 8). | A per-screen navigation table. |
| Do any multi-select outputs feed a Loop, Get Records or Transform? | The output is a semicolon-delimited string (Gotcha 11). | A conversion step in the flow. |
| Should returning to a screen keep or reset the user's inputs? | `inputsOnNextNavToAssocScrn` decides (Gotcha 12). | UseStoredValues or ResetValues per component. |
| Who runs the flow: internal user, mobile agent, or site visitor? | Mobile and Experience Cloud change layout and access (Gotchas 6 and 9; UNVERIFIED 2026-10-20, Help-level). | The audience and a device or guest-access review. |

A proper configuration adds a deliberate commit point, a validation contract for every custom component and explicit navigation properties, which "just adding screens" leaves to defaults.

## Core Concepts

Screen flows are interviews, not pages. That means the experience is stateful, sequential, and sensitive to where the design commits work. A strong screen flow keeps the user focused on entering or confirming information. A weak one starts performing irreversible actions too early or makes validation unpredictable between screens.

### Commit Timing Is A UX Decision

If the flow creates or updates records before the user reaches a natural confirmation point, Back and Cancel become much harder to reason about. In many cases, the best pattern is to gather inputs first, show a summary or final confirmation, and only then perform the final DML.

| Commit placement | When correct | When wrong |
|---|---|---|
| Very early (screen 2 of 6) | Side effects are idempotent AND user can't navigate back | User expects Back/Cancel to undo; partial commits confuse |
| In the middle (screen 4 of 6) | Staged commits are business-meaningful (e.g., "Reserve" then "Confirm") | Staging isn't part of the business model; users confused by half-state |
| At the end (after review screen) | Most cases — the canonical pattern | Business needs true in-progress state persistence across sessions |
| Never (ephemeral flow) | Wizards that only display data or produce a PDF | Data actually needs to persist |

### Standard Components Are Usually Better Defaults

Flow screen components cover many common needs without custom code. Reach for a custom LWC screen component only when the interaction model, validation behavior, or rendering requirement truly exceeds what standard screen elements provide.

Standard screen components handle (UNVERIFIED 2026-10-20: this component list is a Help list, not in the corpus; the metadata field types are in api_meta 264 L74413-74441):
- Text, Number, Date, DateTime, Email, URL, Phone inputs
- Picklist, Multi-select Picklist, Radio Buttons, Checkbox, Checkbox Group
- Lookup (single- and multi-select)
- Dependent Picklists (controlling/dependent relationships)
- Rich Text display
- File Upload
- Data Table (including editable)
- Address compound input

**Multi-select choice components output a string, not a collection.** A `MultiSelectCheckboxes` or `MultiSelectPicklist` screen field "stores its field value as a concatenation of the user-selected choice values, separated by semicolons" and supports only the string data type (api_meta 264 L74442-74447, L74361-74364). Feeding that string into a Loop, a Get Records filter or a Transform element needs a conversion to a collection first. UNVERIFIED (2026-10-20): that Checkbox Group, Choice Lookup and Multi-Select Picklist are "explicitly incompatible with the Transform element", that they need the Lightning runtime, that Checkbox Group became a reactive source in Winter '24 (Beta in Spring '23) and that its choices can be backed by a multi-select picklist field with record-type awareness (since Spring '23) are Help and release-note statements, not corpus lines. Value retention is metadata-controlled: `inputsOnNextNavToAssocScrn` is `UseStoredValues` (default) or `ResetValues` and applies to screen components in API 51.0 and later and to record fields in API 57.0 and later (api_meta 264 L74469-74480), so the earlier claim that these components "keep no built-in memory" on runtime v58 and earlier is CONTRADICTED for flows at those API versions; UNVERIFIED: what a pre-51.0 flow or the "Lightning runtime version 58" number does.

A custom LWC screen component is warranted when you need: cascading reactive UI between multiple fields on the same screen, real-time external-system validation, a rendering that truly isn't expressible with standard components (drag-and-drop, inline image annotation, etc.), or when a reusable LWC you already own must be surfaced.

### Custom Screen Components Need A Validation Contract

A custom LWC used in Flow has to cooperate with Flow runtime validation intentionally. That means implementing the right methods and making sure internal validation, externally supplied error messages, and displayed errors stay consistent with how the user moves between screens.

Required contract for Flow-compatible LWCs:
- `@api validate()` method returning `{ isValid: boolean, errorMessage?: string }`; the flow calls it when it moves to the next screen or finishes, and `setCustomValidity()` / `reportValidity()` are the hooks that receive and render external and internal errors (lwcguide use-flow-validate-external-internal-methods).
- `@api`-exposed properties aligning with Flow variable types.
- `FlowAttributeChangeEvent` dispatched when internal state changes affect Flow variables.
- `FlowNavigationNextEvent` (optional) when the component wants to force advancement.

Missing any of these creates the "Next clicks past invalid data" class of bugs.

### Navigation Should Feel Predictable

The number of screens, presence of a Back path, and clarity of button labels all shape the experience. If a flow has too many screens or too much hidden branching, users stop understanding where they are in the process.

**Heuristic (UNVERIFIED 2026-10-20: a rule of thumb, not a documented limit):** < 4 screens feels like a form; 4–7 screens feels like a wizard; > 7 screens feels like a maze. If the flow needs more than 7 screens, reconsider: is this one task or two? Can some screens be combined? Does a custom LWC display replace a multi-screen sequence?

## Common Patterns

### Pattern 1: Gather, Review, Then Commit

**When to use:** Any flow where the user enters meaningful data or confirms a business transaction.

**Structure:**
```text
Screen 1: Collect inputs (required fields, defaults where safe)
Screen 2: Collect additional inputs (conditional on Screen 1's answers)
Screen 3: Review screen — read-only display of ALL values the user entered + "Confirm" button
[On Confirm click → Create Records / Update Records / Invoke Apex action]
Screen 4: Confirmation — "Done. Record created: <link>"
```

**Why not the alternative:** Early record mutation makes cancellation and back-navigation behavior harder to trust; the user reasonably expects Back and Cancel to undo their changes.

### Pattern 2: Standard Components First, Custom Component Only For Real Gaps

**When to use:** Most inputs are standard, but one part of the experience needs custom UX or validation.

**Structure:**
```text
Screen 1: Standard components (Name, Status, Date)
Screen 2: STANDARD fields + ONE custom LWC component for the exceptional interaction
          (e.g., a reactive product configurator that depends on Screen-1's selections)
Screen 3: Review + commit (Pattern 1 from here)
```

**Why not the alternative:** Rebuilding entire screens as custom LWCs raises maintenance cost, bypasses Flow Builder's accessibility features, and makes the flow harder for admins to adjust.

### Pattern 3: Bounded Screen Count With Clear Branching

**When to use:** A process needs several decisions but should still feel guided.

**Structure:** Every Decision element leads to at most 2 "branch endings" (screens specific to that path). Avoid branches that loop back to common screens — causes confusing Back behavior. Use `Is First Screen` / `Is Last Screen` pattern via dynamic component visibility to signal progress.

### Pattern 4: Modal Flow (Quick Action) vs Full-Page Flow

Screen flows behave differently by surface:

| Surface | Behavior | Use for |
|---|---|---|
| Quick Action modal | UNVERIFIED (2026-10-20: surface behaviours in this table are Help-level, not in the corpus). Dialog; Cancel closes without committing; tight screen-count budget (3–4 max); limited width | Focused tasks |
| Lightning Record Page component | Embedded in the record view; persistent while user navigates; stateful across record refreshes | Ongoing data entry |
| Standalone URL | Full-page flow; Cancel navigates away; widest width | Wizards and one-off journeys |
| Utility bar flow | Persistent access; shared state across records | Tools |

The commit-timing rules change per surface: modal Cancel is a strong "undo" signal; full-page Cancel is a "leave the page" signal. Align UX to surface.

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Guided user input with standard fields | Standard Flow screen components | Fastest path to clear, supported UX |
| One input needs specialized rendering or validation | Custom LWC screen component (Pattern 2) | Contains custom complexity to one boundary |
| Data changes are significant or hard to undo | Commit near the end after review (Pattern 1) | Makes user intent and rollback expectations clearer |
| Many screens needed for one task | Reassess info architecture OR split into multiple flows | Flow is too fragmented or task is too broad |
| Public or external-site embedding | Use `flow/flow-for-experience-cloud` | Guest-user semantics add security concerns |
| Flow must share state across multiple record views | LWC-backed state persistence or full-page flow | Quick Action modal loses state on close |

## Review Checklist

- [ ] Each screen has one clear purpose and does not overload the user.
- [ ] Validation timing is predictable for both standard and custom components.
- [ ] Data commit points are intentional and not placed too early.
- [ ] Back, Next, Cancel, and Finish behavior all make sense to a real user.
- [ ] Custom screen components implement the `@api validate()` contract.
- [ ] Mobile or smaller-screen behavior was considered when layout matters.
- [ ] Screen count is within the "form / wizard / maze" heuristic range.
- [ ] Fault handling exists on the commit step (Pattern A from `flow/fault-handling`).

## Recommended Workflow

1. Choose the surface (Quick Action, record page, standalone URL, utility bar) and the user, then fix the screen budget for it.
2. Sketch the screens and mark every Create/Update/Delete element; move each one after the review screen unless the business case in the commit-timing table justifies it (Pattern 1).
3. For each input pick a standard component first; justify any custom LWC against the Pattern 2 gap list and hand its build to `flow/flow-screen-lwc-components`.
4. For every multi-select output, convert the semicolon-delimited string to a collection before a Loop or Get Records.
5. Set Back, Cancel and Finish deliberately (`allowBack`, `allowFinish`, `showFooter`) and add a fault path on the commit step.
6. Run `python3 scripts/check_screen_flows.py --manifest-dir <flows and lwc dir>`, walk the Review Checklist, and record decisions in `templates/screen-flows-template.md`.

---

## Salesforce-Specific Gotchas

1. **A screen flow is not automatically reversible** — once DML has happened, Back and Cancel cannot behave like true undo.
2. **Custom screen components need to cooperate with Flow validation** — they do not get correct validation behavior for free; missing `@api validate()` lets users click Next past errors.
3. **Too many screens feel like poor information architecture, not better guidance** — sequence alone does not improve UX.
4. **Standard components are easier to support than fully custom screen UIs** — custom screens should be the exception.
5. **Finish button does NOT always go where admin expects (UNVERIFIED 2026-10-20: the redirect behaviour and `{!$Flow.CurrentRecord}` are not in the corpus)** — use an explicit redirect to control it. `allowFinish` and `allowBack` cannot both be false (api_meta 264 L74178-74179).
6. **Mobile behavior differs from desktop** — custom LWCs may render differently; some standard components (Data Table edit mode) have reduced mobile support.
7. **Quick Action modal has a narrower width than standalone** — layouts that work in full-page break in the modal.
8. **Back-button visibility is a screen property** — `allowBack` defaults to true and the Previous button shows only if the user visited a previous screen and `showFooter` is true (api_meta 264 L74170-74177); set it false after an action you do not want repeated, such as a payment. UNVERIFIED (2026-10-20): the earlier claim that Back is disabled by default on some screen types is not in the corpus. Don't rely on browser back.
9. **Screen flows in Experience Cloud run under the site user's access (UNVERIFIED 2026-10-20: not in the corpus)** — sharing implications differ (see `flow/flow-for-experience-cloud`).
10. **Lookup component defaults to the first match on typeahead (UNVERIFIED 2026-10-20)** — users sometimes pick the wrong record; include a disambiguator (e.g. show Account Name next to Contact Name).
11. **Checkbox Group / Multi-Select Picklist output is a semicolon-delimited string, not a collection** (api_meta 264 L74442-74447) — wiring it straight into a Loop or Get Records filter breaks ("silently": UNVERIFIED 2026-10-20); convert to a collection first. Transform-element incompatibility: UNVERIFIED (2026-10-20).
12. **Value retention follows `inputsOnNextNavToAssocScrn`** — default `UseStoredValues` for screen components in API 51.0+ (api_meta 264 L74469-74480); set `ResetValues` when inputs must refresh. UNVERIFIED (2026-10-20): the Lightning-runtime requirement, "no memory on runtime v58 and earlier" and the Winter '24 reactive-source statement are Help-only.

## Proactive Triggers

Surface these WITHOUT being asked:

- **DML on screen 2 of 6 without a staging-model justification** → Flag as High. Almost always wrong; move commit to post-review.
- **Custom LWC screen component with no `@api validate()` method** → Flag as Critical. Users can Next past invalid data.
- **Screen flow with > 7 screens** → Flag as Medium. Reassess info architecture.
- **Quick Action modal flow with > 4 screens** → Flag as High. Modal is the wrong surface for that many screens.
- **Full-page flow with Cancel behavior not explicitly specified** → Flag as Medium. Users guess — ambiguity invites support tickets.
- **Custom LWC used where standard components would suffice** → Flag as Low. Maintenance-cost observation, not a bug.
- **Back button disabled on a wizard-style flow** → Flag as Medium. Users want to go back; disabling surprises them.
- **Screen flow embedded in Experience Cloud without guest-access review** → Flag as Critical. Route to `flow/flow-for-experience-cloud`.
- **Checkbox Group / Multi-Select Picklist output wired directly into a Loop, Get Records filter, or Transform element** → Flag as High. The output is a semicolon-delimited string, not a collection (api_meta 264 L74442-74447); convert it first.

## Output Artifacts

| Artifact | Description |
|---|---|
| Screen-flow UX design | Recommendation for screens, navigation, and commit timing |
| Validation contract | Guidance for standard vs custom component validation behavior |
| Review findings | Risks in screen count, save placement, navigation flow |
| Surface recommendation | Quick Action / LRP embed / full-page / utility bar choice with rationale |

## Related Skills

- **flow/flow-for-experience-cloud** — use when the screen flow is being embedded for external users or guest audiences.
- **flow/fault-handling** — use when the harder problem is failure behavior after the user submits.
- **flow/record-triggered-flow-patterns** — when the screen flow's commit triggers a record-triggered flow downstream.
- **lwc/custom-property-editor-for-flow** — when the question is about Flow Builder design-time configuration rather than runtime screen UX.
- **lwc/lwc-in-flow-screens** — companion LWC-side skill for building the custom components.
