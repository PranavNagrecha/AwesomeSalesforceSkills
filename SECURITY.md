# Security Policy

SfSkills is a Salesforce skill and agent framework consumed by AI coding
assistants (Claude Code, Cursor, Windsurf, Aider, Augment, Codex, raw MCP
clients). It is content plus local tooling — there is no hosted service and no
server we operate. This document covers how to report a security issue and
which controls are actually implemented, as distinct from conventions the
project asks contributors to follow.

## Reporting a Vulnerability

**Do not open a public GitHub issue for a security vulnerability.**

- **Preferred:** open a [private security
  advisory](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/security/advisories/new).
  This keeps the report private while a fix is prepared and lets us credit you
  on disclosure. If GitHub tells you private reporting is not enabled on the
  repository, fall back to the next option and say so in your message.
- **Fallback:** start a private thread via [GitHub
  Discussions](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/discussions)
  or contact the maintainer through their GitHub profile
  ([@PranavNagrecha](https://github.com/PranavNagrecha)). Put `SECURITY` in the
  subject and do not include exploit detail in a public thread.

This is a single-maintainer project. We aim to acknowledge within 72 hours and
to triage within 7 days, and we will agree a disclosure timeline with you based
on severity — but treat those as targets, not a contractual SLA. If you have
had no response in a week, ping the advisory thread.

## What Counts As A Vulnerability Here

### In scope

1. **Skills that recommend insecure Salesforce patterns.**
   - A skill that recommends `without sharing` with no justification, no
     counter-example, and no WAF-Security note.
   - A skill that recommends storing OAuth credentials in Custom Settings.
2. **Agents that bypass CRUD/FLS or the `with sharing` default without
   justification.**
   - A run-time agent whose Plan says "use `Database.query` with a
     user-supplied string" and offers no parameterization guidance.
3. **MCP tool implementations that enable SOQL injection or bypass the `sf`
   CLI's auth boundary.**
   - A probe that interpolates user input into SOQL without passing it through
     `_validate_api_name`.
4. **Validators or pipelines that execute user-supplied strings as code**
   (e.g. `eval()` over content pulled from a skill file).
5. **Build-time scripts that send data outside the local repo without explicit
   user consent.**
6. **Dependency vulnerabilities** in what we ship: `PyYAML` and `jsonschema` in
   the root `requirements.txt`; `mcp`, `jsonschema`, and `referencing` in
   `mcp/sfskills-mcp/pyproject.toml`; the optional `fastembed` extra.
7. **Credential leakage through tool output** — see the redaction section
   below, which exists because this happened once.

### Out of scope (still welcome as ordinary bugs)

- Insecure Salesforce patterns mentioned only as anti-patterns in
  `references/llm-anti-patterns.md` or in gotchas.
- Misconfiguration of a consumer's own Salesforce org.
- Speculation about future platform changes that might make a skill wrong.
- Spelling or style issues in skill content.

## Security Posture Of The Framework

The subsections below separate **enforced** controls (a script, test, or
validator fails the build) from **conventions** (written expectations that
review has to catch).

### Credential redaction in `sf` CLI output — enforced

`mcp/sfskills-mcp/src/sfskills_mcp/sf_cli.py` scrubs credential-shaped strings
at two layers, and `tests/test_sf_cli_redaction.py` pins the behavior as a
regression guard. The comment block in `sf_cli.py` records why: `sf org
display` prepended a warning line, `json.loads` failed, and the error path
returned raw stdout — which contained the access token.

- `_redact_credentials_text` — regex scrub over arbitrary text (any path that
  returns raw stdout).
- `_redact_credentials_in_payload` — walks parsed JSON and replaces
  credential-valued keys.

Replacement value is the literal `[REDACTED]`. Any new code path that surfaces
`sf` output must go through one of these.

### SOQL injection guard — enforced

- All interpolated API names pass `_validate_api_name` (defined in
  `_shared.py`, re-exported from `admin`), which requires
  `^[A-Za-z][A-Za-z0-9_]*$`. Deliberately tighter than the SOQL spec.
- `tooling_query` refuses any statement that does not start with `SELECT`,
  refuses DML statement tokens (`INSERT`, `UPDATE`, `DELETE`, `UPSERT`,
  `MERGE`) and `;`, and bounds rows at `MAX_TOOLING_QUERY_ROWS` (2000).
  Detection looks at statement tokens rather than string-literal content, so
  `WHERE Name = 'foo INSERT bar'` still runs.
  `tests/test_tooling_query_blocklist.py` covers this.

### MCP tool surface — enforced

The server registers **38 tools**. By annotation profile
(`mcp.types.ToolAnnotations`, set in `server.py`):

| Profile | Count | `readOnlyHint` | `openWorldHint` |
|---|---|---|---|
| `_ANN_REPO_ONLY` | 13 | `True` | `False` |
| `_ANN_ORG_READ` | 24 | `True` | `True` |
| `_ANN_ENVELOPE` | 1 | `False` | `False` |

- **No tool writes to the org.** All 24 org-touching tools — the `list_*` /
  `describe_*` / `get_apex_*` / `get_lwc_*` readers, `tooling_query`,
  `validate_against_org`, and every `probe_*` — issue SOQL or Tooling API reads
  only.
- The single non-read-only tool is `emit_envelope`, which writes an agent's
  output envelope to `docs/reports/<agent>/<run_id>.{json,md}` on the local
  filesystem, atomically, with overwrite protection on by default. It never
  touches the org. It is annotated `readOnlyHint=False` deliberately, so
  clients see the write honestly.
- **No secrets in process memory.** The server uses the user's existing
  `sf org login` session; it never stores or transmits tokens.
- **Errors return structured dicts, not exceptions**, so a stack trace cannot
  carry a token out.
- `tests/test_tool_annotations.py` asserts every tool carries a profile, so a
  new tool cannot ship un-annotated.

Any MCP tool PR that writes to the org, stores credentials, or interpolates
user input into SOQL/DML without these patterns will be rejected.

### Agent execution boundary — convention, partially enforced

`agents/_shared/AGENT_CONTRACT.md` rule 7 states:

> Run-time agents NEVER deploy to an org, NEVER run `sf project deploy`, NEVER
> mutate files outside the paths the user gave as input. They produce plans,
> patches, and reports — execution is the human's call.

**What the validator actually checks:** `pipelines/agent_validators.py`
requires that every `class: runtime` `AGENT.md` contains a
`## What This Agent Does NOT Do` section, in the canonical position relative to
the other seven required sections. It does not read the section's contents and
does not search for the word "deploy" anywhere. Whether a given agent's
non-deploy statement is present and correct is a review question, not a gate.

One related boundary is enforced: `_validate_citations` ERRORs when an
`AGENT.md` cites a `skills/…`, `templates/…`, `standards/…`, probe, agent,
slash-command, or MCP tool path that does not resolve, so an agent cannot ship
instructions pointing at something that does not exist.

### CRUD/FLS and `with sharing` — convention

The house style for Apex content under `skills/apex/` is:

- `with sharing` as the default declaration in examples.
- CRUD/FLS enforced via the `SecurityUtils` template
  (`templates/apex/SecurityUtils.cls`) or `WITH SECURITY_ENFORCED` / `USER_MODE`
  in SOQL.
- Any `without sharing` usage flagged as requiring documentation.

`skills/apex/apex-security-patterns` is the canonical reference. Note that no
validator gate enforces any of the three bullets above — they are review
expectations. If you find an Apex skill that violates them, that is an in-scope
report under item 1.

**The correct strip API.** There is no `stripInaccessibleFields`. The real
method is:

```apex
SObjectAccessDecision decision = Security.stripInaccessible(AccessType.UPDATABLE, records);
update decision.getRecords();
```

DML on the original list is unenforced. `AGENT_CONTRACT.md` lists
`stripInaccessibleFields` among the fabricated Apex identifiers that reached
shipped agents before rule 12 existed; if you see it anywhere in this repo
outside a "this does not exist" warning, that is a bug.

### Guest-user and external-user paths — convention

Skills covering Guest or external Experience Cloud users
(`skills/flow/flow-for-experience-cloud`,
`skills/admin/experience-cloud-guest-access`) treat Guest-user access as a
public-endpoint threat model. Their guidance is authoritative for agents that
encounter Guest contexts.

## Contributor Security Checklist

### Apex skills

- [ ] Every example uses `with sharing`, or documents why not
- [ ] Every SOQL uses `WITH SECURITY_ENFORCED`, `USER_MODE`, or
      `Security.stripInaccessible(...).getRecords()`
- [ ] Every DML is preceded by a `SecurityUtils` CRUD check or equivalent
- [ ] Every Apex identifier is copied from `templates/apex/`, not written from
      memory
- [ ] No credentials, tokens, or org IDs in skill content

### Agents (`agents/*/AGENT.md`)

- [ ] `## What This Agent Does NOT Do` explicitly states the non-deploy
      boundary (the validator checks the heading, not the wording — so this one
      is on you)
- [ ] Refusal rules cite canonical codes from
      `agents/_shared/REFUSAL_CODES.md`
- [ ] The agent does not instruct the model to execute untrusted input as code
- [ ] Refusal conditions are evaluable by the caller. Do not gate a refusal on
      an MCP tool the caller may not have — the plugin manifest
      (`.claude-plugin/plugin.json`) ships skills and commands only and
      declares no `mcpServers`, so a plugin-only install has no MCP tools at
      all.

### MCP tools (`mcp/sfskills-mcp/src/`)

- [ ] All inputs validated via `_validate_api_name` or equivalent
- [ ] No DML in the tool implementation
- [ ] Any raw `sf` output passes through the redactors in `sf_cli.py`
- [ ] Error handling returns structured dicts, not exception stack traces
- [ ] The correct annotation profile is set (`_ANN_REPO_ONLY`,
      `_ANN_ORG_READ`, or `_ANN_ENVELOPE`)
- [ ] A test is added under `mcp/sfskills-mcp/tests/`

### Build scripts (`scripts/`, `pipelines/`)

- [ ] No `eval()`, `exec()`, or `subprocess.run(shell=True)` on user content
- [ ] All file reads/writes scoped to the repo root
- [ ] No network calls without explicit user approval

## Third-Party Dependency Policy

| Where | Pins |
|---|---|
| `requirements.txt` | `PyYAML>=6.0,<7.0`, `jsonschema>=4.0,<5.0`. `fastembed>=0.4,<1.0` is commented out — optional embeddings only. |
| `mcp/sfskills-mcp/pyproject.toml` | `mcp>=1.7.0,<2.0`, `jsonschema>=4.0,<5.0`, `referencing>=0.30,<1.0`. Optional extras: `dev` (pytest, build, twine) and `embeddings` (fastembed). |

The `mcp` spec is bounded on both ends for measured reasons recorded in the
file: `ToolAnnotations` does not import below 1.7.0, and mcp 2.0.0 removed
`mcp.server.fastmcp`, which `server.py` imports. Lifting the ceiling is a port,
not a pin bump.

Skill-local checker scripts under `skills/*/*/scripts/` are stdlib-only.

CI pins Python **3.11** for validation, tests, PR lint, and org validation
(`.github/workflows/validate.yml`, `tests.yml`, `pr-lint.yml`,
`org-validation.yml`). The PyPI publish workflow (`publish-mcp.yml`) uses
**3.12**.

Dependency updates go through standard PR review; Dependabot advisories are
accepted through GitHub's normal flow.

## Responsible Disclosure Timeline

1. Private report received, acknowledged (target: 72 hours).
2. Triage — severity classification and fix plan (target: 7 days).
3. Fix developed and tested privately.
4. Disclosure date agreed with the reporter.
5. Fix released, advisory published.

For a critical issue that is actively exploitable with no workaround we aim for
a 7-day private-fix window; for lower severity, up to 90 days. These are the
targets of a small project, not guarantees.

## Credits

Researchers who report a valid vulnerability will be credited in the published
advisory and, with permission, named here.

No reports have been received to date, so this section is empty.
