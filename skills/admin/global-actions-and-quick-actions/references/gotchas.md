# Gotchas — Global Actions and Quick Actions

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## Gotcha 1: Action Layout Is Separate from Page Layout

**What happens:** An admin adds a field to an object's page layout, expecting it to appear in the quick action dialog. The field does not appear. Users cannot enter the field when using the action.

**When it occurs:** Any time an admin who is unfamiliar with the two-layout model edits a page layout and assumes the change flows into the action form. Very common with onboarding admins and new quick action configuration.

**How to avoid:** Always edit the action layout directly: Setup → Object Manager → [Object] → Buttons, Links, and Actions → [Action Name] → Edit Layout. The action layout and the page layout are completely independent. A field must be added to both if you want it visible on the record page AND in the quick action form.

---

## Gotcha 2: LWC Global Quick Actions Only Work in Field Service Mobile

**What happens:** A developer creates a Lightning Web Component, exposes it with `lightning__GlobalAction` as the target in the component metadata, adds it to the Global Publisher Layout, and expects it to appear in Lightning Experience. It does not appear for standard Lightning users.

**When it occurs:** When teams build custom global quick actions using LWC and test in a developer org or sandbox that happens to have FSL installed, the action appears — giving a false positive. Production users without Field Service see nothing.

**How to avoid:** Per the Salesforce LWC Developer Guide, LWC components with `lightning__GlobalAction` target are supported only in the Field Service mobile app. For standard Lightning Experience global actions using custom UI, use a Visualforce page with `<apex:page docType="html-5.0" applyBodyTag="false">` or an Aura component with the `force:lightningQuickAction` interface. For object-specific custom quick actions, LWC works as expected.

---

## Gotcha 3: Action Must Be Added to a Page Layout to Be Visible

**What happens:** An admin creates a quick action, edits the action layout, sets predefined values — but the action never appears on any record page.

**When it occurs:** The admin skips the final step of adding the action to the page layout. The action exists in Setup but is not surfaced to any user because it has not been placed in the "Salesforce Mobile and Lightning Experience Actions" section of any page layout. Common with less experienced admins and with automated scripting that creates actions via Metadata API without updating page layouts.

**How to avoid:** After creating and configuring an action, always open the relevant page layout (or Global Publisher Layout for global actions) and drag the action into the actions section. Then confirm the page layout is assigned to the correct profiles.

---

## Gotcha 4: Merge Field Predefined Values Fail on Global Actions

**What happens:** An admin tries to use `{!ObjectName.FieldName}` merge-field syntax in a predefined value on a global action. Salesforce throws a validation error and will not save the predefined value.

**When it occurs:** When an admin copies predefined value configuration from an object-specific action to a global action without adjusting for the lack of source-record context.

**How to avoid:** Global actions do not have a source record, so merge field formulas that reference record fields are not valid. Predefined values on global actions must be static literal values or formulas that do not reference `{!ObjectName.Field}` syntax. If you need to pre-fill from a record, use an object-specific action instead.

---

## Gotcha 5: Actions Beyond Position 5 Are Hidden in the "More" Menu

**What happens:** An admin adds 8 actions to the "Salesforce Mobile and Lightning Experience Actions" section of a page layout. Users report they cannot find 3 of the actions. The admin confirms the actions are in the layout.

**When it occurs:** In Lightning Experience, the highlights panel displays the first ~5 actions directly in the action bar. Actions beyond the 5th position collapse into a "More" overflow menu that many users do not discover. On mobile, the action bar also has limited visible slots.

**How to avoid:** Limit the total number of actions in the section to the 5–7 most frequently used. Audit action usage to identify low-use actions and remove or move them to a less prominent position. Place the highest-frequency actions first in the list. Consider whether all actions truly belong on the record page vs being accessible from other surfaces.

---

## Gotcha 6: `targetRecordType` Only Understands Three Account Values

**What happens:** An admin (or an agent hand-writing metadata) sets
`<targetRecordType>Escalation</targetRecordType>` on a Create action for Case,
expecting the new Case to be created as the Escalation record type. The deploy
fails, or the element is accepted and the record-type chooser still appears.

**When it occurs:** Any time the element's name is read as "the record type this
action creates" in the general sense. The Metadata API Developer Guide v67.0
constrains it: "Specifies which record type to create. Valid values are:
`Business Account`, `Person Account`, `Master`." It is the Account
business-vs-person switch and nothing else.

**How to avoid:** To pin an arbitrary record type on a Create action, add a
`fieldOverrides` entry on `RecordTypeId` instead — that is an ordinary
predefined value. Reserve `targetRecordType` for Account actions that must
bypass the Business/Person chooser. If the running user does not have the
chosen record type assigned, the action still fails at save time; record-type
assignment lives in `admin/record-types-and-page-layouts`.

---

## Gotcha 7: `literalValue` Is Picklists Only — Text Defaults Need `formula`

**What happens:** An admin writes
`<literalValue>Website enquiry</literalValue>` for a predefined value on a Text
field. The deploy fails, or the field arrives empty when the action opens.

**When it occurs:** Whenever a predefined value is written by hand or copied
from a picklist override. The `FieldOverride` field table states `literalValue`
is "Supported for picklists only. Specifies the literal value of the field
defined from values in the picklist. Corresponds to the **Specific Value** field
in the predefined value UI." `formula` carries everything else, and only gained
single-select picklist support in API version 43.0.

**How to avoid:** For a non-picklist constant, use `<formula>` with the value
quoted as a formula string literal — `<formula>"Website enquiry"</formula>`.
When both are present on the same override the guide is explicit: "A formula
value takes precedence over a literal value if both are defined", so a
half-migrated override silently ignores the `literalValue` you thought you set.

---

## Gotcha 8: A Predefined Value Beats the Field's Own Default Value

**What happens:** A field has a default value defined on the field itself (or
supplied by a record type's picklist default). A quick action creates records
that ignore it. Records created through the full New form get the default;
records created through the action do not.

**When it occurs:** Whenever the same field carries both a field-level default
and a `fieldOverrides` entry on the action. The guide states the precedence
directly: "If a field on an action has both a predefined value and a default
value set, the action uses the predefined value, not the default value."

**How to avoid:** Treat the override list as a full replacement for defaults on
the fields it names. When auditing why two creation paths diverge, diff the
action's `fieldOverrides` against the object's field defaults rather than
looking for automation. This is also why removing a field from the action layout
does not remove its predefined value — the override applies to a field the user
never sees.

---

## Gotcha 9: `uiBehavior` Required Binds Only Inside the Action Dialog

**What happens:** A field is marked `<uiBehavior>Required</uiBehavior>` on the
action layout. Users cannot save the action without it — so the team assumes
the field is now mandatory. Records loaded by Data Loader, created by Flow, or
created through the standard New button arrive with the field blank.

**When it occurs:** Any time action-layout requiredness is mistaken for
field-level requiredness. `uiBehavior` is a `QuickActionLayoutItem` property
whose valid values are `Edit`, `Required` and `Readonly` — it describes "user
input behavior for specific fields" in that one dialog.

**How to avoid:** If the field must be populated on every record regardless of
path, make it required on the field definition or enforce it with a validation
rule; mark it `Required` on the action layout as well so the user is stopped at
the dialog rather than by an error toast. Conversely, when an action fails to
save with an error about a field that is not on the layout, the field is
required *elsewhere* and needs either an override or a place on the layout.

---

## Gotcha 10: `optionsCreateFeedItem` Is Required and Silently Posts to the Feed

**What happens:** An action starts posting a feed item on every save. Chatter
followers get notified for every routine status change, or a compliance review
finds record data replicated into feed posts.

**When it occurs:** `optionsCreateFeedItem` is a **required** element on
QuickAction — a hand-written file must state it, and whichever value gets
written becomes production behaviour. The guide: "Required. Indicates whether
successful completion of the action creates a feed item (true) or not (false).
Applies only to Create Record, Update Record, and Log a Call quick action
types." Available API 36.0+.

**How to avoid:** Set it explicitly on every Create/Update/LogACall action and
review it in code review; do not copy it from a template without reading it.
For Custom, Flow, Canvas and Visualforce types it is inert, so a `true` there
is noise rather than behaviour.

---

## Gotcha 11: The Layout Action Bar Has Two Independent Lists

**What happens:** An admin edits the "Salesforce Mobile and Lightning
Experience Actions" section, deploys, and the Classic publisher still shows the
old set — or a metadata diff shows an action added in one place and not the
other.

**When it occurs:** A `Layout` carries two separate collections.
`platformActionList` is "the list of actions and their order that appear in the
Salesforce mobile app action bar for the layout" (API 34.0+, the Lightning and
mobile bar), while `quickActionList` is "the list of quick actions that display
in the full Salesforce site for the page layout" (API 28.0+, the Classic
publisher). The Setup UI presents them as two sections; a hand-edited XML file
usually gets only one.

**How to avoid:** When adding an action by metadata, decide which surfaces need
it and edit both lists deliberately. Watch the `actionListContext` on
`platformActionList` — it is required, and `Record`, `Global`, `Flexipage`,
`ListView`, `ListViewRecord`, `RelatedList` and `RelatedListRecord` are
different bars on different screens, so editing the wrong context changes a bar
nobody reported. When Dynamic Actions are enabled on the object's Lightning
record page, the `FlexiPage` action list supersedes the Layout entirely and
these edits become dead configuration — see `admin/dynamic-forms-and-actions`.

---

## Gotcha 12: A Deploy Can Ship an Action Nobody Can See, With No Warning

**What happens:** A change set or `sf project deploy` succeeds, the QuickAction
component is listed as deployed, and no user in the org can find the button.
Nothing in the deploy result flags it.

**When it occurs:** Whenever the QuickAction is deployed without the Layout (or
FlexiPage) that references it. The dependency runs one way only: a Layout naming
a missing action fails the deploy, but an action with no referencing Layout is a
perfectly valid component. Metadata-API-driven tooling and agents hit this far
more often than Setup users, because Setup nudges you toward the layout editor
and a manifest does not.

**How to avoid:** Put the QuickAction and every Layout that places it in the
same deployment, and run
`scripts/check_global_actions_and_quick_actions.py --manifest-dir <dir>`, which
reports an unplaced action as INFO by scanning `layouts/` and `flexipages/` for
a reference. Verify from the user's side afterwards with
`QuickAction.describeAvailableQuickActions('Account')` run as a test user on the
target profile — not as System Administrator, whose layout assignment is usually
different.
