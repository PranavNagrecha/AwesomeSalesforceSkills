---
name: object-creation-and-design
description: "Use when creating a new Salesforce custom object: naming the object and setting its API name, selecting optional features (Activities, Chatter, History Tracking), choosing an org-wide default sharing model, and creating a tab. Triggers: 'create a custom object', 'new custom object setup', 'what sharing model should I choose', 'how do I create a tab for my object', 'object features like activities and history tracking'. NOT for custom field design on the object (use custom-field-creation), sharing rule or role hierarchy configuration (use sharing-and-visibility), or object relationship design decisions (use data-model-design-patterns)."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Scalability
  - Operational Excellence
triggers:
  - "how do I create a new custom object in Salesforce"
  - "what sharing model should I pick when creating a custom object"
  - "I need to set up a new object with activities and history tracking"
  - "how do I create a tab for a custom object so users can see it"
  - "what features can I enable when creating a custom object"
  - "what are the limits on custom objects per Salesforce edition"
  - "my custom object does not appear in the navigation bar"
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
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-03
---

# Object Creation and Design

Use this skill when a practitioner needs to create a new custom object in Salesforce — from naming and API name through optional feature selection, org-wide default sharing model, and tab creation. This skill produces a ready-to-deploy custom object configuration.

---

## Before Starting

Gather this context before creating the object:

- **Business purpose**: What real-world entity does this object represent? Is it a transaction, a relationship, a configuration record, or an event log?
- **Record ownership model**: Will records be owned by individual users, or shared across a team or queue? This determines the OWD.
- **Volume expectations**: How many records will exist over three to five years? High-volume objects (millions of records) need index strategy and OWD decisions made early.
- **Integration surface**: Will external systems create or update records? If yes, plan an External ID field immediately after object creation.
- **Edition limits**: How many custom objects already exist in the org? Approaching the edition limit blocks object creation entirely.

The most common wrong assumption: "I can change the sharing model later." Changing OWD from Private to Public (or the reverse) after significant data exists triggers a full sharing recalculation that can take hours in large orgs and may briefly degrade performance.

---

## Core Concepts

### 1. Object Name and API Name Are Permanent

The **Object Name** (API name) is set at creation and cannot be changed after the object is saved. Salesforce appends `__c` automatically; the full API name for an object with Object Name `Project_Request` is `Project_Request__c`.

Rules for the Object Name:
- Maximum 40 characters (the name itself, before `__c`)
- Alphanumeric characters and underscores only
- Must start with a letter
- Cannot end with an underscore
- Cannot contain consecutive underscores

The **Label** and **Plural Label** are user-facing and can be changed any time via Setup. Choose the Object Name carefully — every piece of code, formula, flow reference, integration mapping, and change set that references this object uses the API name. Renaming requires a find-and-replace across all org metadata.

The **Record Name** field type is also permanent after save: either **Text** (user-supplied name) or **Auto Number** (system-generated sequential ID with a configurable format, e.g. `REQ-{0000}`). Use Auto Number when records need a unique, human-readable identifier that does not depend on user input. Use Text when the name is a natural business identifier (e.g., project code, contract number).

### 2. Features Cannot Be Disabled Once Enabled

The following features can be enabled on a custom object and **cannot be disabled after enabling**:

| Feature | What it enables | Important note |
|---------|----------------|----------------|
| Allow Activities | Tasks and Events can be logged on records | Cannot be turned off after first activity is logged |
| Track Field History | Tracks changes to up to 20 fields per object | History records are retained for 18 months. Cannot be turned off. |
| Allow in Chatter | Feed posts on record pages | Cannot be turned off once Chatter posts exist on records |

Features that can safely be toggled at any time:
- Allow Reports
- Allow Bulk API Access
- Allow Streaming API Access
- Search (global search indexing)
- Allow Notes

Enable only the features that are known to be required. Adding Activities to an object that will have millions of records has storage and query-plan implications. History tracking consumes storage and counts against the History object query row limits.

### 3. Org-Wide Default (OWD) Sharing Model

The OWD for a custom object controls the **baseline access** any user has to records they do not own. All sharing expansions (sharing rules, manual sharing, role hierarchy) grant access above the OWD floor — they cannot restrict below it.

| OWD Setting | Who can read | Who can edit |
|-------------|-------------|-------------|
| Private | Record owner and users above in role hierarchy | Record owner and users above in role hierarchy |
| Public Read Only | All internal users | Record owner and users above in role hierarchy |
| Public Read/Write | All internal users | All internal users |
| Controlled by Parent | Inherited from master-detail parent record | Inherited from master-detail parent record |

> Note: **Public Read/Write/Transfer** (which also allows any user to change record ownership) is available only on the standard Case and Lead objects — it is not a valid OWD option for custom objects.

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
9. After saving: create the required fields (see `custom-field-creation` skill), set up page layouts and record types if needed.

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

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

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
- [ ] External ID field planned if external systems will reference records by a non-Salesforce ID.

---

## Salesforce-Specific Gotchas

1. **Changing the OWD later triggers a full sharing recalculation** — Moving an object's OWD from Private to Public Read Only (or any change) forces Salesforce to recompute the entire sharing table for that object. In orgs with millions of records, this job can run for hours and may time out. It also temporarily holds locks. Plan the OWD correctly at object creation; treat a post-go-live OWD change as a major org event that requires scheduling and stakeholder communication.

2. **Activities and Track Field History cannot be disabled after enabling** — If you enable Activities on a config/lookup object (e.g. a Status master table), that object is now permanently associated with the Activity framework. The feature checkbox becomes read-only after the first Activity record is linked or after the first field history entry is created. Enable these only when there is a real user need.

3. **Custom objects count includes managed package objects** — The per-edition limit on custom objects counts all objects in the org, including those installed via managed packages (e.g. Salesforce CPQ, Health Cloud, NPSP). An Enterprise org licensed for 200 custom objects may already have 80+ consumed by managed packages. Always check Setup → Company Information → Used Custom Objects before beginning a large data model design.

---

## Output Artifacts

| Artifact | Description |
|----------|-------------|
| Object creation checklist | Step-by-step with settings rationale, ready for sandbox execution |
| OWD recommendation | Chosen sharing model with justification based on data sensitivity and access patterns |
| Feature selection notes | Which features to enable and why, flagging irreversible ones |
| Tab configuration record | Profile visibility settings and app assignments |

---

## Related Skills

- `custom-field-creation` — use immediately after object creation to add fields to the new object
- `sharing-and-visibility` — use when configuring sharing rules, role hierarchy, and access above the OWD baseline
- `data-model-design-patterns` — use when deciding whether to create a new object vs. adding fields to an existing one, or selecting relationship types
- `record-types-and-page-layouts` — use when the object requires multiple record types with different page layouts per user profile
- `permission-set-architecture` — use when designing profile and permission set access to the new object's CRUD permissions
