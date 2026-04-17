# Agent Smoke Test — `omni-channel-routing-designer`

**Date:** 2026-04-17
**Status:** ✅ PASS
**Agent version:** `1.1.0`
**Class:** `runtime`
**Modes:** ``
**Requires org:** `true`

## TL;DR for humans

Agent `omni-channel-routing-designer` passed all structural + dependency checks. Its declared dependencies exist, its slash-command exists, and its frontmatter is schema-valid.

## What the smoke test did

- Parsed `agents/omni-channel-routing-designer/AGENT.md`
- Ran 6 structural checks against a live-org context (`sfskills-dev`)
- No tool calls issued against the org beyond what probe validation already covered

## Check results

| Check | Status | Detail |
|---|---|---|
| Required sections present + in order | ✅ | (none) |
| Citations resolve to real files | ✅ | (none) |
| Dependencies cover all citations | ✅ | (none) |
| Slash-command coverage | ✅ | covered by /design-omni-channel |
| Inputs schema valid JSON (if present) | ✅ | (none) |
| Declared probes executable | ✅ | (none) |

## Machine-readable result

```json
{
  "agent": "omni-channel-routing-designer",
  "date": "2026-04-17",
  "overall_pass": true,
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
      "pass": true,
      "soft": false,
      "messages": []
    },
    {
      "name": "Slash-command coverage",
      "pass": true,
      "soft": false,
      "messages": [
        "covered by /design-omni-channel"
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

- [ ] Does the TL;DR match the actual behavior of `omni-channel-routing-designer` in production?
- [ ] Are any of the warnings actually critical in your environment?
- [ ] Do the declared dependencies cover everything the agent actually needs?
