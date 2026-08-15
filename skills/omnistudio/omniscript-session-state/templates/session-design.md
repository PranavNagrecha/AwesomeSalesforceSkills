# OmniScript Session Design

## 0. The deciding question

> **Can you delete this state on your own schedule?**

- Does a **retention obligation** attach to this state? [ ] yes  [ ] no
- Do you need to **query across sessions** (reporting, resume-by-subject,
  abandonment analysis)? [ ] yes  [ ] no
- Is the audience **guest / unauthenticated**? [ ] yes  [ ] no

**Any "yes" → you need a custom object.** `OmniScriptSavedSession` is a
standard object marked "for internal use only. Don't perform any create, edit,
or delete operations on this object," so native Save for Later is a store you
can populate but cannot lawfully manage.

**All "no" → native Save for Later** is a configuration, not a project.
Building a custom store here is over-engineering.

Store chosen: [ ] Native Save for Later  [ ] Custom object  [ ] Big Object

## 1. OmniScript

- Name / Type / SubType / Language:
- `uniqueName` (Type_SubType_Language_VersionNumber):
- Number of steps:
- Typical completion time:
- Embedded child OmniScripts? [ ] yes ( `isOmniScriptEmbeddable` = true ) [ ] no
- [ ] Save configuration is on the **PARENT** OmniScript
      (configuring it on a child is a silent no-op)

## 2. Payload budget

Save for Later fails above **4,194,304 characters (4 MB)**, and the network
payload is significantly larger than the visible Data JSON.

| Category | In the saved payload? |
|---|---|
| The user's answers | **yes** |
| Lookup data (catalogs, code tables, picklist option sets) | **no** — re-fetch on resume from a cacheable Integration Procedure |
| File content | **no** — store the document, keep an id |
| Derived values recomputable from answers | **no** — prune |

- Measured request payload at the **LAST** step: ______ characters
- [ ] Under 4,194,304 with headroom
- [ ] Measured at the last step, not a middle one, and against the request —
      not the Data JSON in the debug panel

## 3. State schema (custom object only)

The fields you **filter on** are never the fields you **encrypt** — Shield
encryption restricts SOQL filtering.

| Field | Type | Encrypted? | Filtered on by the purge? |
|---|---|---|---|
| `Answers_JSON__c` | Long Text Area | **yes** | no |
| `ExpiresAt__c` | DateTime | **no** | **yes** |
| `Status__c` | Picklist | **no** | **yes** |
| `Version__c` | Number | no | no |
| `LastSavedAt__c` | DateTime | no | no |
|  |  |  |  |

- [ ] No PII stored in a plaintext field
- [ ] SSN / card numbers tokenized rather than stored
- [ ] No encrypted field appears in a `WHERE` clause anywhere

## 4. Save cadence

- [ ] Step transition (default — each save posts the **whole** payload)
- [ ] Debounced in-step save — **justify**: ______________________
- [ ] Never on input change

## 5. Resume path

- Token type: opaque random value indexing a server-side row
- [ ] The URL carries the token and **nothing else** — no answers in any
      encoding, no PII, no raw session record Id
- [ ] A **hash** of the token is stored server-side, not the token
- [ ] Token bound to the subject it was issued for
- Expiry: ______ (hours, not days)
- [ ] Single-use where the flow allows it
- [ ] Referrer policy set on the resume page (any outbound link can leak the
      token in the `Referer` header)
- [ ] Re-authentication branch handled — Experience Cloud session lifetime and
      OmniScript session lifetime are **independent**, so the resume path must
      verify identity rather than assume it

## 6. Concurrency

Native Save for Later: multi-user editing of one session is **not supported**
and **not blocked** — the second save is accepted and the damage surfaces when
the original user resumes.

- [ ] Handoff between users is modelled as a **record-ownership change**
      (user A submits to a record you own and ends their session; user B starts
      a new instance pre-populated from it)
- [ ] If concurrent editing is genuinely required: custom object with
      `Version__c`, compared on save, mismatch routed to an explicit conflict
      branch. Never a silent overwrite.
- Conflict UX:

## 7. Retention

- Tier: [ ] 1 sensitive  [ ] 2 non-sensitive  [ ] 3 non-PII only
- Expiry duration:
- Confirmed with data owner (name + date):
- Purge mechanism (job name, schedule):
- [ ] The purge filters on a **plaintext** field
- [ ] For guest flows: session state is purged in the **same job** as the intake
      row, so the two cannot drift apart
- [ ] **No DML anywhere against `OmniScriptSavedSession`**

## 8. Version-change plan

Saved sessions are tied to the OmniScript definition version active when the
session was created. Deactivating and reactivating means previously saved
sessions do not resume as the same instance — a new instance is created, and
older saved instances **remain stored in the system**.

- In-flight session count at time of planning: ______
- [ ] Can the change wait for the tail to drain? If not:
- [ ] Users notified **before** the deploy, not after they find an empty form
- [ ] If state must survive version changes, answers are mirrored into a custom
      object at step boundaries — the native saved session cannot do this
- [ ] Orphaned-instance growth recorded in the retention risk register

## Sign-Off

- [ ] Store choice follows from the deleting-on-schedule question
- [ ] Save configured on the parent OmniScript
- [ ] Payload measured at the last step, under 4 MB with headroom
- [ ] Answers only — lookup data and file content excluded
- [ ] PII encrypted or tokenized; filtered fields left plaintext
- [ ] URL carries an opaque token only; hash stored server-side
- [ ] Referrer policy and re-authentication branch in place
- [ ] Version-based conflict detection, or handoff modelled as ownership
- [ ] Expiry field plus a scheduled purge that references it
- [ ] Activation changes planned as migrations
