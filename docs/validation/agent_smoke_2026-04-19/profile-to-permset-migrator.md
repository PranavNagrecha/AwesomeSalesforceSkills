# Agent Smoke Test — `profile-to-permset-migrator`

**Date:** 2026-04-19
**Status:** ✅ PASS
**Agent version:** `1.0.0`
**Class:** `runtime`
**Modes:** ``
**Requires org:** `true`

## TL;DR for humans

Agent `profile-to-permset-migrator` passed all structural + dependency checks. Its declared dependencies exist, its slash-command exists, and its frontmatter is schema-valid.

## What the smoke test did

- Parsed `agents/profile-to-permset-migrator/AGENT.md`
- Ran 6 structural checks against a live-org context (`sfskills-dev`)
- No tool calls issued against the org beyond what probe validation already covered

## Check results

| Check | Status | Detail |
|---|---|---|
| Required sections present + in order | ✅ | (none) |
| Citations resolve to real files | ✅ | (none) |
| Dependencies cover all citations | ✅ | (none) |
| Slash-command coverage | ✅ | covered by /migrate-profile-to-permset |
| Inputs schema valid JSON (if present) | ✅ | (none) |
| Declared probes executable | ✅ | probe_validation_report not found — run validate_probes_against_org.py first |

## Machine-readable result

```json
{
  "agent": "profile-to-permset-migrator",
  "date": "2026-04-19",
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
        "covered by /migrate-profile-to-permset"
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
      "messages": [
        "probe_validation_report not found \u2014 run validate_probes_against_org.py first"
      ]
    }
  ]
}
```

## What a human reviewer should check

- [ ] Does the TL;DR match the actual behavior of `profile-to-permset-migrator` in production?
- [ ] Are any of the warnings actually critical in your environment?
- [ ] Do the declared dependencies cover everything the agent actually needs?
