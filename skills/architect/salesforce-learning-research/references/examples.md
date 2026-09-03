# Worked Research Examples

## Example: LWC TypeScript support

The research packet separates four claims that are easy to collapse:

1. TypeScript authoring support exists for current LWC tooling.
2. The supported source-to-deployment path depends on the installed Salesforce tooling, project configuration, target API/release, and chosen migration strategy.
3. Lightning base-component types are supplied by a named package.
4. A particular project is configured for native TypeScript handling or for an explicit TypeScript-to-JavaScript build step.

The first and third claims can be verified from current official documentation. The second requires version-scoped official evidence, and the fourth is project evidence that remains unknown until `sfdx-project.json`, `tsconfig.json`, package scripts, generated output, and a target validation are inspected.

## Example: feature availability

An official developer blog describes a feature introduced in Spring '26. A help article describes activation steps but does not state edition availability. Record behavior and activation separately; do not infer that every target org is entitled.

## Example: supplied-source boundary

The user asks to summarize an attached implementation guide only. Record `source boundary: supplied sources only`. When the guide omits licensing, say the source does not support a licensing conclusion. Do not silently browse and blend external facts into the source-derived summary.

## Example: community workaround

A Stack Exchange answer suggests a workaround not described in official docs. Record it as lower-tier practitioner guidance, identify the official behavior it addresses, and teach it only with a caveat. If the answer conflicts with current official behavior, exclude or explicitly correct it.

## Example: atomic claim-ledger fragment

```json
{
  "claim_id": "CLM-004",
  "claim": "The selected project deploys raw LWC TypeScript source.",
  "state": "unknown",
  "source_boundary": "official-salesforce",
  "applicability": {
    "salesforce_release": "Summer '26",
    "cli_version": "unverified",
    "extensions_version": "unverified",
    "project": "target project"
  },
  "evidence": [],
  "gap": "Inspect generated project configuration and validate deployment in a scratch org."
}
```

This keeps a platform-wide documentation claim separate from a project-specific deployment conclusion.
