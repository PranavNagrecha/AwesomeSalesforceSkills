# Metadata Examples — Service Console Configuration

Deployable shapes for the console-specific half of a Service Console: the `CustomApplication`
`navType`/`workspaceConfig`/`consoleConfig` blocks, the `UtilityBar` FlexiPage the app points at, and the
`QuickText` / `Macro` / `MacroInstruction` **records** (those three have no Metadata API type at all — see
section 6). Shapes come from the Metadata API Developer Guide (`CustomApplication` api_meta.txt
L39621–40737, `FlexiPage` L66865–68023) and the Object Reference (`Macro` object_reference.txt
L177852–178052, `MacroInstruction` L178054–178220, `QuickText` L238878–239050), extended to one worked
Tier-1 support example.

What this file deliberately does **not** own:

- **The app skeleton, its tabs, and app visibility.** `admin/app-and-tab-configuration`
  `references/metadata-examples.md` carries `brand`, `formFactors`, `setupExperience`, the `CustomTab`
  shapes, and the `PermissionSet` `applicationVisibilities` / `tabSettings` fragment. Everything below
  assumes those tabs already exist.
- **Omni-Channel itself.** `ServiceChannel`, `RoutingConfiguration`, `PresenceConfiguration`, and
  `ServicePresenceStatus` belong to `admin/omni-channel-routing-setup`. Section 5 only places the
  Omni-Channel *widget* in the utility bar.

## Where the files live

| Type | package.xml `<name>` | `<members>` | Wildcard `*` | DX source file | API |
|---|---|---|---|---|---|
| `CustomApplication` | `CustomApplication` | app name; `standard__<Name>` for a standard app (L40428–40434) | Supported (L40415) | `applications/Support_Console.app-meta.xml` | `navType` 38.0+ (L39723) |
| `FlexiPage` (utility bar) | `FlexiPage` | Lightning page name | Supported (L68020–68022) | `flexipages/Support_Console_Utilities.flexipage-meta.xml` | `UtilityBar` type 38.0+ (L67084–67086) |
| `Macro`, `MacroInstruction`, `QuickText` | **none — sObjects, not metadata** | — | — | CSV, loaded with the API/Data Loader | `Macro` 32.0+, `QuickText` 24.0+ |

`CustomApplication` files have the suffix `.app` and live in the `applications` folder (L39627–39628);
FlexiPages have the suffix `.flexipage` in `flexipages` (L66896–66897). DX adds `-meta.xml` to both.

Retrieving a `CustomApplication` "makes the component appear in any Profile and PermissionSet components
that are retrieved in the same package" (L39630–39631) — a console app retrieve quietly widens the diff.

---

## 1. The Lightning console app

`force-app/main/default/applications/Support_Console.app-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <defaultLandingTab>standard-Case</defaultLandingTab>
    <description>Tier-1 support console. Cases and Accounts open as workspace tabs; Contacts open as a subtab of the Account named by Contact.AccountId.</description>
    <formFactors>Large</formFactors>
    <isNavTabPersistenceDisabled>false</isNavTabPersistenceDisabled>
    <label>Support Console</label>
    <navType>Console</navType>
    <tabs>standard-Case</tabs>
    <tabs>standard-Account</tabs>
    <tabs>standard-Contact</tabs>
    <tabs>standard-Knowledge</tabs>
    <uiType>Lightning</uiType>
    <utilityBar>Support_Console_Utilities</utilityBar>
    <workspaceConfig>
        <mappings>
            <tab>standard-Case</tab>
        </mappings>
        <mappings>
            <tab>standard-Account</tab>
        </mappings>
        <mappings>
            <fieldName>AccountId</fieldName>
            <tab>standard-Contact</tab>
        </mappings>
        <mappings>
            <tab>standard-Knowledge</tab>
        </mappings>
    </workspaceConfig>
</CustomApplication>
```

How to read it:

- **`navType` is the whole console switch, and it is "Not updateable"** (L39719–39723). `Standard` is a
  Lightning app with standard navigation; `Console` is a Lightning app with console navigation. There is no
  other element that turns split view on.
- **`isServiceCloudConsole` is absent on purpose.** "For Lightning Experience console apps, this field is
  null and the `navType` field is set to `Console`" (L39702–39706). Anything that decides "is this a
  console app?" by reading `isServiceCloudConsole` misses every Lightning console app in the org.
- **`workspaceConfig` is what the Setup UI calls navigation rules** — `AppWorkspaceConfig`, "Represents how
  records open in a Salesforce console app" (L39796–39799), holding `mappings` (`WorkspaceMappingSingle[]`,
  L40025). There is no element named `navRules`, `consoleComponents`, or `navigationRules` anywhere in the
  Metadata API.
- **`mappings` is required per tab.** `AppWorkspaceConfig.mappings` is "Required for each tab specified in
  the CustomApplication" (L40025–40032). A console tab with no mapping is the single most common cause of
  "the record opened in the wrong place."
- **`isNavTabPersistenceDisabled`** — "Indicates whether workspace tabs are cleared for each new console
  session (true) or not (false). Applies only to Lightning apps with console navigation." API 54.0+
  (L39697–39701). Leave it `false` when agents resume yesterday's work; set it `true` for shared
  workstations where the next shift must not inherit the last agent's open tabs.
- **`defaultLandingTab`** takes the fullName of a tab (L39661–39663) — it is a separate decision from tab
  order, and on a console app it decides which workspace opens on login.

---

## 2. `workspaceConfig` decoded — the actual subtab rule

`WorkspaceMapping` has exactly two fields (L40038–40047):

| Field | Required | Guide text |
|---|---|---|
| `tab` | Yes | "Name of the tab." |
| `fieldName` | No | "The name of the field that specifies the primary tab in which to display `tab` as a subtab. **If not specified, `tab` opens as a primary tab.**" |

So the choice is not an enum. It is *the presence or absence of a lookup field name*:

| Mapping | Result for the agent |
|---|---|
| `<tab>standard-Case</tab>` | A Case opens as its own **workspace (primary) tab** |
| `<fieldName>AccountId</fieldName><tab>standard-Contact</tab>` | A Contact opens as a **subtab of the workspace showing the Account in `Contact.AccountId`** — and only if that Account workspace is open or can be opened |
| `<fieldName>ParentId</fieldName><tab>standard-Account</tab>` | A child Account opens as a subtab of its parent Account (the guide's own sample, L40712–40716) |

The guide's console sample uses exactly this pattern — `standard-Case` and `standard-Contract` with no
`fieldName`, `standard-Account` keyed on `ParentId` and `standard-Contact` keyed on `AccountId`
(L40701–40724).

Two consequences the Setup UI wording hides:

- The parent is chosen by **data**, not by "whatever tab is focused." A Contact whose `AccountId` is null
  has no parent workspace to nest under.
- `fieldName` must be a real field on **the mapped tab's own object** that points at the parent object.
  `AccountId` is a field on Contact, not on Account. Getting the direction backwards deploys cleanly and
  behaves wrong. `scripts/check_service_console_configuration.py` checks exactly this.

---

## 3. `consoleConfig` — read the version note before you copy this

`ServiceCloudConsoleConfig` (L40314–40374) is reachable from `CustomApplication.consoleConfig`
(L39658–39660, API 42.0+). Its sub-fields are gated on the **Salesforce Classic** console flag:
`detailPageRefreshMethod`, `listPlacement`, and `listRefreshMethod` are each "Required if
`isServiceCloudConsole` is true", `keyboardShortcuts` likewise (L40211–40213), and `tabLimitConfig` is
"Required if `enableTabLimits` is true" (L40377–40379) — where `enableTabLimits` lives on `AppPreferences`
and is documented as "the number of primary tabs and subtabs that can be opened in a **Salesforce Classic**
console session" (L39962–39964).

> UNVERIFIED (2026-09-05): the Metadata API guide presents this block only inside its
> "Declarative Metadata Sample Definition—Salesforce Console" sample, introduced as "a custom app where
> `isServiceCloudConsole` is true" (L40544–40546) — i.e. the Classic shape. It never states whether a
> Lightning console app (`navType` `Console`, `isServiceCloudConsole` null) accepts, ignores, or rejects a
> `consoleConfig` block. Retrieve a Lightning console app from the target org
> (`sf project retrieve start --metadata CustomApplication:<Name>`) and see what the org actually emits
> before hand-authoring one. Treat the shape below as the Classic-console reference, not as a Lightning
> console deliverable.

`force-app/main/default/applications/Support_Console_Classic.app-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<CustomApplication xmlns="http://soap.sforce.com/2006/04/metadata">
    <consoleConfig>
        <componentList>
            <alignment>left</alignment>
            <components>Case_Timeline_VF</components>
        </componentList>
        <detailPageRefreshMethod>autoRefresh</detailPageRefreshMethod>
        <footerColor>#0B5CAB</footerColor>
        <headerColor>#0B5CAB</headerColor>
        <keyboardShortcuts>
            <customShortcuts>
                <action>EscalateActiveCase</action>
                <active>true</active>
                <description>Run the Tier-2 escalation handler registered by the console toolkit</description>
                <eventName>supportConsoleEscalate</eventName>
                <keyCommand>SHIFT+CTRL+E</keyCommand>
            </customShortcuts>
            <defaultShortcuts>
                <action>FOCUS_CONSOLE</action>
                <active>true</active>
                <keyCommand>ESC</keyCommand>
            </defaultShortcuts>
            <defaultShortcuts>
                <action>CLOSE_TAB</action>
                <active>true</active>
                <keyCommand>SHIFT+C</keyCommand>
            </defaultShortcuts>
            <defaultShortcuts>
                <action>MOVE_RIGHT</action>
                <active>true</active>
                <keyCommand>SHIFT+RIGHT ARROW</keyCommand>
            </defaultShortcuts>
        </keyboardShortcuts>
        <listPlacement>
            <location>left</location>
            <units>px</units>
            <width>300</width>
        </listPlacement>
        <listRefreshMethod>refreshListRows</listRefreshMethod>
        <primaryTabColor>#0B5CAB</primaryTabColor>
        <tabLimitConfig>
            <maxNumberOfPrimaryTabs>10</maxNumberOfPrimaryTabs>
            <maxNumberOfSubTabs>15</maxNumberOfSubTabs>
        </tabLimitConfig>
    </consoleConfig>
    <isServiceCloudConsole>true</isServiceCloudConsole>
    <label>Support Console (Classic)</label>
    <preferences>
        <enableKeyboardShortcuts>true</enableKeyboardShortcuts>
        <enableMultiMonitorComponents>true</enableMultiMonitorComponents>
        <enableTabLimits>true</enableTabLimits>
        <saveUserSessions>true</saveUserSessions>
    </preferences>
    <tabs>standard-Case</tabs>
    <tabs>standard-Account</tabs>
</CustomApplication>
```

How to read it:

- **`listPlacement.location` is `full`, `top`, or `left`** (L40247–40250) — the list panel is not fixed to
  the left. `width` is "Required if location is `left`", `height` is "Required if location is `top`", and
  `units` (px or %) is required in every case (L40245–40254). A `location` of `full` with a `width` is
  contradictory, not additive.
- **`tabLimitConfig` values are a closed set of strings**: `maxNumberOfPrimaryTabs` accepts `5`, `10`, `20`,
  `30`; `maxNumberOfSubTabs` accepts `5`, `10`, `15` (L40382–40395). `15` primary tabs or `20` subtabs are
  not valid values, and it is required whenever `enableTabLimits` is true.
- **`defaultShortcuts.action` is an 18-value enum** — `FOCUS_CONSOLE`, `FOCUS_NAVIGATOR_TAB`,
  `FOCUS_DETAIL_VIEW`, `FOCUS_PRIMARY_TAB_PANEL`, `FOCUS_SUBTAB_PANEL`, `FOCUS_LIST_VIEW`,
  `FOCUS_FIRST_LIST_VIEW`, `FOCUS_SEARCH_INPUT`, `MOVE_LEFT`, `MOVE_RIGHT`, `UP_ARROW`, `DOWN_ARROW`,
  `OPEN_TAB_SCROLLER_MENU`, `OPEN_TAB`, `CLOSE_TAB`, `ENTER`, `EDIT`, `SAVE` (L40170–40195). You cannot
  invent a nineteenth; you can only disable or rebind these.
- **`customShortcuts.eventName` binds to developer code, not to a macro.** "Before you can create custom
  shortcuts, a developer must define the shortcut's action with the `addEventListener()` method in the
  Salesforce Console Integration Toolkit. You can't create keyboard shortcuts for actions performed outside
  of the console" (L40052–40054). `CustomShortcut` has five fields — `action`, `active`, `keyCommand`,
  `description`, `eventName` — and none of them references a `Macro` record.
- **`keyCommand` grammar**: "up to four modifier keys followed by one non-modifier key", joined with `+`,
  modifiers in any order but non-modifiers last; valid modifiers are `SHIFT`, `CTRL`, `ALT`, `META`
  (L40062–40074). Not case-sensitive, displayed uppercase in Setup.
- **`componentList` is Visualforce console components** — `AppComponentList`, "Represents custom console
  components (Visualforce pages) assigned to a Salesforce console app", renamed from
  `CustomApplicationComponents` in API 42.0, and its `components` field renamed from
  `customApplicationComponent` (L39900–39907). `alignment` is required.

---

## 4. The utility bar is a separate FlexiPage

`force-app/main/default/flexipages/Support_Console_Utilities.flexipage-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<FlexiPage xmlns="http://soap.sforce.com/2006/04/metadata">
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>label</name>
                    <type>decorator</type>
                    <value>History</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>width</name>
                    <type>decorator</type>
                    <value>340</value>
                </componentInstanceProperties>
                <componentName>forceSearch:historyUtilityItem</componentName>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>label</name>
                    <type>decorator</type>
                    <value>Omni-Channel</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>height</name>
                    <type>decorator</type>
                    <value>480</value>
                </componentInstanceProperties>
                <componentName>runtime_service_omnichannel:omniWidget</componentName>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>label</name>
                    <type>decorator</type>
                    <value>Macros</value>
                </componentInstanceProperties>
                <componentInstanceProperties>
                    <name>width</name>
                    <type>decorator</type>
                    <value>360</value>
                </componentInstanceProperties>
                <componentName>runtime_service_macros:macrosUtility</componentName>
            </componentInstance>
        </itemInstances>
        <itemInstances>
            <componentInstance>
                <componentInstanceProperties>
                    <name>label</name>
                    <type>decorator</type>
                    <value>Notes</value>
                </componentInstanceProperties>
                <componentName>one:notesUtility</componentName>
            </componentInstance>
        </itemInstances>
        <name>utilityItems</name>
        <type>Region</type>
    </flexiPageRegions>
    <flexiPageRegions>
        <itemInstances>
            <componentInstance>
                <componentName>c:consoleTelephonyListener</componentName>
            </componentInstance>
        </itemInstances>
        <name>backgroundUtilityItems</name>
        <type>Background</type>
    </flexiPageRegions>
    <masterLabel>Support Console Utilities</masterLabel>
    <template>
        <name>flexipage:utilityBarTemplateDesktop</name>
    </template>
    <type>UtilityBar</type>
</FlexiPage>
```

How to read it:

- **`type` is `UtilityBar`** — "A Lightning page used as the utility bar in Lightning Experience apps",
  API 38.0+ (L67084–67086). The app names it by developer name in `<utilityBar>` (L39788–39789).
- **Panel width, height, and the visible label are component *decorators*, not app settings.** A
  `componentInstanceProperties` entry with `<type>decorator</type>` "can apply more capabilities to the
  component when it renders on a specific page… for example, you can configure a component decorator around
  a component on the Lightning Experience utility bar to set the component's height or width when opened.
  **The UtilityBar is the only page type that supports component decorators**" (L67352–67363).
- **A second region of `type` `Background` holds utilities with no button.** `FlexiPageRegionType`
  `Background` "Represents a region for background utility items, which aren't visible in the UI. Supported
  for utility bars only" (L67286–67290). That is where a telephony or event listener goes — it runs for the
  whole session without occupying footer space. The other two values are `Facet` and `Region`.
- **`masterLabel` and `template` are required on every FlexiPage** (L66936–66944).
- **One utility bar, one app.** "We recommend assigning a utility bar to only one Lightning App, because
  utility bars are shared. Sharing means that if you change the utility bar in one app, it automatically
  changes in all apps associated with it" (L39788–39794).

> UNVERIFIED (2026-09-05): the template name `flexipage:utilityBarTemplateDesktop`, the region names
> `utilityItems` / `backgroundUtilityItems`, and the component names `forceSearch:historyUtilityItem`,
> `runtime_service_omnichannel:omniWidget`, `runtime_service_macros:macrosUtility`, and `one:notesUtility`
> are not published in the Metadata API Developer Guide — it documents the FlexiPage *structure* but not
> the catalogue of templates or standard utility components. Retrieve an existing utility bar
> (`sf project retrieve start --metadata FlexiPage:<Name>`) and copy the exact strings.

> UNVERIFIED (2026-09-05): "auto-open the panel when the app loads" (the Setup checkbox usually labelled
> *Start automatically*) has no counterpart in the FlexiPage field tables in `api_meta.txt`. It is
> presumably another decorator property; confirm its `name` against a retrieved utility bar rather than
> guessing.

---

## 5. Quick Text and Macros are records, not metadata

Neither `Macro`, `MacroInstruction`, nor `QuickText` appears as a Metadata API type in `api_meta.txt`. The
only console-adjacent metadata is the `QuickTextChannel` **StandardValueSet**, which backs
`QuickText.Channel` (L142921) — the channel values themselves are org-configurable through that value set,
which is why the guide never publishes a fixed five-value list.

So these travel as **data**: `Macro` supports `create(), delete(), query(), retrieve(), update(),
upsert()` (object_reference L177857–177859) and `QuickText` the same plus `undelete()` (L238886–238888).
Load them with Data Loader or the Bulk API, in this order: `QuickText` → `Macro` → `MacroInstruction`
(instructions need the parent macro's Id).

### `QuickText.csv`

```csv
Name,Message,Category,Channel,IsInsertable
Greeting - Email,"Hi {!Contact.FirstName}, thanks for contacting support. I'm looking into this now.",Greetings,Email;Chat,true
Awaiting Customer,"We're waiting on the log file you mentioned. I'll hold the case open for 5 working days.",Status Updates,Email;Portal,true
Internal - Escalation Note,"Escalated to Tier 2 under SLA clause 4.2. Do not send to customer.",Internal,Internal,true
```

- **`Channel` is a multipicklist, not a picklist** — "A multi-select picklist that can be used to specify
  where specific quick text messages are available, such as in Chat or in the Email publisher in Case Feed"
  (object_reference L238905–238913). One record can serve several channels; the CSV separator for a
  multipicklist is `;`. Splitting one snippet into three single-channel records is unnecessary duplication.
- **`IsInsertable` is the "Include in selected channels" checkbox.** "If `true`, the quick text is available
  in the channels selected in the `Channel` field." It defaults to `true` for records created from the Quick
  Text page or via the API, but **`false`** for records created by the Einstein Reply Recommendations
  publishing process (L238932–238946). Bulk-loading a set that was exported from that feature and leaving
  the column out gives agents an invisible library.
- **`Category` is a customizable picklist** used to group related snippets (L238895–238903), backed by the
  `QuickTextCategory` standard value set (L142919).

### `Macro.csv`

```csv
Name,Description,StartingContext,IsLightningSupported,IsAlohaSupported
Escalate to Tier 2,"Opens the case Email quick action, fills the SLA notification, and submits it",Case,true,false
```

- **`StartingContext` is the object the macro acts on**, and it is a restricted picklist: "In Lightning
  Experience, macros are supported on standard and custom objects that allow quick actions and have a
  customizable page layout" (L177943–177950). An object without quick actions cannot host a macro.

### `MacroInstruction.csv`

```csv
MacroId,SortOrder,Operation,Target,Value
a1B...MacroId,0,Select,Tab.Case,
a1B...MacroId,1,Select,QuickAction.Case.Email,
a1B...MacroId,2,Set,Field.EmailMessage.Subject,Your case has been escalated
a1B...MacroId,3,Set,Field.EmailMessage.ToAddress,{!Case.ContactEmail}
a1B...MacroId,4,Insert,Field.EmailMessage.HtmlBody.cursor,We have escalated your case to our senior team.
a1B...MacroId,5,Submit,QuickAction.Case.Email,
```

This is the guide's own worked example, one row per step (object_reference L178024–178029).

- **`Operation` is a five-value picklist** — `Select`, `Set`, `Insert`, `Submit`, `Close` — plus `IF`,
  `ELSEIF`, `ELSE`, `ENDIF` in API 46.0 and later for conditional macros (L178095–178126). There is no
  `Update Field`, `Send Email`, `Post to Chatter`, or `Save Record` operation: sending an email is
  `Select QuickAction.Case.Email` → `Set` the fields → `Submit`.
- **`Target` follows a documented grammar and hierarchy** (L177980–178020): `Tab.<EntityApiName>` at the
  root (supports `SELECT`, and `CLOSE` implicitly), then `QuickAction.<EntityApiName>.<QuickActionName>`
  (`SELECT`, `SUBMIT`), then `Field.<QATargetEntityApiName>.<FieldApiName>` (`SET`), with
  `Field.<…>.<MultilineTextFieldApiName>.cursor` and `Field.<…>.<SinglelineTextFieldApiName>.end` taking
  `INSERT`. "A target isn't available if its parent isn't" — which is why row 0 must select the tab.
  Knowledge sidebar targets (`SidebarCmp.Knowledge`, `SearchAction.KnowledgeArticle`,
  `Command.InsertToEmail`, `Command.AttachToEmailAsPDF`) hang off the same tree.
- **`SortOrder` is 0-based and load-bearing.** "A macro contains an ordered list of macro instructions whose
  index field, `sortOrder`, is 0-based. If there's an incorrect sequence of macro instructions, the macro
  doesn't execute" (L177958–177961).
- **`Value` and `ValueRecord` are mutually exclusive** — "An instruction can contain both a `Value` field
  and a `ValueRecord` field, but only one of these fields can have a value. The other field value must be
  null" (L178152–178163). Use `ValueRecord` for an Id (a queue, an EmailTemplate), `Value` for literal text.
- **Relative dates use a `MacroFormula:` prefix** — `MacroFormula:NOW() + 1` — and the guide warns "You
  can't edit custom relative formulas in the Macro Builder" (L178157–178163). A macro loaded this way is
  partly read-only in the point-and-click builder afterwards.

---

## 6. package.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Support_Console</members>
        <name>CustomApplication</name>
    </types>
    <types>
        <members>Support_Console_Utilities</members>
        <name>FlexiPage</name>
    </types>
    <types>
        <members>Support_Agent</members>
        <name>PermissionSet</name>
    </types>
    <version>62.0</version>
</Package>
```

`CustomApplication` supports the `*` wildcard, but it "returns only all custom applications but not standard
applications" in API 29.0 and earlier (L40415–40421). Name a standard app with the `standard__` prefix
(`standard__Chatter`, L40428–40434) and a packaged one with its namespace (`myInstalledPackageNS__PackageApp`,
L40437–40444).

`Macro`, `MacroInstruction`, and `QuickText` are **not** in this file — they have no metadata type. Nothing
in a package.xml will carry them between orgs.

---

## 7. Deploy order

| # | Step | Command | Why this order |
|---|---|---|---|
| 1 | Tabs and objects exist | see `admin/app-and-tab-configuration` | Every `<tabs>` and every `mappings.tab` value must resolve |
| 2 | Retrieve the reference utility bar | `sf project retrieve start --metadata FlexiPage:<ExistingUtilityBar>` | Harvest the real template and component names instead of typing them |
| 3 | Deploy the utility bar FlexiPage | `sf project deploy start --source-dir force-app/main/default/flexipages` | The app's `<utilityBar>` points at it by name; deploy the app first and that reference dangles |
| 4 | Deploy the console app | `sf project deploy start --source-dir force-app/main/default/applications` | Carries `navType`, `workspaceConfig`, and the utility-bar reference |
| 5 | Deploy app + tab visibility | `sf project deploy start --source-dir force-app/main/default/permissionsets` | `CustomApplication` has no visibility field of its own |
| 6 | Load QuickText | Data Loader / Bulk API insert on `QuickText` | Independent of the app |
| 7 | Load Macro, then MacroInstruction | insert `Macro`, capture Ids, insert `MacroInstruction` | `MacroInstruction.MacroId` is a lookup to the parent (L178080–178085) |
| 8 | Run the checker | `python3 scripts/check_service_console_configuration.py --manifest-dir force-app/main/default` | Catches broken `fieldName` mappings and dangling FlexiPage references before the deploy |

Retrieve the console app before editing it:

```bash
sf project retrieve start --metadata CustomApplication:Support_Console --target-org sandbox
sf project deploy start --source-dir force-app/main/default --target-org sandbox --dry-run
```

---

## 8. Verification

**Is it actually a console app, and does it point at the right utility bar?**

```sql
SELECT DeveloperName, Label, NavType, UiType, UtilityBar
FROM AppDefinition
WHERE DeveloperName = 'Support_Console'
```

`AppDefinition.NavType` is a picklist of `Standard`, `Console`, or null for a Salesforce Classic app
(object_reference L34301–34309); `UtilityBar` is "The ID of the utility bar associated with this
application" (L34331–34338). `NavType` = `Console` and a non-null `UtilityBar` is the pass condition.

**Did the utility bar leak into other apps?**

```sql
SELECT DeveloperName, UtilityBar FROM AppDefinition WHERE UtilityBar != null
```

More than one row sharing a `UtilityBar` Id means an edit to one app's footer silently changes the other's.

**Did the macro load in the right order?**

```sql
SELECT MacroId, SortOrder, Operation, Target, Value
FROM MacroInstruction
WHERE Macro.Name = 'Escalate to Tier 2'
ORDER BY SortOrder
```

Row 0 must be `Select` on a `Tab.*` target. A gap or a duplicate in `SortOrder` means the macro will not
execute (L177958–177961).

**Are the macros actually running for agents?**

```sql
SELECT MacroId, ExecutionState, FailureReason, ExecutedInstructionCount, InstructionCount, IsFromBulk
FROM MacroUsage
WHERE ExecutionState != 'SUCCESS'
ORDER BY ExecutionEndTime DESC
```

`ExecutionState` is `SUCCESS` / `FAILURE` / `CANCELED` and `FailureReason` is `ACCESS`, `GENERIC`,
`TIMEOUT`, or `UNSUPPORTED` (object_reference L178302–178322). `ACCESS` on every row is the permission
problem; `UNSUPPORTED` is usually a `Target` the object does not offer. `IsFromBulk` distinguishes a bulk
macro run, where "usage is recorded per record" (L178346–178352).

**Setup check (nothing above proves the agent experience):** log in as an agent, open a Case, click a
Contact from it, and confirm the Contact appears as a subtab under the Account workspace named by
`Contact.AccountId` — not as a new primary tab and not under the Case.
