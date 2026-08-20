# P03 — Access Path Explainer

**Lifecycle target:** release-candidate target  
**Primary command:** `/why-cant-user`  
**Product agent:** `access-path-explainer`

## User job

Explain why a specific Salesforce user can or cannot see, create, edit, delete, or invoke an object, field, record, record type, or action.

## Personas and modes

- Personas: admin, developer, security-reviewer, consultant, architect
- Modes: fixture, live-read-only, hybrid, scratch-qa

## Inputs

| Input | Requirement | Meaning |
|---|---|---|
| `user` | required | User ID, username, or explicit fixture identity |
| `resource` | required | Object, field, record, record type, action, or capability |
| `operation` | required | read/create/edit/delete/transfer/execute/assign or product-defined action |
| `target_org` | conditional | Explicit org alias/username |
| `record_id` | optional | Record for record-level explanation |

At least one valid evidence input path must exist. Optional project inspection follows explicit path, one unambiguous active workspace, bounded roots, then standalone. The SfSkills repository itself is never assumed to be the target Salesforce project.

## Required evidence

- User/license/profile/permission-set context
- Resource identity and requested operation

## Optional enrichment

- Permission-set groups and muting
- CRUD/FLS/record type
- sharing/restriction/territory/team/manual/Apex sharing
- record ownership and role hierarchy
- page/action visibility
- automation or validation that blocks the operation

## Evidence tools

`get_user_access_evidence`, `get_record_access_evidence`, `get_org_identity`, `describe_salesforce_component`

Tools are product-read-only. QA setup may create scenario evidence only inside disposable scratch orgs under a separate authority.

## Required findings

- access decision by layer
- first blocking control
- granting paths
- conflicting or muted permissions
- record-level path
- UI versus platform permission distinction
- evidence gaps
- least-privilege remediation options

Each material finding is a typed claim with support links. Recommendations reference the claims and constraints they address.

## Context plan

1. Load product contract, output schema, authority, and target identity.
2. Load 3–5 core Salesforce knowledge items.
3. Classify observed evidence and add only conditional packs needed for those classes.
4. Target no more than 8 knowledge/reference files; hard stop/overflow at 12.
5. Bound each injected tool page to 32 KiB and preserve continuation metadata.
6. Pass structured handoffs only.
7. Checkpoint at evidence-ready and draft-ready boundaries.

## Agent flow

```text
command/input validation
  -> sf-context-librarian
  -> sf-project-inspector (optional)
  -> sf-org-grounder or fixture loader
  -> access-path-explainer
  -> deterministic evidence lint
  -> sf-evidence-reviewer
  -> final envelope
```

Host limitations may require the parent to perform MCP calls and pass normalized evidence to a read-only subagent. The behavior contract remains the same.

## Known-truth scenarios

- `ACC-FLS`
- `ACC-OBJECT-CRUD`
- `ACC-RECORD-SHARING`
- `ACC-RESTRICTION-RULE`
- `ACC-MUTING`
- `ACC-LICENSE`
- `ACC-RECORD-TYPE`

## Quality gates

- Never says “profile issue” without tracing layers
- Separates object/field/record/UI/automation causes
- Sensitive user and record data are minimized
- Unknown evaluation paths are explicit

## Failure and status behavior

- `refused`: unsafe request, missing mandatory input, or unresolved target ambiguity.
- `partial`: useful findings but missing/stale/truncated/contradictory evidence.
- `failed`: unexpected system/tool failure prevents valid output.
- `completed`: required evidence, deterministic lint, and independent review all pass.

## Known limitations

- Does not assign permissions or modify sharing
- Some formula/Apex/custom UI decisions may require code/project evidence
- Record-level access explanation may be partial when APIs do not expose a decisive reason

## Product metrics

- time to first useful finding;
- required-finding recall;
- root-cause rank;
- unsupported material claim rate;
- evidence-reference validity;
- context files/tokens and tool bytes;
- status correctness;
- repeat use and user acceptance.
