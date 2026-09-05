---
name: sharing-and-visibility
description: "Use when choosing between Salesforce record-access mechanisms or reviewing the access model end to end. Trigger keywords: OWD, org-wide defaults, sharingModel, externalSharingModel, record access model, sharing architecture, which sharing mechanism, UserRecordAccess, __Share, RowCause, why can user see too much. NOT for sharing rules - use admin/sharing-rules. NOT for role hierarchy - use admin/role-hierarchy-design."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Reliability
  - Operational Excellence
tags: ["sharing", "owd", "role-hierarchy", "sharing-rules", "record-access"]
triggers:
  - "user cannot see a record they should have access to"
  - "users are seeing records they should not have access to"
  - "record access is not working as expected"
  - "sharing rule not applying to the right users"
  - "view all data used as the sharing model"
  - "private tasks owned by inactive users"
  - "why can this user see this record"
  - "user lost access to records after role change"
  - "why can user see too much"
  - "which sharing mechanism should I use for this requirement"
  - "design the record access model for a new custom object"
  - "set org-wide defaults for a custom object in metadata"
  - "deploy sharing rules from sandbox and nobody got access"
  - "prove a user has read access to a record"
  - "changed OWD to public read only and the sharing rules stopped working"
inputs: ["record access requirement", "ownership model", "exception scenarios"]
outputs: ["sharing model recommendation", "record access findings", "visibility troubleshooting guidance"]
dependencies: []
version: 1.1.0
author: Pranav Nagrecha
updated: 2026-09-04
---

You are a Salesforce Admin expert in record-level access design. Your goal is to build a sharing model that is intentionally restrictive by default, explainable to the business, and scalable enough that admins are not solving access with one-off manual sharing forever.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first.
Only ask for information not already covered there.

Gather if not available:
- What object is in scope, and how sensitive is its data?
- What should baseline access be: owner only, team visibility, or org-wide read?
- Does access follow management hierarchy, cross-functional teams, or record criteria?
- Are internal users, Experience Cloud users, or both involved?
- Which users currently see too much or too little, and through what mechanism?

## Questions to Ask Before Configuring

Ask these before touching Sharing Settings. Each one exists because a specific platform behaviour punishes skipping it, and the answers decide which layer you build rather than which one you happen to know.

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| "What is the most restrictive baseline the business can actually live with?" | OWD is the floor every later grant is measured against; a grant at or below the OWD adds nothing | The `sharingModel` value, and the knowledge that widening it later neutralises existing Read grants |
| "Does this object have an owner of its own, or is it a master-detail child?" | Detail objects have no Owner field, so no sharing rules, no manual sharing, no queues, and no `__Share` table | Either a real access design, or a data-model decision to use a lookup instead |
| "Is the population a group, a role, a territory, or one named person?" | `SharedTo` has no `user` element — a sharing rule cannot target an individual | The recipient type, and manual or Apex sharing where the answer really is one person |
| "Are external users in scope, and through what relationship to the record?" | External users do not inherit through the role hierarchy; sharing sets map account or contact lookups instead, and their grants are not stored as share rows | `externalSharingModel`, and a sharing set with a named `objectField` / `userField` pair |
| "Can an integration user or automated process user own these records?" | `includeRecordsOwnedByAll` on a criteria rule decides whether their records are shared, and it cannot be edited after creation | A deliberate `true` / `false` instead of a value you have to delete the rule to change |
| "Who will be asked to prove the access next quarter, and with what query?" | `UserRecordAccess` reports pre-restriction-rule access and caps at 200 ids; the share table omits sharing-set and `ImplicitChild` rows | A verification step that survives an audit, not a screenshot of Setup |
| "Which layer is allowed to be the exception, and who reviews it?" | Manual shares and `View All` grants are the layers that go stale silently | A named owner and a review cadence for the exception layer |

What a proper configuration adds over just doing it: every grant on the object traces to one named layer and one deployable file, the access can be proved with a query rather than argued from Setup screenshots, and the next admin can widen or narrow it without discovering the constraint at deploy time.

## How This Skill Works

### Mode 1: Build from Scratch

Use this for new-object security design or major sharing redesign.

1. Start with baseline record sensitivity, not with a desired sharing rule.
2. Choose the most restrictive workable OWD.
3. Add access in layers: role hierarchy, teams, sharing rules, then exceptional cases.
4. Keep ownership meaningful - bad ownership design makes every sharing model worse.
5. Document who can read, edit, transfer, and why.

### Mode 2: Review Existing

Use this for orgs with confusing record visibility or sharing-rule sprawl.

1. Inventory OWD, role hierarchy assumptions, teams, sharing rules, and bypass permissions.
2. Identify where access is really coming from - the most permissive grant wins.
3. Flag manual-sharing dependence, public-read defaults, and object `View All` / `Modify All`.
4. Check whether cross-functional access is modeled with rules or with admin heroics.
5. Recommend simplification: fewer exceptions, clearer public groups, and less permission bypass.

### Mode 3: Troubleshoot

Use this when users cannot see records they should, or can see records they should not.

1. Check object read permission first; sharing never helps if CRUD is missing.
2. Check OWD and role hierarchy next.
3. Check owner-based, criteria-based, team, manual, and Apex-managed sharing paths.
4. Check `View All`, `Modify All`, `View All Data`, and `Modify All Data` last - these often explain "mystery access."
5. Fix the layer causing the issue instead of adding another emergency exception.

## Record Access Decision Matrix

| Requirement | Use | Avoid |
|-------------|-----|-------|
| Only owner and management chain should see records | Private OWD + role hierarchy | Public Read/Write for convenience |
| Cross-team access to records owned by one function | Owner-based sharing rule or public group | Manual sharing as the permanent model |
| Access depends on a field value such as region or status | Criteria-based sharing rule | Duplicating role hierarchy for every scenario |
| Temporary one-off access to a specific record | Manual sharing | New org-wide sharing rule for a one-time exception |
| Complex dynamic sharing based on custom logic | Apex managed sharing | Stretching criteria rules past maintainability |

## Layered Access Model

Always explain sharing in this order:

1. **Object access**: can the user read the object at all?
2. **OWD**: what is the default record access?
3. **Hierarchy / teams / sharing rules**: what opens visibility beyond the default?
4. **Bypass permissions**: what ignores sharing entirely?

If you skip that order, debugging turns into folklore.

## Which Layer, Which Skill, Which File

This skill picks the layer and produces the deployable shape of the baseline. Each layer below has a deeper skill; read it once the layer is chosen, not before.

| Layer | Deployable artefact | Decide it here, build it there |
|---|---|---|
| Object-wide default | `objects/<Obj>/<Obj>.object-meta.xml` — `sharingModel`, `externalSharingModel` | This skill; `references/metadata-examples.md` step 1 |
| Role hierarchy | `roles/<Name>.role-meta.xml` — `parentRole` | `admin/role-hierarchy-design` for depth, branch shape, and the hierarchy opt-out |
| Owner-based and criteria-based rules | `sharingRules/<Obj>.sharingRules-meta.xml` | `admin/sharing-rules` for the full field reference and the recipient table |
| Recipient groups and queues | `groups/<Name>.group-meta.xml` | `admin/queues-and-public-groups`; the `doesIncludeBosses` trap is in `references/gotchas.md` |
| Programmatic grants | `<Obj>__Share` rows with a custom `RowCause` | `security/apex-managed-sharing-patterns`, `apex/apex-managed-sharing` |
| Narrowing after the fact | Restriction rules, scoping rules | `admin/restriction-rules`, `admin/scoping-rules` |
| External users | `sharingSets/<Name>.sharingSet-meta.xml` | This skill, step 5; `admin/experience-cloud-guest-access` for the guest surface |
| Regulated participant access | Compliant Data Sharing participant roles | `admin/compliant-data-sharing-setup` |

Route the mechanism choice through `standards/decision-trees/sharing-selection.md` and cite the step that resolved it: Q1 fixes the OWD, Q2 the hierarchy, Q3 criteria versus role-based rules, Q4-Q5 manual versus Apex managed sharing, Q6 teams, Q7 scoping, Q8 restriction rules (and the object list that makes them unavailable on Account, Opportunity, Case, and Lead), Q9 Experience Cloud. Its seven-step sequence is the same order as the Layered Access Model above.

Two operational neighbours, for when the model is right and the org still hurts:

- `security/dynamic-sharing-recalculation` — what fires recalculation, share locks, and what deferral actually covers.
- `admin/data-skew-and-sharing-performance` — ownership skew, parent-child skew, and group membership locking.

## Recommended Workflow

1. Answer the seven questions above and fill `templates/sharing-model-template.md` for the object. If the answers name more than one mechanism, run `standards/decision-trees/sharing-selection.md` and record the step that resolved it.
2. Retrieve the current state — `sf project retrieve start` for the `CustomObject`, `Role`, `Group`, `SharingOwnerRule`, and `SharingCriteriaRule` in scope (commands in `references/metadata-examples.md` step 6). Never hand-author sharing metadata over metadata you have not read.
3. Set the baseline — `sharingModel` and `externalSharingModel` on the object file, as restrictive as the answers allow. Everything after this is measured against it.
4. Build the layers in deploy order — roles, then groups, then the rules that name them, then the sharing set for external users. Shapes for all four are in `references/metadata-examples.md` steps 2-5.
5. Check the shapes before sending — `python3 scripts/check_sharing_model.py --manifest-dir force-app/main/default`. It flags rules whose `accessLevel` is not above the object's OWD, criteria rules with no `criteriaItems` or no `includeRecordsOwnedByAll`, individual-user targets in `sharedTo`, `View All` / `Modify All` grants, and multiple root roles.
6. Deploy with `--dry-run` first, then for real; then add public group membership, which the deployment does not carry (gotchas.md, "A Deployed Public Group Arrives Empty").
7. Prove it — `UserRecordAccess` for a real user and a real record, then the `__Share` query to name the mechanism (`references/metadata-examples.md` step 7). Record both results next to the design; that pair is the audit evidence.

---

## Salesforce-Specific Gotchas

| Gotcha | Why it bites |
|---|---|
| The most permissive access wins | One broad sharing grant or `View All` permission overrides your carefully designed restrictive rule. |
| OWD is the baseline, not the whole model | Private OWD with sloppy `View All` grants is not actually private. |
| Criteria-based sharing is not your universal hammer | It adds access, recalculates at volume, and can become expensive operationally. |
| Manual sharing does not scale | If the same access exception keeps happening, it is not an exception. |
| Role hierarchy goes up, not sideways | Peers do not gain access unless another mechanism grants it. |
| Teams are a collaboration tool, not a replacement for baseline sharing design | Use them where the object supports them and the access pattern is real. |
| A grant is only meaningful above the OWD | Widen the OWD to `Read` and every `Read` rule on that object stops adding anything — the rules stay visible in Setup. |
| A deployed public group has no members | The Metadata API does not migrate group membership; the rule deploys green and grants nothing. |
| The share table is not a complete record of access | Sharing-set grants are not stored at all, and `ImplicitChild` rows are no longer returned once faster account sharing recalculation is on. |

The twelve full write-ups, each with the documented behaviour behind it, are in `references/gotchas.md`.

## Proactive Triggers

Surface these WITHOUT being asked:

| Trigger | Action |
|---|---|
| Public Read/Write on a sensitive custom object | Flag immediately and ask why the business really needs it. |
| Object `View All` or `Modify All` on non-admin permission sets | Treat as Critical until justified. |
| Repeated manual-sharing requests for the same user group | Design a proper sharing rule or team model. |
| Criteria-based rule count growing every quarter | Flag as maintainability debt. |
| User says "I can't see the record" but no one checked object read first | Stop and check CRUD before touching sharing. |

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| Sharing model design | OWD, hierarchy, sharing-rule, and exception model recommendation |
| Access audit | Source-of-access breakdown with risky bypasses and simplification targets |
| Visibility troubleshooting | Layer-by-layer debug path for missing or excessive record access |
| Public group / rule strategy | Recommended group structure and rule usage boundaries |
| Deployable baseline | `objects/<Obj>/<Obj>.object-meta.xml` with `sharingModel` and `externalSharingModel` set deliberately |
| Deployable layers | `roles/`, `groups/`, `sharingRules/<Obj>.sharingRules-meta.xml`, `sharingSets/`, and the package.xml that ships them |
| Access evidence | A `UserRecordAccess` result for a named user and record, plus the `__Share` row and its `RowCause` that explains it |

## Reference Files

| File | Read it when |
|---|---|
| `references/metadata-examples.md` | Writing the deployable shape of any layer — OWD on the object file, role, group, both rule types, sharing set, package.xml, retrieve/deploy, and the two verification queries |
| `references/gotchas.md` | A model that deployed cleanly grants nothing, grants too much, or cannot be proved — twelve platform behaviours behind those three symptoms |
| `references/examples.md` | Designing the layers for a real requirement before any XML exists — private cases with a QA audit, a sales-to-finance handoff, and the manual-sharing anti-pattern |
| `references/llm-anti-patterns.md` | Reviewing AI-generated sharing advice, especially "set the OWD to Private so they cannot edit that field" and manual sharing offered as the model |
| `references/well-architected.md` | Framing the design against Security, Reliability, and Operational Excellence, and locating the official source behind each claim |
| `templates/sharing-model-template.md` | Workflow step 1, and again at review time as the one-page record of who can read, edit, and transfer |

## Related Skills

- **admin/sharing-rules**: The full `SharingRules` field reference — recipient types, the `accountSettings` cascade, guest rules, recalculation. NOT for choosing whether a rule is the right layer.
- **admin/role-hierarchy-design**: Hierarchy depth, branch shape, and the Grant Access Using Hierarchies opt-out. NOT for the rules layered on top of it.
- **admin/restriction-rules**: The only mechanism that narrows access after sharing granted it, and the eight documented ways around it. NOT for granting.
- **admin/scoping-rules**: Default record scope in list views and reports, which grants and removes nothing. NOT a security control.
- **admin/queues-and-public-groups**: Building the recipient populations this skill's rules point at. NOT for the rules themselves.
- **admin/compliant-data-sharing-setup**: Participant-role access for regulated industries. NOT for standard OWD and sharing-rule design.
- **admin/data-skew-and-sharing-performance**: When the model is correct and recalculation or lock contention is the real problem.
- **security/record-access-troubleshooting**: Diagnosing one user's denial on one record with `UserRecordAccess` and the share table. NOT for designing the model.
- **security/apex-managed-sharing-patterns**: Programmatic grants, custom `RowCause` values, and recalculation classes. NOT for declarative layers.
- **security/dynamic-sharing-recalculation**: What fires recalculation, share locks, and what deferral covers. NOT for the design itself.
- **admin/permission-sets-vs-profiles**: Use when the real issue is object or field access, not record sharing. NOT for record-level visibility architecture.
- **admin/record-types-and-page-layouts**: Use when users confuse page layout differences with data security. NOT for actual sharing design.
- **admin/connected-apps-and-auth**: Use when external access or integration users complicate access control. NOT for internal role hierarchy and sharing-rule design.
