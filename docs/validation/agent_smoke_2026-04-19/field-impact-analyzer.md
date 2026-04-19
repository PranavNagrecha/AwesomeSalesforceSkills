# Agent Smoke Test — `field-impact-analyzer`

**Date:** 2026-04-19
**Status:** ❌ FAIL
**Agent version:** `1.0.0`
**Class:** `runtime`
**Modes:** ``
**Requires org:** `true`

## TL;DR for humans

Agent `field-impact-analyzer` has **1** structural / dependency issue(s). See details below.

## What the smoke test did

- Parsed `agents/field-impact-analyzer/AGENT.md`
- Ran 6 structural checks against a live-org context (`sfskills-dev`)
- No tool calls issued against the org beyond what probe validation already covered

## Check results

| Check | Status | Detail |
|---|---|---|
| Required sections present + in order | ✅ | (none) |
| Citations resolve to real files | ✅ | (none) |
| Dependencies cover all citations | ❌ | probe cited but not declared in dependencies: apex-references-to-field.md |
| Slash-command coverage | ✅ | covered by /analyze-field-impact |
| Inputs schema valid JSON (if present) | ✅ | (none) |
| Declared probes executable | ✅ | (none) |

## Machine-readable result

```json
{
  "agent": "field-impact-analyzer",
  "date": "2026-04-19",
  "overall_pass": false,
  "any_soft": false,
  "checks": [
    {
      "name": "Required sections present + in order",
      "pass": true,
      "soft": false,
      "messages": []
    },
    {
      "name": "Citations resolve to real files",
      "pass": true,
      "soft": false,
      "messages": []
    },
    {
      "name": "Dependencies cover all citations",
      "pass": false,
      "soft": false,
      "messages": [
        "probe cited but not declared in dependencies: apex-references-to-field.md"
      ]
    },
    {
      "name": "Slash-command coverage",
      "pass": true,
      "soft": false,
      "messages": [
        "covered by /analyze-field-impact"
      ]
    },
    {
      "name": "Inputs schema valid JSON (if present)",
      "pass": true,
      "soft": false,
      "messages": []
    },
    {
      "name": "Declared probes executable",
      "pass": true,
      "soft": false,
      "messages": []
    }
  ]
}
```

## What a human reviewer should check

- [ ] Does the TL;DR match the actual behavior of `field-impact-analyzer` in production?
- [ ] Are any of the warnings actually critical in your environment?
- [ ] Do the declared dependencies cover everything the agent actually needs?
