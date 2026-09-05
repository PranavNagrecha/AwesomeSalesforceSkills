# Metadata Examples — Global Actions and Quick Actions

Deployable `QuickAction` metadata, plus the `Layout` entries that make an action
visible. Element names, enumerations and the sample shape come from the
**Metadata API Developer Guide v67.0 (Summer '26)**, `QuickAction` type
([PDF](https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf)).

Object-specific *Layout* structure (sections, columns, items, record-type
assignment) belongs to `admin/record-types-and-page-layouts` — this file only
carries the two action-list elements of a Layout. Dynamic Actions on a
`FlexiPage` and their visibility rules belong to `admin/dynamic-forms-and-actions`.

---

## Where the files live

| What | Path in an SFDX source tree | Guide statement |
|---|---|---|
| Object-specific action | `force-app/main/default/quickActions/<Object>.<Name>.quickAction-meta.xml` | "QuickAction components have the suffix `quickAction` and are stored in the `quickActions` folder" |
| Global action | `force-app/main/default/quickActions/<Name>.quickAction-meta.xml` | same |
| Page layout that surfaces it | `force-app/main/default/layouts/<Object>-<Layout Name>.layout-meta.xml` | `Layout` type |

The `<Object>.` prefix on the file name is the same dot notation the platform
uses everywhere else for actions: the Layout sample in the guide references
`FeedItem.TextPost`, `WaveXmd.defaultAction` accepts "a valid API name with dot
notation like `Global.LogACall` or `FeedItem.Post`", the Macro target grammar in
the Object Reference is `QuickAction.<EntityApiName>.<QuickActionName>`, and
Apex `describeQuickActions` takes `'Account.QuickCreateContact'` or
`'Global.CreateNewContact'`.

**Element order:** the guide's sample lists QuickAction child elements
alphabetically (`description`, `label`, `optionsCreateFeedItem`,
`quickActionLayout`, `successMessage`, `targetObject`, `targetParentField`,
`type`). Keep that order — retrieves come back alphabetised and a different
order produces noisy diffs.

---

## 1. Object-specific Create action — new Case from an Account

`quickActions/Account.New_Escalation_Case.quickAction-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Opens a Case pre-linked to the Account, pre-subjected and pre-sourced.</description>
    <fieldOverrides>
        <field>Subject</field>
        <formula>"Escalation - " &amp; Account.Name</formula>
    </fieldOverrides>
    <fieldOverrides>
        <field>Origin</field>
        <literalValue>Phone</literalValue>
    </fieldOverrides>
    <label>New Escalation Case</label>
    <optionsCreateFeedItem>false</optionsCreateFeedItem>
    <quickActionLayout>
        <layoutSectionStyle>TwoColumnsLeftToRight</layoutSectionStyle>
        <quickActionLayoutColumns>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>Subject</field>
                <uiBehavior>Required</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>Priority</field>
                <uiBehavior>Required</uiBehavior>
            </quickActionLayoutItems>
        </quickActionLayoutColumns>
        <quickActionLayoutColumns>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>ContactId</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>Description</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
        </quickActionLayoutColumns>
    </quickActionLayout>
    <successMessage>Escalation case created and linked to this account.</successMessage>
    <targetObject>Case</targetObject>
    <targetParentField>AccountId</targetParentField>
    <type>Create</type>
</QuickAction>
```

**How to read it**

- `type` is `Create` and `targetObject` is `Case`: the action creates a *Case*,
  and it lives on *Account* only because the file is named `Account.…`. The
  guide describes exactly this shape — "on the detail page of an account,
  allows a user to create a contact related to that account … In this case,
  Contact is the `targetObject`."
- `targetParentField` "links the target object to the parent object". Here it
  names the Case lookup that points back at the Account, so the new Case is
  associated without a `fieldOverrides` entry and without the user typing
  anything. UNVERIFIED (2026-09-04): the guide's prose for `targetParentField`
  says "use Account if the target object is Contact and the parent object is
  Account" (an object name) while its own sample writes
  `<targetParentField>What</targetParentField>` for a Task (a relationship
  name). Retrieve one working action from the org and copy the form it uses
  before hand-writing this element.
- `fieldOverrides` **is** predefined field values. Per the guide: "If a field
  on an action has both a predefined value and a default value set, the action
  uses the predefined value, not the default value. A formula value takes
  precedence over a literal value if both are defined."
- `literalValue` is "Supported for picklists only" — that is why `Origin`
  (a picklist) can use it and `Subject` (text) must use `<formula>` with a
  quoted string. `formula` gained single-select picklist support in API 43.0.
- `quickActionLayout` is the action's own layout, entirely separate from the
  page layout. `layoutSectionStyle` is required; valid values are
  `TwoColumnsTopToBottom`, `TwoColumnsLeftToRight`, `OneColumn`, `CustomLinks`.
  Two `quickActionLayoutColumns` elements = two columns; with
  `TwoColumnsLeftToRight` the fields fill across the row before dropping down.
- `uiBehavior` per item is `Edit`, `Required` or `Readonly`. `Required` here is
  an *action-layout* setting — it does not create a field-level or validation
  requirement anywhere else.
- `optionsCreateFeedItem` is **Required** in the schema and "Applies only to
  Create Record, Update Record, and Log a Call quick action types."
- `successMessage` is the toast shown after a successful save (API 36.0+).
- Field count: the guide notes "There's no hard limit to the number of fields
  you can add to an action layout. However, for optimum usability, we recommend
  a maximum of eight fields. Adding more than 20 fields can severely affect
  user efficiency."

---

## 2. Global Log a Call action

`quickActions/Log_Call_Anywhere.quickAction-meta.xml` — no `<Object>.` prefix,
so it is global.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Log a call from any page; rep relates it afterwards.</description>
    <label>Log Call</label>
    <optionsCreateFeedItem>false</optionsCreateFeedItem>
    <quickActionLayout>
        <layoutSectionStyle>OneColumn</layoutSectionStyle>
        <quickActionLayoutColumns>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>Subject</field>
                <uiBehavior>Required</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>WhoId</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>WhatId</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>ActivityDate</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>Description</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
        </quickActionLayoutColumns>
    </quickActionLayout>
    <standardLabel>LogACall</standardLabel>
    <successMessage>Call logged.</successMessage>
    <targetObject>Task</targetObject>
    <type>LogACall</type>
</QuickAction>
```

**How to read it**

- No `targetParentField`: there is no parent record in a global context, so
  `WhoId` / `WhatId` are on the layout for the rep to fill in manually.
- `standardLabel` (`QuickActionLabel` enum) makes the platform render its own
  translated label rather than a hard-coded string. `LogACall` is a valid value;
  the enum also carries `New`, `NewChild`, `Update`, `SendEmail`, `Escalate`,
  `ChangeStatus`, `ChangeDueDate`, `ChangePriority`, `CreateNew`, `Forward`,
  `Reply`, `LogANote` and others — read the guide's list before guessing one,
  because an unlisted value is rejected at deploy.
- A global action still has a `targetObject` (`Task` for Log a Call). "Global"
  means *no parent*, not *no target*.

---

## 3. Update action on the current record

`quickActions/Case.Close_Case.quickAction-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Close this case with a mandatory resolution note.</description>
    <fieldOverrides>
        <field>Status</field>
        <literalValue>Closed</literalValue>
    </fieldOverrides>
    <label>Close Case</label>
    <optionsCreateFeedItem>true</optionsCreateFeedItem>
    <quickActionLayout>
        <layoutSectionStyle>OneColumn</layoutSectionStyle>
        <quickActionLayoutColumns>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>Status</field>
                <uiBehavior>Readonly</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>Description</field>
                <uiBehavior>Required</uiBehavior>
            </quickActionLayoutItems>
        </quickActionLayoutColumns>
    </quickActionLayout>
    <successMessage>Case closed.</successMessage>
    <targetObject>Case</targetObject>
    <type>Update</type>
</QuickAction>
```

**How to read it**

- An `Update` action has no `targetParentField`: it edits the record it was
  launched from. `targetObject` equals the host object.
- `Status` is pinned with `literalValue` **and** shown `Readonly` — the agent
  sees what will happen but cannot change it. Drop the `quickActionLayoutItems`
  entry entirely and the override still applies silently.
- `optionsCreateFeedItem` is `true` here, so the save posts a feed item on the
  Case. That is a per-action choice, not an org setting.

---

## 4. Flow action

`quickActions/Case.Run_Refund_Wizard.quickAction-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Launches the multi-step refund screen flow in a modal.</description>
    <flowDefinition>Case_Refund_Wizard</flowDefinition>
    <height>600</height>
    <label>Refund Wizard</label>
    <optionsCreateFeedItem>false</optionsCreateFeedItem>
    <type>Flow</type>
</QuickAction>
```

**How to read it**

- `flowDefinition` is "the API name of the flow" — the `Flow` metadata
  developer name, not its label, and not a version-suffixed name.
- No `quickActionLayout`: the flow's own screens are the UI.
- `type` `Flow` is annotated in the guide as "available as a **Beta** in API
  version 41.0 and later". The annotation has never been removed from the
  `QuickActionType` list; the feature is in broad production use.
- `height` is documented as "the height in pixels of the action pane" for a
  custom action. UNVERIFIED (2026-09-04): the guide attaches `height`/`width`
  to "a custom action" generically and does not say which of `Canvas`,
  `VisualforcePage`, `LightningComponent` and `Flow` honour them. Retrieve the
  action after configuring it in Setup and keep whatever the org writes back.
- Building the flow itself is `flow/screen-flows`; the flow receives the record
  id through a variable named `recordId`.

---

## 5. Custom component action

`quickActions/Opportunity.Price_Check.quickAction-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Opens the pricing calculator against this opportunity.</description>
    <height>500</height>
    <label>Price Check</label>
    <lightningComponent>c:priceCheckAction</lightningComponent>
    <optionsCreateFeedItem>false</optionsCreateFeedItem>
    <type>LightningComponent</type>
    <width>80</width>
</QuickAction>
```

**How to read it**

- `lightningComponent` is "the fully qualified name of the component"
  (API 38.0+), namespace-prefixed: `c:` in an org without a namespace.
- UNVERIFIED (2026-09-04): the `QuickActionType` enum documented in Metadata
  API Developer Guide v67.0 lists only `Canvas`, `Create`, `Flow`,
  `LightningComponent`, `LogACall`, `Post`, `SendEmail`, `SocialPost`,
  `Update`, `VisualforcePage` — there is **no** `LightningWebComponent` value
  and **no** `lightningWebComponent` element anywhere in that guide, even
  though orgs do emit them for LWC quick actions. Retrieve an existing LWC
  quick action from the target org and copy its exact element names rather
  than hand-writing this file. The component-side contract (which `target`
  the LWC must expose, `@api recordId`, `CloseActionScreenEvent`) is
  `lwc/lwc-quick-actions`.
- `page` (Visualforce) and `canvas` (Canvas app, API 29.0+) are the sibling
  elements for the other two custom types.

---

## 6. Person Account create action — the one place `targetRecordType` applies

```xml
<?xml version="1.0" encoding="UTF-8"?>
<QuickAction xmlns="http://soap.sforce.com/2006/04/metadata">
    <description>Create a Person Account without the record-type chooser.</description>
    <label>New Person Account</label>
    <optionsCreateFeedItem>false</optionsCreateFeedItem>
    <quickActionLayout>
        <layoutSectionStyle>OneColumn</layoutSectionStyle>
        <quickActionLayoutColumns>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>LastName</field>
                <uiBehavior>Required</uiBehavior>
            </quickActionLayoutItems>
            <quickActionLayoutItems>
                <emptySpace>false</emptySpace>
                <field>PersonEmail</field>
                <uiBehavior>Edit</uiBehavior>
            </quickActionLayoutItems>
        </quickActionLayoutColumns>
    </quickActionLayout>
    <targetObject>Account</targetObject>
    <targetRecordType>Person Account</targetRecordType>
    <type>Create</type>
</QuickAction>
```

**How to read it** — `targetRecordType` "Specifies which record type to create.
Valid values are: `Business Account`, `Person Account`, `Master`." It is an
Account business-vs-person switch, **not** a way to pin an arbitrary custom
record type. To pin a custom record type on a Create action, use a
`fieldOverrides` entry on `RecordTypeId`.

---

## 7. The Layout entries that make an action visible

`layouts/Account-Account Layout.layout-meta.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- EXCERPT. Only the two action-list elements are shown. A real Layout file
     also carries layoutSections, layoutColumns, layoutItems, relatedLists and
     summaryLayout - see admin/record-types-and-page-layouts for that shape. -->
<Layout xmlns="http://soap.sforce.com/2006/04/metadata">
    <platformActionList>
        <actionListContext>Record</actionListContext>
        <platformActionListItems>
            <actionName>Account.New_Escalation_Case</actionName>
            <actionType>QuickAction</actionType>
            <sortOrder>0</sortOrder>
        </platformActionListItems>
        <platformActionListItems>
            <actionName>Edit</actionName>
            <actionType>StandardButton</actionType>
            <sortOrder>1</sortOrder>
        </platformActionListItems>
        <platformActionListItems>
            <actionName>SendEmail</actionName>
            <actionType>ProductivityAction</actionType>
            <sortOrder>2</sortOrder>
        </platformActionListItems>
    </platformActionList>
    <quickActionList>
        <quickActionListItems>
            <quickActionName>Account.New_Escalation_Case</quickActionName>
        </quickActionListItems>
        <quickActionListItems>
            <quickActionName>FeedItem.TextPost</quickActionName>
        </quickActionListItems>
    </quickActionList>
</Layout>
```

**How to read it**

- `platformActionList` is "the list of actions and their order that appear in
  the Salesforce mobile app action bar for the layout" (API 34.0+) — this is
  what Setup calls **Salesforce Mobile and Lightning Experience Actions**.
  `quickActionList` is "the list of quick actions that display in the full
  Salesforce site" (API 28.0+) — the Classic publisher list.
- `actionListContext` is **required**. Documented values include `Record`
  (a record page), `Global`, `Flexipage`, `ListView`, `ListViewRecord`,
  `RelatedList`, `RelatedListRecord`, `Chatter`, `Dockable`, `MruList`,
  `Photo`, `BannerPhoto`, `Assistant` and more. Use `Record` for the record
  highlights-panel bar. `relatedSourceEntity` is only meaningful when the
  context is `RelatedList` or `RelatedListRecord`.
- `actionType` distinguishes what is being placed: `QuickAction` ("a global or
  object-specific action"), `StandardButton`, `CustomButton`,
  `ProductivityAction`, `InvocableAction`, `ActionLink`. Only the first is a
  QuickAction metadata component; the others resolve elsewhere and a typo in
  `actionName` for them fails at deploy with a different message.
- `sortOrder` is the position. It is the *only* control over which actions land
  in front of the "More" overflow.
- A `FlexiPage` carries the same two fields (`platformActionlist` and
  `quickActionList`) — note the lowercase `l` in the FlexiPage spelling. When
  Dynamic Actions are on for the object, the FlexiPage's list wins and this
  Layout block stops driving the bar; see `admin/dynamic-forms-and-actions`.

---

## package.xml

`QuickAction` supports the `*` wildcard in the manifest (guide: "This metadata
type supports the wildcard character `*` (asterisk) in the package.xml manifest
file"). `Layout` members use the `Object-Layout Name` form.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<Package xmlns="http://soap.sforce.com/2006/04/metadata">
    <types>
        <members>Account.New_Escalation_Case</members>
        <members>Case.Close_Case</members>
        <members>Case.Run_Refund_Wizard</members>
        <members>Log_Call_Anywhere</members>
        <name>QuickAction</name>
    </types>
    <types>
        <members>Account-Account Layout</members>
        <members>Case-Case Layout</members>
        <name>Layout</name>
    </types>
    <types>
        <members>Case_Refund_Wizard</members>
        <name>Flow</name>
    </types>
    <version>67.0</version>
</Package>
```

To pull every action in the org for an audit, swap the QuickAction block for a
single `<members>*</members>`.

---

## Retrieve, check, deploy

```bash
# Pull actions plus the layouts that place them
sf project retrieve start \
  --metadata "QuickAction:Account.New_Escalation_Case" \
  --metadata "QuickAction:Log_Call_Anywhere" \
  --metadata "Layout:Account-Account Layout" \
  --target-org my-sandbox

# Or pull everything for an audit
sf project retrieve start --metadata "QuickAction" --target-org my-sandbox

# Static checks before you deploy
python3 skills/admin/global-actions-and-quick-actions/scripts/check_global_actions_and_quick_actions.py \
  --manifest-dir force-app/main/default

# Validate-only, then deploy
sf project deploy start --manifest manifest/package.xml --dry-run --target-org my-sandbox
sf project deploy start --manifest manifest/package.xml --target-org my-sandbox
```

Deploy the QuickAction and the Layout **in the same deployment**. A Layout that
names an action the org does not have yet fails; an action deployed without its
Layout entry deploys cleanly and is invisible to every user.

---

## Verify after deploy

**Apex — does the running user actually get the action?** Run in anonymous Apex
as a user on the target profile, not as System Administrator.

```apex
// Object-specific actions available on Account for the running user
for (QuickAction.DescribeAvailableQuickActionResult r
        : QuickAction.describeAvailableQuickActions('Account')) {
    System.debug(r.getName() + ' | ' + r.getLabel() + ' | ' + r.getType());
}

// Global actions: pass the literal 'Global'
for (QuickAction.DescribeAvailableQuickActionResult r
        : QuickAction.describeAvailableQuickActions('Global')) {
    System.debug(r.getName() + ' | ' + r.getLabel() + ' | ' + r.getType());
}
```

`describeAvailableQuickActions(parentType)` takes "an object type name
('Account') or 'Global' (meaning that this method is called at a global level
and not an entity level)". If the action is absent from this list for a test
user but present for you, the cause is page-layout assignment or profile
access, not the action definition.

**Setup check** — Setup → Object Manager → *Object* → Buttons, Links, and
Actions confirms the action exists; Setup → Object Manager → *Object* → Page
Layouts → *layout* → Salesforce Mobile and Lightning Experience Actions
confirms it is placed. Global actions: Setup → Global Actions, then Setup →
Global Publisher Layouts.

**Confirm a record really came from the action** — an sObject exposes
`getQuickActionName()` in a trigger, and the guide's own example distinguishes a
global action (`QuickAction.CreateContact`) from an object-specific one
(`Schema.Account.QuickAction.CreateContact`) with it, returning `null` when the
record did not originate from an action.
