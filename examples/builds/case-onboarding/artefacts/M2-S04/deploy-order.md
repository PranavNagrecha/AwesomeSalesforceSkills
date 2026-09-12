# Deploy order — M2-S04 (Case queues and public groups)

Built by `agents/metadata-builder` under `agents/build-step-runner`. Nothing here was deployed.

## Order inside this step

| # | Component | Type | Why it must come at this point |
|---|---|---|---|
| 1 | `Support_Tier_1`, `Support_Tier_2`, `Billing_Team` | `Group` | Each queue's `<queueMembers><publicGroups><publicGroup>` names its group by developer name. `skills/admin/queues-and-public-groups/references/metadata-examples.md` states it directly: "Deploy the group before any queue or sharing rule that names it." |
| 2 | `Tier_1_General`, `Tier_2_Engineering`, `Billing` | `Queue` | Depends on row 1 only. |

A single `sf project deploy start --manifest artefacts/M2-S04/package.xml` satisfies both rows in
one request; the ordering matters only if the two types are split across requests.

## Where this step sits in the build's own order

The same reference states why this step is early: "Queues are the routing targets every
assignment rule, escalation action, and Omni-Channel routing configuration names by developer
name, so they deploy **first**." Every downstream component that names one of these three queues
must be deployed after this manifest:

| Downstream component | Step | What it references |
|---|---|---|
| `Case.assignmentRules` / `Case.autoResponseRules` | M3-S04 | `assignedTo` = a queue developer name (`Tier_1_General` as the Q26 catch-all) |
| `Tier_1_Push.queueRoutingConfig` and the Omni-Channel stack | M3-S05 | pushes work *from* `Tier_1_General` |
| Escalation rules reassigning to Tier 2 after 8 business hours | M4 | escalation action target = `Tier_2_Engineering` |

## Dependencies on components OUTSIDE this step

**None that must be deployed first.** That is unusual enough to state rather than leave implied:

- `<queueSobject><sobjectType>Case</sobjectType></queueSobject>` names the **standard** Case
  object. It is platform-provided, so this manifest does not depend on M1-S01's
  `CustomObject Case` file even though that file exists in the build. No custom field, record
  type or layout is referenced by a `Queue` or a `Group`.
- **Nothing here references M2-S02**, this step's declared `depends_on`. `Queue` membership
  accepts users, roles, role-and-internal-subordinates and public groups — it cannot name a
  permission set or a permission set group, so `Case_Tier1` / `PSG_Tier1_Prod` and their siblings
  are not referenced and cannot be. The dependency is a sequencing choice in the plan (access
  model before work pools), not a metadata reference. Recorded because a reader looking for the
  PSG names in these six files will not find them, and that is correct rather than missing.

### One forward reference, deliberately not written

`Tier_1_General` carries **no** `<queueRoutingConfig>` element. The value it would carry,
`Tier_1_Push`, is built by **M3-S05**, which `depends_on` M2-S04 — so at this step's deploy time
that component does not exist and naming it would be a dangling reference.

Note the ordering conflict this exposes, because it is a plan-level fact and not something this
step can fix: `queues-and-public-groups/references/metadata-examples.md` says "Deploy the routing
configuration before the queue" and warns that "Omitting it on an Omni-Channel org means the
queue is never pushed". The plan orders the two the other way round. The consequence is concrete
and bounded: **`Tier_1_General` is a list-view queue until the element is added.** The second
pass is either

- deploy M3-S05's `queueRoutingConfig` and then re-deploy `Tier_1_General.queue-meta.xml` with
  `<queueRoutingConfig>Tier_1_Push</queueRoutingConfig>` added (alphabetically after
  `queueMembers`, before `queueSobject`), or
- deploy M2-S04 and M3-S05 in one request, with the element present.

Either way it is a change to this file that a human has to make or a re-plan has to schedule. It
is flagged to the M2 gate rather than silently deferred.

## Decisions worth reading before deploy

1. **`<doesIncludeBosses>` is absent from all three `Queue` files and present on all three
   `Group` files.** Not an oversight. The cited reference's version table dates
   `doesIncludeBosses` on `Queue` at **API 67.0+**, and this manifest is `62.0` — writing it would
   be an element the target API version does not carry. On `Group` it is available and documented
   with no version gate, so it is written there. Grant Access Using Hierarchies for
   *queue-owned* records therefore falls to the org's own setting at 62.0; if that visibility
   must be explicit on the queue, the manifest has to move to 67.0 first.
2. **`<doesIncludeBosses>true</doesIncludeBosses>` on the three groups is a skill default, not an
   answered decision.** No clarification asks whether managers above the members should see
   queue-owned records. `queues-and-public-groups` says to "leave it `true` unless managers must
   not see queue-owned records", so `true` is written and labelled a default here. If Q13's
   deferred finance-visibility question resolves toward record-level separation, `Billing_Team`
   is the file to revisit.
3. **`doesSendEmailToMembers` is `false` on all three queues.** Q88 answers "a shared mailbox per
   queue rather than every member". `false` is the encoding of "not every member"; with `email`
   set, only the queue address is notified.
4. **`Billing` carries `<email>billing@acme.example</email>` — and that address is also the
   Email-to-Case inbound address.** Q88 says Billing "wants the queue address emailed", and
   `billing@acme.example` is the only Billing address anywhere in `requirement.md`, so the value
   is grounded. The risk is not: this is the same class of loop the answer key flags for the
   acknowledgement sender ("an org-wide email address, never the Email-to-Case routing address
   itself"). A queue-assignment notification sent to an address that Email-to-Case reads can
   create a case, which lands in a queue, which sends another notification. **Cover this in
   Q68's sandbox loop test explicitly for the Billing queue**, and if it fires, the fix is a
   separate monitored alias for queue notification rather than the intake address.
5. **No `<fullName>` on any of the six files; the file stem is the developer name.** The cited
   reference states it: "The developer name is the file name; `name` inside the file is the
   label." Stems are therefore `Tier_1_General`, `Tier_2_Engineering`, `Billing`,
   `Support_Tier_1`, `Support_Tier_2`, `Billing_Team` — no spaces — and the labels in `<name>`
   carry the spaced human form. This is the M1 mock-deploy F-11 rule applied ahead of time: the
   CLI names the package member from the stem, so a stem that disagrees with the member is "not
   found in zipped directory". `admin/data-skew-and-sharing-performance`
   `references/metadata-examples.md` § 2 shows a `Group` *with* `<fullName>`; both shapes are
   documented, and omitting it removes the whole class of stem-vs-fullName divergence.
6. **`package.xml` members are bare developer names.** `Queue` and `Group` are not child
   components, so there is no `Object.Member` prefix — unlike the record types and layouts in
   M1. The reference's own manifest example shows exactly this shape. Members are explicit rather
   than `*`, even though both types accept the wildcard, because a wildcard would pull every
   queue and group in the target org into scope.
7. **Group membership is not in this deploy.** "Members of the public group aren't migrated when
   you deploy the group type." All three groups deploy **empty**, and an empty group behind a
   queue is a pool with nobody in it. The `GroupMember` load for the 12 / 4 / 2 users (Q8) is a
   post-deploy data step, listed in `queue-retirement-runbook.md` § 6. A green deploy here is not
   a working queue.

## Elements this step could NOT ground

Recorded rather than invented, per `standards/build-orchestration.md` § 8.

1. **No `<roles>` or `<roleAndSubordinatesInternal>` member on any queue.** Q29's answer is
   "by role **and** public group, no named users" — the public-group half is written, the role
   half is not, because **no role developer name exists anywhere in this build**: not in
   `requirement.md`, not in any of the 97 clarifications, not in an upstream step's artefacts.
   The reference is explicit that these members deploy by role developer name, so writing one
   would mean inventing the name of a role hierarchy nobody has described. Membership is
   therefore carried entirely by the three public groups. **If the org's role hierarchy is meant
   to feed these queues directly, that is a change to all three queue files and it needs the role
   developer names first.**
2. **No `<email>` on `Tier_2_Engineering`.** Q88's answer for Tier 2 is the accepted default, "a
   shared mailbox per queue rather than every member" — a *posture*, with no address. No Tier 2
   mailbox is named in `requirement.md` or in any answer; the two addresses on file
   (`support@acme.example`, `billing@acme.example`) are the general and finance intake addresses
   and neither is Tier 2's. An invented `tier2-@acme.example` would look grounded and route real
   notifications nowhere, so the element is omitted and `doesSendEmailToMembers` stays `false`,
   which is the documented "nobody is notified; the record is visible in the queue list view"
   row of the notification matrix. **This is a gap to close before go-live, not a design
   choice.** Consequence for the tester, stated plainly: `check_queues.py` emits **two** WARNs
   over this step (Tier 1 General and Tier 2 Engineering, both "No `<email>` configured"), while
   the step's declared `acceptance_tests[0].expected` names only the Tier 1 one. Exit code is
   still 0 and the test still passes on its stated condition; the description was written from a
   fixture in which Tier 2 carried an address. It should be corrected to name both, or Tier 2's
   address should be answered.
3. **No fall-through owner if `Tier_1_General` itself is retired.** Q26 makes `Tier_1_General`
   the catch-all for everything else, which leaves it with no target of its own. Recorded in
   `queue-retirement-runbook.md` § 4 step 2 as a decision the process owner must take before
   that queue is ever touched.
4. **Whether `Billing_Team` should see non-billing cases, or be excluded from them, is
   untouched here.** Q13 is DEFERRED and the plan's assumption A1 takes the conservative reading.
   Record access to a Case in this build is decided by the Private OWD (M1-S01) and the
   criteria-based sharing rule (M2-S05) — not by queue or group membership, which grants access
   only to the records the queue owns.

## Validate-only command for a human to run

Never run by an agent in this loop. Copy the artefacts into a DX source tree first — the path
below is relative to that tree, not to the build directory.

```bash
sf project deploy start \
    --manifest manifest/package.xml \
    --dry-run \
    --target-org <your-sandbox-alias>
```

Then verify, per the cited reference's own post-deploy queries:

```sql
SELECT Queue.DeveloperName, Queue.Email, SobjectType
FROM QueueSobject WHERE SobjectType = 'Case'

SELECT Id, Name, DeveloperName, Type FROM Group
WHERE DeveloperName IN ('Support_Tier_1','Support_Tier_2','Billing_Team','Tier_1_General','Tier_2_Engineering','Billing')
```

The second query returns both the public groups (`Type` = `Regular`) and the queues (`Type` =
`Queue`), because a queue is a `Group` row; a queue id starts `00G`. Expect six rows and
**zero `GroupMember` rows** until the post-deploy membership load runs.
