# Custom Object Creation — Output Template

Use this template to document a custom object being designed and created.
Fill in every section before submitting for review or including in a deployment.

---

## Object Summary

| Field | Value |
|-------|-------|
| Object Label (singular) | |
| Object Label (plural) | |
| Object Name (API name, before `__c`) | |
| Full API Name | `<ObjectName>__c` |
| Record Name type | ☐ Text  ☐ Auto Number |
| If Auto Number — Display Format | (e.g. `REQ-{00000}`) |
| Description (internal) | |
| Business Purpose | |

---

## Features Enabled

| Feature | Metadata element | Enable? | Justification |
|---|---|---|---|
| Allow Reports | `enableReports` | ☐ Yes  ☐ No | |
| Allow Activities (Tasks & Events) | `enableActivities` | ☐ Yes  ☐ No | |
| Track Field History | `enableHistory` | ☐ Yes  ☐ No | |
| Allow Notes | — | ☐ Yes  ☐ No | |
| Allow Bulk API Access | `enableBulkApi` | ☐ Yes  ☐ No | |
| Allow Sharing | `enableSharing` | ☐ Yes  ☐ No | |
| Allow Streaming API Access | `enableStreamingApi` | ☐ Yes  ☐ No | |
| Enable Chatter Feed Tracking | `enableFeeds` | ☐ Yes  ☐ No | |
| Search (global search and SOSL) | `enableSearch` | ☐ Yes  ☐ No | |

> **Reminder 1:** Activities and Track Field History are treated as one-way in this skill — see the marked note in `SKILL.md` § Core Concepts 2 before promising a customer a checkbox can be cleared.
> **Reminder 2:** `enableBulkApi`, `enableSharing` and `enableStreamingApi` deploy as a set — all three or none.
> **Reminder 3:** Search is off by default on new custom objects. Leaving the row blank means "not searchable".

---

## Sharing Model (Org-Wide Default)

**Selected internal OWD (`sharingModel`):** ☐ Private  ☐ Public Read Only (`Read`)  ☐ Public Read/Write (`ReadWrite`)  ☐ Controlled by Parent (`ControlledByParent`)

**External OWD (`externalSharingModel`), if the org has Experience Cloud:** ☐ Private  ☐ `Read`  ☐ `ReadWrite`  ☐ N/A — no external users

**Does this object sit on the detail side of a master-detail relationship?** ☐ Yes  ☐ No

> If Yes: the OWD is fixed at Controlled by Parent, the object has no Owner field, and it can never have a queue, a sharing rule, or a manual share. Confirm nothing in the requirements needs to route or reassign these records.

**Justification:**

> Explain why this OWD was chosen. Reference the access requirement (who needs to see/edit records by default) and the data sensitivity level.

---

## Fields to Track (if Track Field History is enabled)

| Field API Name | Field Label | Reason for Tracking |
|----------------|-------------|---------------------|
| | | |
| | | |

> Track a maximum of 20 fields. Only include fields with a compliance or audit requirement.

---

## Tab Configuration

| Setting | Value |
|---------|-------|
| Tab needed? | ☐ Yes  ☐ No |
| Tab Style (icon) | |
| Default visibility (Admin profile) | ☐ Default On  ☐ Default Off  ☐ Hidden |
| Default visibility (other profiles) | |
| Apps to add tab to | |

---

## Review Checklist

- [ ] Object Name (API name) reviewed for clarity and permanence
- [ ] Record Name type chosen intentionally (Text vs Auto Number)
- [ ] Description added to object
- [ ] Only required features enabled; irreversible features (Activities, History) have confirmed use cases
- [ ] OWD is the most restrictive level that satisfies baseline access requirements
- [ ] If Track Field History enabled: fields to track are listed above
- [ ] Tab created and visibility configured per profile
- [ ] Deployment artifact includes object metadata, page layouts, and profile/permission set updates
- [ ] Custom object count checked against edition limit before deployment
- [ ] `enableSearch` set explicitly; `enableBulkApi` / `enableSharing` / `enableStreamingApi` set as a set or all omitted
- [ ] Auto Number `startingNumber` recorded here and in the object description — it cannot be retrieved from the org
- [ ] `scripts/check_object_creation_and_design.py --manifest-dir <source>` run clean

---

## Notes

> Record any decisions, deviations from standard patterns, or open questions here.
