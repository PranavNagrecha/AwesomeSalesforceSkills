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

| Feature | Enable? | Justification |
|---------|---------|--------------|
| Allow Reports | ☐ Yes  ☐ No | |
| Allow Activities (Tasks & Events) | ☐ Yes  ☐ No | |
| Track Field History | ☐ Yes  ☐ No | |
| Allow Notes | ☐ Yes  ☐ No | |
| Allow Bulk API Access | ☐ Yes  ☐ No | |
| Allow Streaming API Access | ☐ Yes  ☐ No | |
| Enable Chatter Feed Tracking | ☐ Yes  ☐ No | |
| Search (global search indexing) | ☐ Yes  ☐ No | |

> **Reminder:** Activities and Track Field History **cannot be disabled** after enabling.

---

## Sharing Model (Org-Wide Default)

**Selected OWD:** ☐ Private  ☐ Public Read Only  ☐ Public Read/Write  ☐ Controlled by Parent

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

---

## Notes

> Record any decisions, deviations from standard patterns, or open questions here.
