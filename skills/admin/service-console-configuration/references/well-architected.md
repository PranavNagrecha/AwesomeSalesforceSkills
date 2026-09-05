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

- **Metadata API Developer Guide — `CustomApplication`** (api_meta.txt L39621–40737) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  Source for `navType` being "Not updateable" with values `Standard` / `Console` (L39719–39723); for
  `isServiceCloudConsole` being null on Lightning console apps (L39702–39706); for
  `isNavTabPersistenceDisabled` clearing workspace tabs per console session (L39697–39701); for
  `utilityBar` naming a shared FlexiPage (L39788–39794); and for the API 42.0 renames of
  `WorkspaceMappings` → `AppWorkspaceConfig` and `CustomApplicationComponents` → `AppComponentList`
  (L40022, L39900–39907).

- **Metadata API Developer Guide — `AppWorkspaceConfig` / `WorkspaceMapping`** (api_meta.txt L40019–40047,
  worked sample L40701–40724) — same PDF.
  Source for the whole workspace-tab-vs-subtab mechanism: `mappings` is "Required for each tab specified in
  the CustomApplication", and `fieldName` is "the name of the field that specifies the primary tab in which
  to display `tab` as a subtab. If not specified, `tab` opens as a primary tab." The sample keying
  `standard-Contact` on `AccountId` and `standard-Account` on `ParentId` is what establishes that the
  lookup lives on the child.

- **Metadata API Developer Guide — `ServiceCloudConsoleConfig`, `ListPlacement`, `TabLimitConfig`,
  `KeyboardShortcuts`** (api_meta.txt L40211–40232, L40240–40254, L40314–40395) — same PDF.
  Source for `listPlacement.location` being `full` / `top` / `left` with conditional `width` / `height`;
  for the closed `tabLimitConfig` value sets (5/10/20/30 and 5/10/15); for the 18-value `DefaultShortcut`
  action enum; and for custom shortcuts requiring an `addEventListener()` handler in the Console
  Integration Toolkit before they can exist.

- **Metadata API Developer Guide — `FlexiPage`, `FlexiPageRegionType`, `ComponentInstanceProperty`**
  (api_meta.txt L66865–68023, specifically L67084–67086, L67286–67290, L67352–67363) — same PDF.
  Source for the utility bar being a FlexiPage of `type` `UtilityBar` (API 38.0+); for the `Background`
  region type existing solely for invisible utility items; and for `UtilityBar` being the only page type
  that supports component decorators — which is where panel width, height, and label actually live, and
  therefore why the "utility bar auto-load" tradeoff below is a FlexiPage decision, not an app decision.

- **Object Reference — `Macro`, `MacroInstruction`, `MacroUsage`** (object_reference.txt L177852–178396) —
  https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
  Source for a macro being a `Macro` plus ordered `MacroInstruction` records with 0-based `SortOrder`
  ("If there's an incorrect sequence of macro instructions, the macro doesn't execute"); for the five-value
  `Operation` picklist plus the API 46.0 conditional operations; for the `Target` grammar and hierarchy
  table; and for the `MacroUsage` telemetry (`ExecutionState`, `FailureReason`, `IsFromBulk`) that turns
  the "macros vs Flow" tradeoff below into a measurable one.

- **Object Reference — `QuickText` and `AppDefinition`** (object_reference.txt L238878–239050, L34140–34340)
  — same PDF.
  Source for `Channel` being a **multipicklist**; for `IsInsertable` defaulting to `false` on records
  created by Einstein Reply Recommendations; and for `AppDefinition.NavType` / `UtilityBar`, the two fields
  that let a review verify console configuration by SOQL rather than by clicking through Setup.

- **Salesforce Well-Architected Overview** — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
  Framing for the pillar mapping at the top of this file.

> UNVERIFIED (2026-09-05): the previous revision of this file cited five help.salesforce.com and Trailhead
> pages (`console2_features_available`, `console2_keyboard_shortcuts`, `macros_def`,
> `quick_text_overview`). help.salesforce.com cannot be fetched from this environment, so those URLs can be
> neither confirmed nor corrected. They have been replaced above by the API guides, which ground the same
> claims at field-table level. Two claims that only Help documents — the History utility being console-only,
> and the "Macros" / "Manage Macros" user-permission names — are marked UNVERIFIED beside the claims
> themselves in `SKILL.md` and `references/gotchas.md`.
