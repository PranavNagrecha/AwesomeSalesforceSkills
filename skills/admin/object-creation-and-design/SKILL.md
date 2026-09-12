---
name: object-creation-and-design
description: "Use when creating a new Salesforce custom object: naming the object and setting its API name, selecting optional features (Activities, Chatter, History Tracking), choosing an org-wide default sharing model, and creating a tab. Triggers: 'create a custom object', 'new custom object setup', 'what sharing model should I choose', 'how do I create a tab for my object', 'object features like activities and history tracking'. NOT for designing the fields on the object - use admin/custom-field-creation. NOT for sharing rules or role hierarchy configuration - use admin/sharing-and-visibility. NOT for lookup-vs-master-detail and junction design - use data/data-model-design-patterns. More triggers: 'custom object records not showing in search', 'sharing model greyed out on my object', 'auto number restarted at 1 after deploy', 'cannot create a queue for my custom object', 'CustomObject deploy failed enableBulkApi', 'field history tracking shows no rows'."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Operational Excellence
triggers:
  - "create a new custom object in Salesforce"
  - "pick the org-wide default sharing model for a new custom object"
  - "custom object records do not show up in global search or SOSL"
  - "my custom object does not appear in the navigation bar"
  - "sharing model is greyed out and I cannot create a sharing rule on my object"
  - "cannot create a queue or assignment rule for a master-detail child object"
  - "auto number restarted at 1 after redeploying the object"
  - "CustomObject deploy fails with enableBulkApi or enableSharing error"
  - "field history tracking is on but the history related list is empty"
  - "records loaded through the API show a record ID instead of a name"
  - "set up a custom object tab and its profile visibility"
  - "write a deployable object-meta.xml for a new custom object"
  - "how long can a custom object or custom field description be"
tags:
  - custom-objects
  - object-design
  - sharing-model
  - org-wide-defaults
  - admin
inputs:
  - "Business purpose of the object: what data it represents and who owns/uses records"
  - "Object label (singular and plural) and preferred API name"
  - "Whether records need to support activities (tasks/events), chatter, or field history"
  - "Who should be able to see and edit records by default (determines sharing model)"
  - "Whether the object needs a tab for user navigation"
outputs:
  - "Step-by-step object creation checklist with settings rationale"
  - "Sharing model recommendation with explanation"
  - "Feature selection guidance (activities, history, chatter)"
  - "Tab creation steps"
  - "Review checklist before deploying the object to production"
dependencies: []
version: 1.2.1
author: Pranav Nagrecha
updated: 2026-09-12
---

# Object Creation and Design

Use this skill when a practitioner needs to create a new custom object in Salesforce — from naming and API name through optional feature selection, org-wide default sharing model, and tab creation. This skill produces a ready-to-deploy custom object configuration.

---

## Before Starting

Gather this context before creating the object:

| Question | What it determines |
|---|---|
| Business purpose | What real-world entity does this object represent? Is it a transaction, a relationship, a configuration record, or an event log? |
| Record ownership model | Will records be owned by individual users, or shared across a team or queue? This determines the OWD. |
| Volume expectations | How many records will exist over three to five years? High-volume objects (millions of records) need index strategy and OWD decisions made early. |
| Integration surface | Will external systems create or update records? If yes, plan an External ID field immediately after object creation. |
| Edition limits | How many custom objects already exist in the org? Approaching the edition limit blocks object creation entirely. |

The most common wrong assumption: "I can change the sharing model later." Changing OWD from Private to Public (or the reverse) after significant data exists triggers a full sharing recalculation that can take hours in large orgs and may briefly degrade performance.

---

## Questions to Ask Before Configuring

Ask these before opening Object Manager. Each one maps to a decision that is fixed at save or expensive to reverse, and to a gotcha in `references/gotchas.md`.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who owns a record, and does anything ever need to route or reassign one?" | An object on the detail side of a master-detail relationship has no Owner field, so it can never have a queue, a sharing rule, or a manual share (gotchas #5) | The relationship type and the OWD together, decided once instead of twice |
| "Does the name of a record carry business meaning, or is it just a label?" | Fixes Text vs Auto Number, which cannot be changed after save; an API insert with an unmapped Text name silently stores the record ID as the name (gotchas #9) | The `nameField` block, including `displayFormat` and `startingNumber` if Auto Number |
| "Which field changes must be auditable, and who is asking?" | `enableHistory` tracks nothing on its own, the ceiling is twenty fields per object, and there is no retention lever without Field Audit Trail (gotchas #11) | The tracked-field list, with a named audit reason per field |
| "Will users find these records by typing a name into search?" | Search is off by default on new custom objects and is switched off again after 120 unsearched days (gotchas #8) | An explicit `enableSearch` value and a search check in the post-deploy test |
| "Does an integration read or write this object, and through which API?" | `enableBulkApi`, `enableSharing` and `enableStreamingApi` deploy as a set; an External ID field is far cheaper to add now than after the first load | The API surface, the three flags set consistently, and the External ID decision |
| "How many custom objects does the org already have, including managed packages?" | Managed-package objects consume the same edition allocation, so the headroom is smaller than the object list suggests (gotchas #4) | A real number from Setup rather than a count of the objects someone remembers |
| "Is this org an Experience Cloud org?" | `externalSharingModel` is a second OWD that governs external users and is separate from `sharingModel` | A deliberate external OWD instead of whatever the org default happened to be |

What a proper configuration adds over just creating the object: the permanent choices (API name, name field type, relationship side) are made once with the routing and audit requirements already known, and the object arrives in production searchable, tracked, deployable and owned rather than needing a second pass that the platform will not allow.

---

## Core Concepts

### 1. Object Name and API Name Are Permanent

The **Object Name** (API name) is set at creation and cannot be changed after the object is saved. Salesforce appends `__c` automatically; the full API name for an object with Object Name `Project_Request` is `Project_Request__c`.

Rules for the Object Name — the Metadata API states them for the component `fullName`: it "can contain only underscores and alphanumeric characters. It must be unique, begin with a letter, not include spaces, not end with an underscore, and not contain two consecutive underscores" (api_meta.txt L47322–47332):

| Rule | Effect if broken |
|---|---|
| Alphanumeric characters and underscores only, no spaces | Deploy or save rejected |
| Must begin with a letter | Deploy or save rejected |
| Cannot end with an underscore | Deploy or save rejected |
| Cannot contain two consecutive underscores | Deploy or save rejected — `__` is reserved as the namespace and suffix separator |
| Must be unique in the org | Collides with an existing object, including managed-package objects |
| Maximum 40 characters, before `__c` | Save rejected. UNVERIFIED (2026-09-04): the 40-character figure is not stated for `CustomObject` in the Metadata API Developer Guide or the Object Reference; the guide gives it for other components' `fullName`, and help.salesforce.com cannot be fetched to confirm it for custom objects. The other five rules above are quoted from the guide. |

The object `label` and `description` do have grounded limits: labels should be "unique across all standard, custom, and external objects in the org" (api_meta.txt L42168–42171), and `description` takes "a maximum of 1000 characters" (api_meta.txt L42007).

The **Label** and **Plural Label** are user-facing and can be changed any time via Setup. Choose the Object Name carefully — every piece of code, formula, flow reference, integration mapping, and change set that references this object uses the API name. Renaming requires a find-and-replace across all org metadata.

The **Record Name** field type is also permanent after save: either **Text** (user-supplied name) or **Auto Number** (system-generated sequential ID with a configurable format, e.g. `REQ-{0000}`). Use Auto Number when records need a unique, human-readable identifier that does not depend on user input. Use Text when the name is a natural business identifier (e.g., project code, contract number).

### 2. Features Cannot Be Disabled Once Enabled

The following features can be enabled on a custom object and are documented in this skill as **not disable-able after enabling**:

| Feature | Metadata element | What it enables | Important note |
|---|---|---|---|
| Allow Activities | `enableActivities` | Tasks and Events can be logged on records | Cannot be turned off after the first activity is logged |
| Track Field History | `enableHistory` | Turns on the History framework; `trackHistory` on each field selects what is captured | Cannot be turned off |
| Allow in Chatter | `enableFeeds` | Feed posts on record pages | Cannot be turned off once Chatter posts exist on records |

UNVERIFIED (2026-09-04): the "cannot be turned off" claims in this table are not stated in the Metadata API Developer Guide or the Object Reference, where `enableActivities`, `enableHistory` and `enableFeeds` are plain booleans with no one-way constraint recorded; the supporting Salesforce Help pages listed in `references/well-architected.md` cannot be fetched to re-confirm them. Two things the guides *do* say cut against the strongest reading: field-level tracking can be switched off ("in the online application, you can specify which fields are tracked or not tracked at any time" — object_reference.txt L110675), and turning it off "stops further changes from being recorded, but the history data is not deleted" (object_reference.txt L110677). Treat these as one-way *in practice* — the data and framework associations persist even where a checkbox clears — and verify against the org before telling a customer a checkbox is permanently locked.

Retention is also narrower than "18 months" suggests: 18 months is the default and maximum of `archiveAfterMonths` on `HistoryRetentionPolicy`, a component "only available to users with the RetainFieldHistory permission" (api_meta.txt L44075–44077, L44098–44105). Without Field Audit Trail it is not a setting the org has. The twenty-field ceiling is grounded: "up to a total of twenty fields (standard or custom) can be tracked for a given object" (object_reference.txt L110674).

Features that are ordinary toggles, with the caveats that matter:

| Feature | Metadata element | Caveat |
|---|---|---|
| Allow Reports | `enableReports` | — |
| Allow Bulk API Access | `enableBulkApi` | Must be deployed together with `enableSharing` and `enableStreamingApi` (api_meta.txt L42013–42019) |
| Allow Streaming API Access | `enableStreamingApi` | Same trio |
| Allow Sharing | `enableSharing` | Same trio |
| Search | `enableSearch` | Off by default on new custom objects since API 35.0, and switched off again after 120 unsearched days (api_meta.txt L42062–42071) |
| Allow Notes | — | — |

Enable only the features that are known to be required. Adding Activities to an object that will have millions of records has storage and query-plan implications. History tracking consumes storage and counts against the History object query row limits.

### 3. Org-Wide Default (OWD) Sharing Model

The OWD for a custom object controls the **baseline access** any user has to records they do not own. All sharing expansions (sharing rules, manual sharing, role hierarchy) grant access above the OWD floor — they cannot restrict below it.

| OWD Setting | `sharingModel` value | Who can read | Who can edit |
|---|---|---|---|
| Private | `Private` | Record owner and users above in role hierarchy | Record owner and users above in role hierarchy |
| Public Read Only | `Read` | All internal users | Record owner and users above in role hierarchy |
| Public Read/Write | `ReadWrite` | All internal users | All internal users |
| Controlled by Parent | `ControlledByParent` | Inherited from master-detail parent record | Inherited from master-detail parent record |

The full `SharingModel` enum also contains `ReadWriteTransfer`, `FullAccess`, `ControlledByCampaign` and `ControlledByLeadOrContact`, but the guide scopes them: "accounts, opportunities, and custom objects support `Private`, `Read` and `ReadWrite` values" (api_meta.txt L45801–45814). **Public Read/Write/Transfer**, which also lets any user change record ownership, is therefore not an option on a custom object. `ControlledByParent` is what a detail object carries and is not a free choice — it follows from the master-detail relationship.

`sharingModel` is settable through the Metadata API only from version 30.0; in version 29.0 and earlier "this field is read-only ... you must use the Salesforce user interface" (api_meta.txt L42250–42256). `externalSharingModel` is a second, separate OWD governing external users (api_meta.txt L42132–42134).

**Controlled by Parent** is only available when the object has at least one Master-Detail relationship. When this OWD is selected, users can only access child records if they can access the parent — manual sharing and sharing rules cannot be created for the child object.

Choose the most restrictive OWD that satisfies the baseline access requirement, then expand with sharing rules. Starting with a permissive OWD and trying to restrict access later is not possible — OWDs cannot restrict existing access.

### 4. Platform Limits by Edition

| Edition | Custom Objects Allowed |
|---------|----------------------|
| Contact Manager | 5 |
| Group | 50 |
| Professional | 50 |
| Enterprise | 200 |
| Performance, Unlimited | 2,000 |
| Developer | 400 |

UNVERIFIED (2026-09-04): the per-edition numbers above are carried forward from the edition-allocation pages listed in `references/well-architected.md`; they are not stated in the Metadata API Developer Guide or the Object Reference, and help.salesforce.com cannot be fetched to re-confirm them for Summer '26. Use the live count in Setup rather than this table when the answer decides whether a project can proceed.

These limits count all custom objects in the org, including those from installed managed packages. Check the current count in Setup → Company Information → Used Custom Objects before planning a data model that adds many objects. Approaching the limit blocks object creation.

---

## Common Patterns

### Pattern 1: Build From Scratch — Create a New Custom Object

**When to use**: A new business entity needs to be tracked in Salesforce and no existing object covers it.

**Steps:**

1. Setup → Object Manager → (dropdown at top right) → **Create Custom Object**.
2. Enter **Label** (singular, user-facing, e.g. "Project Request") and **Plural Label** (e.g. "Project Requests"). Salesforce auto-populates the **Object Name** — review and adjust if needed; this is the API name before `__c`.
3. Choose **Record Name** type: **Text** for user-supplied names, **Auto Number** for system-generated IDs. If Auto Number, set the Display Format (e.g. `REQ-{0000}`) and Starting Number.
4. Add a **Description** (internal, admin-facing — helps future maintainers understand the purpose).
5. Select optional features. Enable only what is known to be needed (Activities, Track Field History, Allow Notes, Allow Reports, Chatter). Remember: Track Field History and Activities cannot be turned off later.
6. Set the **Deployment Status**: choose **Deployed** for a live object or **In Development** to keep it hidden from non-admins during build/test. An object left in "In Development" is invisible to end users — flip this to Deployed before go-live.
7. Set the **OWD (Sharing Model)**. Use the decision guide above. Default is Private — change only if users genuinely need broader baseline access.
8. **Optionally** check "Launch New Custom Tab Wizard after saving" to proceed directly to tab setup. Or skip and create the tab separately.
9. Click **Save**.
10. If Track Field History was enabled, immediately go to Fields & Relationships → **Set History Tracking** and select which fields (up to 20) to track. Enabling the feature without configuring fields means nothing is tracked.
11. After saving: create the required fields (`admin/custom-field-creation`), then page layouts and record types if needed (`admin/record-types-and-page-layouts`).

### Pattern 2: Review / Audit — Validate an Existing Custom Object Configuration

**When to use**: An org assessment or design review requires validating that a custom object is correctly configured.

**Checklist for review:**

1. Setup → Object Manager → [Object] → **Details** — verify Object Name is clear and follows naming conventions. Check description is present.
2. Scroll to **Optional Features** — note which are enabled. Flag any that seem unused (e.g. Activities enabled on a config/lookup object with no logged activity).
3. Check **OWD** under Sharing Settings (Setup → Security → Sharing Settings). Verify it is the most restrictive baseline the business requires. Flag if Public Read/Write when records contain sensitive data.
4. Check field count: Setup → Object Manager → [Object] → Fields & Relationships → verify not approaching the edition field limit.
5. Check if a **Tab** exists (Setup → User Interface → Tabs → Custom Object Tabs). If the object is user-facing, it needs a tab.
6. If Track Field History is enabled, verify the tracked fields are configured: Setup → Object Manager → [Object] → Fields & Relationships → check the "Track" column.

### Pattern 3: Tab Creation for a Custom Object

**When to use**: The custom object has been created but users cannot find it in the navigation because no tab exists.

**Steps:**

1. Setup → User Interface → Tabs → **New** (under Custom Object Tabs section).
2. Select the **Object** from the dropdown.
3. Choose a **Tab Style** (icon and color scheme). Click Next.
4. Set default visibility per profile: choose **Default On**, **Default Off**, or **Hidden** for each profile. "Default On" places the tab in the navigation by default; "Default Off" means users can add it manually; "Hidden" prevents users with that profile from seeing the tab.
5. Select which **Custom Apps** should include this tab. Add it to the relevant app(s).
6. Click **Save**.

Note: A tab is required for end users to see the object in the navigation and in the App Launcher, but it is NOT required for the object to be accessible via reports, flows, Apex, or API.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|-----------|---------------------|--------|
| Records are sensitive and belong to individual owners | Private OWD | Forces explicit sharing grants; prevents accidental data exposure |
| All users need to see records but only owners can edit | Public Read Only OWD | Removes need for org-wide sharing rules; simpler to manage |
| Object is a configuration lookup (e.g. product catalog items) | Public Read Only or Public Read/Write OWD | No sensitive data; broad read access simplifies flows and reports |
| Object always has a master record (e.g. order line item) | Consider Master-Detail + Controlled by Parent | Ties access to parent; cascade delete keeps data consistent |
| Records need a stable unique ID not dependent on user input | Auto Number Record Name | Prevents duplicate or blank names; sequential IDs aid support |
| Object is accessed by integrations heavily | Enable Bulk API Access at creation | Allows Bulk API 2.0 for high-volume data loads |
| Object will have millions of records | Private OWD to minimize sharing rows | Large public OWDs generate more sharing rows and slow recalculations |

---


## Recommended Workflow

1. Answer the questions above and fill `templates/object-creation-and-design-template.md` — the permanent choices (API name, `nameField` type, master-detail vs lookup, OWD) are settled here, not in Setup
2. Check headroom — Setup → Company Information → Used Custom Objects for the live count including managed-package objects, and confirm the target object does not already exist under a different label
3. Write the metadata — copy the object, field, master-detail and tab shapes from `references/metadata-examples.md`, keeping `enableSearch`, the `enableBulkApi`/`enableSharing`/`enableStreamingApi` trio and `externalSharingModel` explicit rather than defaulted
4. Run the checker — `python3 scripts/check_object_creation_and_design.py --manifest-dir force-app/main/default` and clear every ISSUE and WARN before deploying
5. Deploy to a sandbox with `sf project deploy start --manifest manifest/package.xml --dry-run` first, then for real; keep `Profile` and `PermissionSet` out of the same manifest unless the access change is intentional (`references/gotchas.md` #10)
6. Verify in the org — the four Setup checks and the two SOQL queries at the end of `references/metadata-examples.md`, including a record edit that must produce a `__History` row
7. Hand off — record the tracked-field audit reasons and the `startingNumber` value in the object description, then continue with `admin/custom-field-creation` and `admin/permission-set-architecture`

---

## Review Checklist

Before deploying the object to production:

- [ ] Object Name (API name) is clear, follows naming conventions, and has been reviewed — it cannot be changed after save.
- [ ] Record Name type (Text vs Auto Number) chosen intentionally — cannot be changed after save.
- [ ] Description added to the object — helps future admins and developers.
- [ ] Only required features enabled (Activities, History Tracking, Chatter) — disabled features add storage overhead and cannot be turned off.
- [ ] If Track Field History is enabled, fields to track are configured in Fields & Relationships → Set History Tracking (enabling the feature alone tracks nothing).
- [ ] Deployment Status set to **Deployed** before go-live — objects in "In Development" are invisible to non-admins.
- [ ] OWD set to the most restrictive level appropriate for the business requirement.
- [ ] External ID field planned if external systems will reference records by a non-Salesforce ID.
- [ ] Tab created if the object is user-facing; tab visibility set per profile.
- [ ] Object is included in the deployment artifact (change set or SFDX manifest) along with any page layouts and profiles.
- [ ] Custom object count verified against edition limit before creating additional objects.
- [ ] `enableSearch` set explicitly if users must find records by name; search is off by default on new custom objects.
- [ ] `enableBulkApi`, `enableSharing` and `enableStreamingApi` set as a set, or all left alone.
- [ ] `externalSharingModel` set deliberately if the org has Experience Cloud enabled.
- [ ] Object `description` is under 1000 characters (`OCD-DESC-01` ISSUE) and field `description`s are kept terse (`OCD-DESC-02` INFO past 200, headroom only) — the two fields do not share one length limit; see `references/metadata-examples.md`.
- [ ] `scripts/check_object_creation_and_design.py --manifest-dir <source>` run clean against the metadata being deployed.

---

## Salesforce-Specific Gotchas

1. **Changing the OWD later triggers a full sharing recalculation** — Moving an object's OWD from Private to Public Read Only (or any change) forces Salesforce to recompute the entire sharing table for that object. In orgs with millions of records, this job can run for hours and may time out. It also temporarily holds locks. Plan the OWD correctly at object creation; treat a post-go-live OWD change as a major org event that requires scheduling and stakeholder communication.

2. **Activities and Track Field History cannot be disabled after enabling** — If you enable Activities on a config/lookup object (e.g. a Status master table), that object is now permanently associated with the Activity framework. The feature checkbox becomes read-only after the first Activity record is linked or after the first field history entry is created. Enable these only when there is a real user need.

3. **Custom objects count includes managed package objects** — The per-edition limit on custom objects counts all objects in the org, including those installed via managed packages (e.g. Salesforce CPQ, Health Cloud, NPSP). An Enterprise org licensed for 200 custom objects may already have 80+ consumed by managed packages. Always check Setup → Company Information → Used Custom Objects before beginning a large data model design.

4. **A detail object has no Owner, so nothing can route to it** — put a custom object on the detail side of a master-detail relationship and it can never have a queue, a sharing rule, or a manual share. This is the single most expensive object-design mistake to reverse.

5. **Two defaults bite silently** — new custom objects are not searchable, and an Auto Number `startingNumber` cannot be retrieved, so a routine retrieve-edit-redeploy drops it.

6. **`CustomObject` and `CustomField` descriptions do not share one length limit** — an object's `description` is documented up to 1000 characters (api_meta.txt L42007), not 255; a field's `description` states no limit at all in the guide. Do not import the 255-character figure from the permission-set/profile skills into object or field design.

Deeper treatment, with the guide lines each behaviour rests on, in `references/gotchas.md`.

---

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Object creation checklist | Step-by-step with settings rationale, ready for sandbox execution |
| OWD recommendation | Chosen sharing model with justification based on data sensitivity and access patterns |
| Feature selection notes | Which features to enable and why, flagging irreversible ones |
| Tab configuration record | Profile visibility settings and app assignments |

---

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing deployable `CustomObject`, `CustomField` and `CustomTab` XML, the package.xml, and the post-deploy verification |
| `references/gotchas.md` | Eleven platform behaviours that break object designs — Owner-less detail objects, lost auto-number counters, search defaults, whole-file replacement |
| `references/examples.md` | Two worked object builds plus the "enable everything just in case" anti-pattern |
| `references/well-architected.md` | Justifying the OWD and name-field trade-offs, and the source list behind the claims in this skill |
| `references/llm-anti-patterns.md` | Self-checking generated object configuration before handing it over |

---

## Related Skills

- admin/custom-field-creation — the fields on the object, immediately after it exists
- admin/lookup-and-relationship-design — choosing lookup vs master-detail, which decides whether the object can have an Owner at all
- admin/sharing-and-visibility — sharing rules, role hierarchy and everything that opens access above the OWD floor
- admin/record-types-and-page-layouts — record types and per-profile layouts once the object is saved
- admin/list-views-and-compact-layouts — the list views and the compact layout named by `compactLayoutAssignment`
- admin/permission-set-architecture — object and tab access, which the object file itself does not grant
- data/data-model-design-patterns — whether a new object is the right answer at all, and junction-object design
