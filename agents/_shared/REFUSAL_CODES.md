# Refusal Codes

Every agent's Escalation / Refusal Rules section describes *when* it stops and asks a human. The `refusal.code` in the structured output envelope uses the canonical enum below so tooling can aggregate refusal reasons across runs.

New codes MAY be added via PR. Codes are never renamed after release — retire and replace instead.

## Canonical codes

| Code | Applies to | Meaning |
|---|---|---|
| `REFUSAL_MISSING_ORG` | Any agent where `requires_org: true` | No `target_org_alias` supplied; agent cannot ground recommendations. |
| `REFUSAL_ORG_UNREACHABLE` | Any agent | Org alias supplied but `describe_org` failed / auth expired. |
| `REFUSAL_MISSING_INPUT` | Any agent | A required input was not supplied and no sensible default exists. Message names the input. |
| `REFUSAL_INPUT_AMBIGUOUS` | Any agent | Inputs present but contradict each other or are too vague to act on. |
| `REFUSAL_FIELD_NOT_FOUND` | Field-centric agents | The named field does not exist on the target object in the target org. |
| `REFUSAL_OBJECT_NOT_FOUND` | Object-centric agents | The named sObject does not exist or is not accessible. |
| `REFUSAL_MANAGED_PACKAGE` | Admin / data / metadata agents | The target artifact lives in a managed-package namespace; the agent refuses to propose rename/delete/deploy changes. |
| `REFUSAL_STANDARD_SYSTEM_FIELD` | Field-centric agents | The target is a standard system field (`Id`, `Name`, `OwnerId`, `CreatedDate`, etc.) that cannot be renamed or deleted. |
| `REFUSAL_OUT_OF_SCOPE` | Any agent | The request falls outside the agent's declared scope; the agent recommends a different agent. |
| `REFUSAL_COMPETING_ARTIFACT` | Design agents | A similar active artifact already exists (e.g. competing duplicate rule, overlapping matching rule). Agent refuses to design a competitor. |
| `REFUSAL_OVER_SCOPE_LIMIT` | Probing agents | Target scope exceeds the probe's safe upper bound (e.g. `>100 referencing Apex classes`, `>2000 PSes`). Returns partial results + recommendation. |
| `REFUSAL_POLICY_MISMATCH` | Design agents | Requested policy is incompatible with platform behavior (e.g. "block on Lead Convert via duplicate rule" — dup rules do not fire on Convert). |
| `REFUSAL_DATA_QUALITY_UNSAFE` | Data agents | Proposed operation would operate on data whose quality makes it unsafe (e.g. fuzzy match on free-text at >100k rows). |
| `REFUSAL_FEATURE_DISABLED` | Feature-specific agents | The relevant feature is not enabled in the target org (e.g. Knowledge, Omni-Channel, Person Accounts). |
| `REFUSAL_SECURITY_GUARD` | Security-adjacent agents | The agent will not propose the requested artifact because it would grant a security-sensitive permission (e.g. `Modify All Data` on a persona PSG). |
| `REFUSAL_NEEDS_HUMAN_REVIEW` | Any agent | Agent hit a condition that explicitly requires human judgment (contradictory skills, unresolved policy question). |

## Usage in output envelope

When an agent refuses, it emits:

```json
{
  "agent": "field-impact-analyzer",
  "mode": "single",
  "summary": "Refused: field Industry__c not found on Account in org `uat`.",
  "confidence": "LOW",
  "refusal": {
    "code": "REFUSAL_FIELD_NOT_FOUND",
    "message": "FieldDefinition query returned zero rows for Account.Industry__c.",
    "remediation_hint": "Verify the field API name and org alias, then re-run."
  },
  "process_observations": [],
  "citations": []
}
```

When `refusal` is set, the other deliverable fields (`findings`, `deliverables`) MAY be absent.

## Adding a new code

1. Add a row to the table above. Keep the prefix `REFUSAL_` and stay ALL_CAPS.
2. Add the code to the enum in `schemas/output-envelope.schema.json` if the validator is wired to enforce it (currently validator treats the code field as free-form string to avoid churn when new codes are added mid-release).
3. Reference the code in the citing AGENT.md under Escalation / Refusal Rules.
