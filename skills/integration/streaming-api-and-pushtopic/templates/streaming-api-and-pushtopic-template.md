# Streaming API and PushTopic — Work Template

Use this template when working on tasks in this area.

## Scope

**Skill:** `streaming-api-and-pushtopic`

**Request summary:** (fill in what the user asked for)

---

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here before writing any code or configuration.

- **Salesforce API version in use:**
- **Authentication method for the CometD client** (OAuth JWT, username-password, web server flow):
- **Channel type needed** (PushTopic for sObject change events OR Generic Streaming for arbitrary payloads):
- **Estimated concurrent subscriber count per channel:**
- **Event retention requirement** (less than 24 hours = Streaming API OK; more than 24 hours = Platform Events):
- **Replay strategy** (-2 new events only, -1 all retained, or specific stored replayId):

---

## PushTopic Definition (if applicable)

Fill in these fields before writing the Apex or REST payload:

| Field | Value |
|---|---|
| Name | |
| Query | `SELECT <fields> FROM <Object> WHERE <condition>` |
| ApiVersion | (24.0 minimum, use current API version) |
| NotifyForOperationCreate | true / false |
| NotifyForOperationUpdate | true / false |
| NotifyForOperationDelete | true / false |
| NotifyForOperationUndelete | true / false |
| NotifyForFields | Referenced / Select / All / Where |

**SOQL Validation Checklist (complete before inserting):**

- [ ] No aggregate functions (COUNT, SUM, AVG, MIN, MAX, GROUP BY)
- [ ] No relationship fields in SELECT (e.g., `Account.Name`)
- [ ] No LIMIT or OFFSET clause
- [ ] No semi-join (IN with subquery) in WHERE
- [ ] Query references only fields on the root object in SELECT

---

## Generic Streaming Channel Definition (if applicable)

| Field | Value |
|---|---|
| Channel Name | `/u/<ChannelName>` |
| Publisher | (Apex, Java REST client, other) |
| Payload schema | (describe the JSON structure) |
| Broadcast or targeted? | All subscribers (`userIds: []`) or specific users |

---

## CometD Client Configuration

| Parameter | Value |
|---|---|
| CometD URL | `<instanceUrl>/cometd/<apiVersion>` |
| Client library | EMP Connector (Java) / cometd npm (JS) / empApi (LWC) / custom |
| Replay ID storage | (database table, file, in-memory — note if durable) |
| Initial replay value | -2 (new only) / -1 (all retained) / stored ID |
| Token refresh mechanism | (describe how the client re-authenticates on session expiry) |

---

## Approach

Which mode from SKILL.md applies?

- [ ] Mode 1: Creating a PushTopic and subscribing via CometD
- [ ] Mode 2: Generic Streaming for custom payloads
- [ ] Mode 3: Troubleshooting connection drops and missed events

Describe the specific approach and why it was chosen:

---

## Review Checklist

Copy from SKILL.md and tick items as you complete them:

- [ ] PushTopic SOQL does not use aggregate functions, LIMIT, OFFSET, relationship fields in SELECT, or semi-joins.
- [ ] `ApiVersion` on the PushTopic is 24.0 or higher; CometD URL version matches.
- [ ] `NotifyForFields` is set deliberately.
- [ ] CometD client persists `replayId` to durable storage before processing each event.
- [ ] Client re-issues `connect` immediately after each server response.
- [ ] Concurrent subscriber count estimated and within limits (100 per channel, 1,000 org-wide).
- [ ] Authentication token refresh is handled.
- [ ] For Generic Streaming, `StreamingChannel` record exists and users have Streaming API permission.
- [ ] Event retention requirement confirmed within 24-hour window.

---

## Notes

Record any deviations from the standard pattern and why:
