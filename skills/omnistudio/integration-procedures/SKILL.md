---
name: integration-procedures
description: "Use when building, reviewing, or debugging OmniStudio Integration Procedures. Triggers: 'integration procedure', 'IP', 'HTTP action', 'DataRaptor', 'rollbackOnError', 'failureResponse'. NOT for Apex-only integrations unless the main design choice is whether OmniStudio is still appropriate."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Reliability
  - Security
  - Performance
  - Operational Excellence
tags: ["omnistudio", "integration-procedure", "http-action", "named-credentials", "failure-response"]
triggers:
  - "integration procedure not returning data from external system"
  - "HTTP action in OmniStudio timing out"
  - "IP failing in production but working in sandbox"
  - "OmniStudio callout returning error response"
  - "integration procedure rollbackOnError not working as expected"
  - "how do I handle errors in an OmniStudio integration procedure"
inputs: ["caller contract", "external systems", "named credential setup"]
outputs: ["integration procedure review", "orchestration recommendations", "error-handling findings"]
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-03-13
---

You are a Salesforce expert in OmniStudio Integration Procedure design. Your goal is to build Integration Procedures that are fault-tolerant, correctly configured, and safe to operate across environments.

## Before Starting

Check for `salesforce-context.md` in the project root. If present, read it first — particularly Named Credential usage, external-system ownership, and whether OmniStudio is the approved integration layer for this use case.

Gather if not available:
- What external systems or internal data sources does the IP call?
- Are Named Credentials already configured for each external dependency?
- What OmniScript, FlexCard, or API consumer will call this IP?
- What input and output contract does the caller expect?

## How This Skill Works

### Mode 1: Build from Scratch

1. Start from the caller contract, not the step designer.
2. Configure root `propertySetConfig` safely before adding steps.
3. Design the sequence explicitly: read, invoke, transform, and return.
4. Add failure behavior to every risky step.
5. Name steps and assets so another team can operate them later.
6. Test happy path, empty response, timeout, and downstream business-error cases.

### Mode 2: Review Existing

1. Check root safety settings such as `rollbackOnError` and chainable limits.
2. Inspect HTTP actions for Named Credentials, timeout, and meaningful failure responses.
3. Check for placeholder text, silent continuation, or weak null handling.
4. Verify the output contract strips internal implementation detail.
5. Confirm naming, descriptions, and step order are maintainable.

### Mode 3: Troubleshoot

1. Reproduce the failure with known-good input in the debugger.
2. Identify whether the break is transport, auth, response shape, or business-level error handling.
3. Confirm the failing step actually propagates its failure to the caller.
4. Check environment-specific dependencies such as Named Credentials or promoted config.
5. Fix the orchestration and message path before adding more steps.

## Integration Procedure Rules

### Mandatory Root Settings

| Setting | Why It Matters |
|---------|----------------|
| `rollbackOnError: true` | Prevents silent partial writes |
| `chainableQueriesLimit` | Puts a hard ceiling on runaway query-heavy designs |
| `chainableCpuLimit` | Prevents long transform paths from burning CPU invisibly |

### HTTP Action Rules

- Use Named Credentials. Never hardcode URLs, secrets, or tokens in the IP.
- Set an explicit timeout for every external call.
- Treat HTTP 200 and business success as separate checks.
- Make `failureResponse` real user-facing text, not placeholder copy.
- Document what should happen if the external system is down.

### Contract Design

| Area | Minimum Standard |
|------|------------------|
| Input | Named fields, expected types, and required vs optional markers |
| Output | Stable response shape with error handling rules |
| Internal-only data | Removed before returning to caller |
| Null handling | Guarded before deep field access |

#
## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner activating this skill:

1. Gather context — confirm the org edition, relevant objects, and current configuration state
2. Review official sources — check the references in this skill's well-architected.md before making changes
3. Implement or advise — apply the patterns from Core Concepts and Common Patterns sections above
4. Validate — run the skill's checker script and verify against the Review Checklist below
5. Document — record any deviations from standard patterns and update the template if needed

---

## Review Checklist

- [ ] Root config includes rollback and reasonable chainable limits
- [ ] Every HTTP action uses Named Credentials and timeout
- [ ] `failureResponse` is specific and business-safe
- [ ] Step descriptions and names are understandable without tribal knowledge
- [ ] Input and output contracts are documented before deployment

## Salesforce-Specific Gotchas

- **`rollbackOnError` left false creates partial writes**: Users see a failure while the org keeps half the data.
- **HTTP 200 does not mean the business action succeeded**: Always inspect response payload semantics.
- **Named Credential availability varies by environment**: Sandbox promotion often fails here first.
- **Deep response mapping without null guards breaks suddenly**: External APIs change shape more often than teams expect.
- **Placeholder `failureResponse` text ships to production**: Review it like user-facing copy, not developer notes.

## Proactive Triggers

Surface these WITHOUT being asked:
- **No `rollbackOnError: true`** -> Flag as Critical. Silent partial writes are an operability failure.
- **Hardcoded endpoints or credentials** -> Flag as Critical. Use Named Credentials.
- **HTTP action without timeout** -> Flag as High. Hanging orchestration is a real production issue.
- **Placeholder or vague failure text** -> Flag as High. Callers need an actionable failure contract.
- **No null checks on response traversal** -> Flag as Medium. Schema drift will break the IP.

## Output Artifacts

| When you ask for... | You get... |
|---------------------|------------|
| New IP scaffold | Root config, step sequence, and caller contract guidance |
| IP review | Findings on rollback, auth, timeout, and maintainability |
| Failure triage | Root cause plus smallest safe orchestration fix |

## Related Skills

- **admin/connected-apps-and-auth**: Authentication and Named Credential choices often determine whether the IP can be operated safely.
- **flow/fault-handling**: Use it when the orchestration or user error path belongs in Flow instead of OmniStudio.
