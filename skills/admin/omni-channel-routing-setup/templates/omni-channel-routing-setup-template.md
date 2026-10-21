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

| Queue Name | Routing Model | Skills-based (isAttributeBased) | Priority | Capacity Weight | Push Timeout |
|---|---|---|---|---|---|
| (queue 1) | Least Active / Most Available | false / true | 1 | 5 | 30s |
| (queue 2) | | | | | |
| (queue 3) | | | | | |

Capacity weight is a routing-configuration field; the service channel has none.

---

## Service Channel Plan

| Object | Service Channel Name | Capacity Model (status / tab) | Notes |
|---|---|---|---|
| Case | Cases | Status-based | |
| Chat Transcript | Chats | Tab-based | |
| (custom object) | | | |

---

## Presence Status Plan (channels; access via Profile or Permission Set)

| Status Name | Service Channels | Status Access Granted To |
|---|---|---|
| Available | Cases, Chats | Support Agent Profile |
| Available - Cases Only | Cases | |
| Break | none (treated as Away) | |

## Presence Configuration Plan (capacity; assigned to Profiles or Users)

| Configuration Name | Capacity Ceiling | Assigned To (Profile / User) |
|---|---|---|
| Support Agent - Full Capacity (10) | 10 | Support Agent Profile |

---

## Skills Matrix (Skills-Based Routing Only)

| Agent Name | Skill 1 | Level | Skill 2 | Level | Skill 3 | Level |
|---|---|---|---|---|---|---|
| (Agent A) | Product CRM Support | 50 | | | | |
| (Agent B) | Product CRM Support | 30 | Product ERP Support | 30 | | |

Skill levels range 0–99.99; record the team's convention here.

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
- [ ] Presence Statuses created with correct channels; Presence Configurations with the capacity ceiling
- [ ] Agents assigned to Presence Configurations by Profile or User; status access granted by Profile or Permission Set
- [ ] Service Resource records created for every skills-based routing agent
- [ ] Service Resource Skills assigned (skills-based only)
- [ ] Skills-Based Routing Rules validated (skills-based only)
- [ ] End-to-end routing tested in sandbox
- [ ] Omni-Channel Supervisor confirms agents Available and work items routing

---

## Deviations and Notes

Record any deviations from the standard pattern and the business reason:

- (e.g., "Billing queue uses tab-based capacity instead of status-based because all work is uniform — agreed with stakeholder")
- (e.g., "Push Timeout set to 60s for voice queue because average ring time is 45s")
