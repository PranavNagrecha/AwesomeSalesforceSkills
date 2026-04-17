# Designer Shared Output Shape

Every designer that inherits `designer_base` emits an output document with these sections in this order. Domain-specific sections nest inside **Design** (design mode) or **Audit Findings** (audit mode).

## Required sections

### 1. Summary

One paragraph + a key-value block. Required keys:

```
- mode: <design | audit | single>
- target_org_alias: <alias or "(none — design-only)">
- scope: <domain-specific scope token>
- max_severity: <P0 | P1 | P2 | NONE>  [audit mode only]
- confidence: <HIGH | MEDIUM | LOW>
```

### 2. Design (design mode only)

Domain-specific design artifact. The designer's AGENT.md defines the exact subsections (e.g. sales-stage-designer has "Stage ladder", "Path + guidance"; omni-channel-routing-designer has "Capacity model", "Queue + routing topology"). This harness only requires that the content is scoped, named, and reviewable — NOT imperative, not executable.

### 3. Audit Findings (audit mode only)

Table with the same 7 columns as `audit_harness/output_schema.md`:

```
| code | severity | subject_id | subject_name | description | evidence | suggested_fix |
```

Codes use a designer-scoped prefix by convention (e.g. `SALES_STAGE_NON_MONOTONIC`, `PSET_DUPLICATE_OBJECT_PERMS`). Severity strict P0/P1/P2 per `agent_harness/severity_rubric.md`.

### 4. Process Observations

Per `AGENT_CONTRACT.md` — healthy / concerning / ambiguous / suggested follow-ups. Each with evidence pointing at a specific file, SOQL result, or MCP probe.

### 5. Citations

Every skill, template, decision-tree, MCP tool, probe, and harness doc consulted. Validator enforces resolution.

## Optional sections

Designers MAY include additional sections between **Design** and **Process Observations** when the domain calls for them, for example:

- **Metadata stubs** — XML or JSON for the domain's deploy artifact (e.g. `Sales Process` XML, Permission Set XML).
- **Cutover plan** — when the design implies replacing an existing live config.
- **Rollback plan** — same.
- **Migration recommendations** — routing to `automation-migration-router` or another agent.

Optional sections do NOT change the required order: Summary → Design/Audit → (optional sections) → Process Observations → Citations.

## Confidence rubric

Per `AGENT_CONTRACT.md` rubric, adapted for designers:

| Score | Condition |
|---|---|
| **HIGH** | All mandatory inputs supplied. Audit mode: all MCP probes returned without pagination. Design mode: every design section cites a skill or template. No freestyling. |
| **MEDIUM** | One probe paginated, one soft-optional input was missing and a sensible default was used, OR one design section was freestyled (no matching skill) but cross-referenced in Process Observations. |
| **LOW** | Target org unreachable in audit mode; required input substituted; critical skill/template citation resolves to a TODO; agent freestyled > 1 section. |

## What the shape does NOT constrain

- Domain-specific columns inside tables (designer defines).
- Subsection naming within Design (beyond "Design" as the top-level heading).
- Language / voice (each designer's tone can be more or less technical based on its persona).

## Validator enforcement

Agents declaring `harness: designer_base` must:

1. Emit the 5 required sections in the specified order.
2. Use P0/P1/P2 severity strictly when in audit mode.
3. Include a Process Observations block even when design-mode output has no findings (use the literal "nothing notable" string if honest).
4. End with a Citations block.

Violations emit validator ERRORs at PR time. This is belt-and-suspenders on top of `AGENT_CONTRACT.md`'s base requirements.
