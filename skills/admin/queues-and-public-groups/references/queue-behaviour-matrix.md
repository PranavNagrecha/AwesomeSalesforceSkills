# Queue Behaviour Matrix — Membership, Objects, Notifications, Visibility

What to ask, what to expect, and what each choice adds. Grounded in the Metadata API Developer Guide (`Queue` type, v62 PDF), the Object Reference (`Group`, `QueueSobject`, `GroupMember`), and the Help pages cited in `well-architected.md`. Claims that could not be re-verified against an official page are marked UNVERIFIED beside the claim.

## Questions to ask before creating a queue

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "Who works this pool, and how does that list change?" | Decides the member source: named users churn, roles and public groups maintain themselves | Membership that survives onboarding and offboarding without editing the queue |
| "Which objects will this queue own?" | A queue only owns objects listed in `queueSobject`; a rule or Omni configuration that targets it for another object fails | One queue per work pool, not one per object per team by accident |
| "Who should hear about a new record: a shared mailbox, every member, nobody?" | `email` and `doesSendEmailToMembers` are independent switches; the wrong pair is either silence or a flood | A notification design people will not filter to spam |
| "Should managers above the members see queue-owned records?" | `doesIncludeBosses` is the Grant Access Using Hierarchies checkbox | Deliberate visibility instead of the default |
| "Is Omni-Channel pushing from this queue?" | Without `queueRoutingConfig` the queue is a list view, not a routing target | The link that makes the queue part of the routing stack |
| "What happens to records still owned by the queue when it is retired?" | Queue-owned records are stranded when the queue goes away | A retirement step in the runbook (gotchas #2) |

## Membership sources

| Source (`queueMembers`) | Deploys by | Updates itself when | Sandbox caveat |
|---|---|---|---|
| `users/user` | Username | Never; a departure leaves a dead member (gotchas #4) | Usernames carry the sandbox suffix, so user members do not deploy between orgs |
| `roles/role` | Role developer name | A user changes role | None |
| `roleAndSubordinatesInternal` | Role developer name | Anyone joins a role below it; internal users only | Old `roleAndSubordinates` name is transitional (gotchas #6) |
| `publicGroups/publicGroup` | Group developer name | Group membership changes (maintained in Setup or via `GroupMember`) | Group members are records, not metadata; re-add after a refresh from source if they were sandbox-only |

Expect: membership is a union of all sources; a user reached through two sources is one member. Prefer roles and public groups; use named users only for individuals with no role that fits.

## Object support

| Object | Queue support | What it implies |
|---|---|---|
| Case, Lead | Yes | The only objects with assignment rules; an assignment rule entry targeting a queue must find the object in `queueSobject` |
| Task | Yes (API 48.0+) | Queue-owned tasks appear in no one's task list until accepted; pair with a list view per queue |
| ContactRequest, ServiceContract | Yes (ServiceContract when Entitlements are enabled) | Same visibility rule as Case |
| Custom objects | Yes when the object allows queues | `queueSobject` uses the API name with `__c` |
| Account, Contact, Opportunity | No | Ownership pooling for these needs a public group plus sharing, or a proxy user; not a queue |

Expect: one queue can own several objects. Removing an object from a queue that still owns records of that object is blocked or strands records (UNVERIFIED which; reassign first either way).

## Notifications

| `email` set | `doesSendEmailToMembers` | Who is notified when a record lands in the queue |
|---|---|---|
| no | `false` | Nobody; the record is visible only in the queue list view |
| yes | `false` | The queue address only (a shared mailbox or distribution list); members are not emailed individually (gotchas #5) |
| no | `true` | Each member individually |
| yes | `true` | The queue address and each member (UNVERIFIED that both fire; test in a sandbox before promising either) |

Two other emails can fire on the same event and are often confused with queue notification: the assignment rule entry's `template` email, and any Flow email alert on Case or Lead create. Decide which one the team should receive and switch the others off, or the first week of a new queue is three emails per record.

## Visibility and ownership

- Queue Ids start with `00G` (the `Group` object); `OwnerId` on a record is either a user (`005`) or a queue. Filter with `Owner.Type = 'Queue'`, not by Id prefix.
- Members can see and take queue-owned records through queue membership; with `doesIncludeBosses` = `true`, users above the members in the role hierarchy see them too.
- Queue-owned records are absent from "My Cases", "My Leads", and "My Tasks" until a member accepts them, and absent from ownership-based reports and roll-ups that assume a user owner (gotchas #1).
- Accepting is an owner change: the list view Accept button, an Omni-Channel push, or an escalation action all write `OwnerId`, and each of those fires record-triggered automation again.

## What a proper queue configuration adds

A pool whose membership follows the org chart, a notification channel someone actually reads, records that managers can see without manual sharing, and a routing target that assignment rules, escalation actions, and Omni-Channel can all name by developer name and deploy between orgs. "Just creating a queue" gives a list view and an email address.
