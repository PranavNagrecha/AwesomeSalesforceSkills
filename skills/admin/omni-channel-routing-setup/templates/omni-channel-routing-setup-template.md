# Omni-Channel Routing Setup — Work Template

Use this template when configuring or updating Omni-Channel routing for a Salesforce org.

## Scope

**Skill:** `omni-channel-routing-setup`

**Request summary:** (fill in what the user asked for — e.g., "first-time Omni-Channel setup for case routing" or "add skills-based routing for product specialist matching")

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before proceeding.

- **Routing model decision:** queue-based / skills-based / both
- **Omni-Channel enabled in org?** yes / no / unknown — confirm at Service Setup > Omni-Channel Settings
- **Skills-Based Routing enabled?** yes / no / not applicable — confirm at same settings page
- **Service channels required:** (list: Case / Chat / Messaging / Voice / Custom Object: ___)
- **Queue list:** (list all queues that will route via Omni-Channel)
- **Agent count:** (number of agents who will receive routed work)
- **Known constraints:** (license tier, existing capacity model, any queues that must NOT migrate to Omni-Channel)
- **Failure modes to watch for:** (existing Apex trigger routing? manual queue pickup patterns that will conflict?)

---

## Routing Configuration Plan

| Queue Name | Routing Model | Priority | Capacity Units | Push Timeout |
|---|---|---|---|---|
| (queue 1) | Least Active / Most Available / Skills-Based | 1 | 5 | 30s |
| (queue 2) | | | | |
| (queue 3) | | | | |

---

## Service Channel Plan

| Object | Service Channel Name | Capacity Weight | Notes |
|---|---|---|---|
| Case | Cases | 5 | |
| Chat Transcript | Chats | 3 | |
| (custom object) | | | |

---

## Presence Configuration Plan

| Status Name | Status Type | Service Channels | Capacity Ceiling | Assigned To (Profile/PermSet) |
|---|---|---|---|---|
| Available | Online | Cases, Chats | 10 | Support Agent Profile |
| Available - Cases Only | Online | Cases | 10 | |
| Break | Busy | none | — | |

---

## Skills Matrix (Skills-Based Routing Only)

| Agent Name | Skill 1 | Level | Skill 2 | Level | Skill 3 | Level |
|---|---|---|---|---|---|---|
| (Agent A) | Product CRM Support | 5 | | | | |
| (Agent B) | Product CRM Support | 3 | Product ERP Support | 3 | | |

---

## Skills-Based Routing Rules (Skills-Based Routing Only)

| Rule Name | Field API Name | Field Value | Required Skill | Min Level |
|---|---|---|---|---|
| Route by Product Line | Product_Line__c | CRM | CRM Support | 1 |
| Route by Product Line | Product_Line__c | ERP | ERP Support | 1 |
| Fallback (catch-all) | — | — | (none — route to general queue) | — |

---

## Checklist

Copy from SKILL.md Review Checklist and tick as completed:

- [ ] Omni-Channel enabled; Skills-Based Routing enabled if needed
- [ ] Service Channel exists for every object type being routed
- [ ] Routing Configuration created and assigned for every queue
- [ ] Presence Statuses and Configurations created with correct channel assignments
- [ ] Agents assigned to Presence Configurations via Profile or Permission Set
- [ ] Service Resource records created for every routing agent
- [ ] Service Resource Skills assigned (skills-based only)
- [ ] Skills-Based Routing Rules validated (skills-based only)
- [ ] End-to-end routing tested in sandbox
- [ ] Omni-Channel Supervisor confirms agents Available and work items routing

---

## Deviations and Notes

Record any deviations from the standard pattern and the business reason:

- (e.g., "Billing queue uses tab-based capacity instead of status-based because all work is uniform — agreed with stakeholder")
- (e.g., "Push Timeout set to 60s for voice queue because average ring time is 45s")
