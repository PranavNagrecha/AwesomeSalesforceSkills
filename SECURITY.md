# Security Policy

SfSkills is a Salesforce skill + agent framework consumed by AI coding assistants (Claude Code, Cursor, Windsurf, Aider, Augment, raw MCP clients). This document describes how to report security issues and the security posture the project enforces.

## Reporting a Vulnerability

**Do NOT open a public GitHub issue for a security vulnerability.** Public disclosure before a fix gives attackers a window between disclosure and deployment.

Instead:

- **Preferred:** open a [private security advisory](https://github.com/PranavNagrecha/AwesomeSalesforceSkills/security/advisories/new) on GitHub. This lets us coordinate a fix privately and credit you on disclosure.
- **Alternative:** email the maintainer directly (contact in the README or git commit history). Include the word `SECURITY` in the subject line.

We will acknowledge within 72 hours, triage within 7 days, and coordinate a disclosure timeline with you based on severity.

## What Counts As A Vulnerability Here

This project is content + tooling, not a running service. The threat model is:

### In scope

1. **Skills that recommend insecure Salesforce patterns.**
   - e.g. a skill that says "use `WITHOUT SHARING` without documentation" without a counter-example or WAF-Security tag.
   - e.g. a skill that recommends storing OAuth credentials in Custom Settings.
2. **Agents that bypass CRUD/FLS or bypass `with sharing` defaults without justification.**
   - e.g. a run-time agent's Plan that says "use `Database.query` with a user-supplied string" without parameterization guidance.
3. **MCP tool implementations that enable SOQL injection or bypass the `sf` CLI's auth boundary.**
   - e.g. a probe that concatenates user input into SOQL without the API-name pattern check used in `admin.py`.
4. **Validators or pipelines that execute user-supplied strings as code.**
   - e.g. `eval()` on content pulled from a skill file.
5. **Build-time scripts that upload data outside the local repo without explicit user consent.**
6. **Dependency vulnerabilities** in the Python packages we ship in `requirements.txt` (PyYAML, jsonschema, mcp).

### Out of scope (but still welcomed as bugs)

- Insecure Salesforce patterns mentioned ONLY as anti-patterns in `references/llm-anti-patterns.md` or gotchas.
- Misconfiguration of a consumer's own Salesforce org (we don't control their setup).
- Speculation about future platform changes that might affect a skill's correctness.
- Spelling or style issues in skill content.

For the out-of-scope items, please open a normal issue or PR.

## Security Posture Of The Framework

### CRUD/FLS And `with sharing` Enforcement

Every Apex skill in this repo (under `skills/apex/`) is required to:
- Reference `with sharing` as the default declaration in examples.
- Enforce CRUD/FLS via `SecurityUtils` template (`templates/apex/SecurityUtils.cls`) or `WITH SECURITY_ENFORCED` / `USER_MODE` in SOQL.
- Flag any `WITHOUT SHARING` usage as requiring documentation.

The `skills/apex/apex-security-patterns` skill is the canonical reference. Every Apex skill links to it or its equivalents.

### MCP Tool Security Surface

The SfSkills MCP server (`mcp/sfskills-mcp/`) exposes 19 tools that can query the user's Salesforce org via the `sf` CLI. Security discipline:

1. **No secrets in process memory.** The server uses the user's existing `sf org login` credentials; it never stores, transmits, or logs tokens.
2. **All tool inputs validated.** API names match `^[A-Za-z0-9_]+$` via `admin._validate_api_name()`. SOQL in `tooling_query` rejects DML keywords and semicolons.
3. **Read-only by contract.** No MCP tool writes to the org. The `validate_against_org` and probe tools issue SOQL only.
4. **Errors return structured dicts, not exceptions.** Prevents token leaks through stack traces.

Any MCP tool PR that writes to the org, stores credentials, or concatenates user input into SOQL/DML without the standard validation patterns will be rejected.

### Agent Execution Boundary

Run-time agents never execute writes on the user's org. Every `AGENT.md` that does CRUD/DML only PRODUCES metadata patches — the human deploys them. This is documented in `agents/_shared/AGENT_CONTRACT.md`:

> Run-time agents NEVER deploy to an org, NEVER run `sf project deploy`, NEVER mutate files outside the paths the user gave as input.

The validator enforces that every `class: runtime` `AGENT.md` has a "What This Agent Does NOT Do" section explicitly stating non-deploy behavior.

### Guest-User / External-User Paths

Skills that cover Guest or external Experience Cloud users (e.g. `flow/flow-for-experience-cloud`, `admin/experience-cloud-guest-access`) treat Guest-user access as a public-endpoint threat model. Security guidance in those skills is authoritative for agents that encounter Guest contexts.

## Contributor Security Checklist

Before submitting a PR that touches:

### Apex skills
- [ ] Every example uses `with sharing` (or documents why not)
- [ ] Every SOQL uses `WITH SECURITY_ENFORCED` or `USER_MODE` or `stripInaccessibleFields`
- [ ] Every DML is preceded by a `SecurityUtils` CRUD check or equivalent
- [ ] No credentials, tokens, or org IDs in skill content

### Agents (`agents/*/AGENT.md`)
- [ ] "What This Agent Does NOT Do" section explicitly states non-deploy behavior
- [ ] Refusal rules reference canonical codes from `REFUSAL_CODES.md`
- [ ] Agent does not instruct the LLM to execute untrusted input as code

### MCP tools (`mcp/sfskills-mcp/src/`)
- [ ] All inputs validated via `_validate_api_name` or equivalent
- [ ] No DML in the tool implementation (except `validate_against_org`'s specific documented write-adjacent checks)
- [ ] Error handling returns structured dicts, not exception stack traces
- [ ] No secrets or tokens in tool output

### Build scripts (`scripts/`, `pipelines/`)
- [ ] No `eval()`, `exec()`, or `subprocess.run(shell=True)` on user content
- [ ] All file reads/writes scoped to the repo root
- [ ] No external network calls without explicit user approval

## Third-Party Dependency Policy

- **`requirements.txt`** dependencies pinned to major versions: `PyYAML>=6.0,<7.0`, `jsonschema>=4.0,<5.0`.
- **MCP server** depends on `mcp>=1.2.0` (Anthropic's MCP SDK).
- No other runtime Python dependencies. Stdlib-only is the default for skill-local checker scripts.
- CI pins Python to 3.11; incompatible versions fail the build.

Dependency updates go through standard PR review. Dependency security advisories (Dependabot, etc.) are accepted via GitHub's standard flow.

## Responsible Disclosure Timeline

1. Private report received → acknowledged within 72 hours.
2. Triage → within 7 days (severity classification + fix plan).
3. Fix developed + tested privately.
4. Coordinated disclosure date agreed with reporter.
5. Fix released + advisory published.

For critical vulnerabilities (actively exploited, no workaround), we aim for a 7-day private-fix window before public disclosure. For lower severity, up to 90 days.

## Credits And Hall Of Fame

Security researchers who report valid vulnerabilities will be credited in the published advisory and (with permission) in a HALL-OF-FAME section of this document.

This section is blank today — we hope to add names responsibly.
