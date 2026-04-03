# /assess-org — Org Health Assessment Command

Triggers the **org-assessor** agent.

## Usage

```
/assess-org
```

Point the agent at an SFDX project directory or metadata export. Get a WAF-scored report.

## What Happens

1. Agent determines input type (SFDX project / metadata export / component list)
2. Reads `salesforce-context.md` if present
3. Scans metadata across all applicable skill domains
4. Runs analysis scripts where available
5. Scores each WAF pillar (0-100)
6. Produces:
   - Executive summary (non-technical, stakeholder-ready)
   - WAF scorecard
   - Findings by domain (Critical → Low)
   - Prioritised remediation roadmap

## Variants

**Targeted assessment:**
```
/assess-org — apex security only
/assess-org — flows only
/assess-org — pre-upgrade readiness for API v63
```

## Input Options

| Input Type | Example |
|-----------|---------|
| SFDX project | `force-app/` directory |
| Metadata export | Unzipped package.xml retrieve |
| Component list | List of class names, flow names, etc. |

## Agent

See `agents/org-assessor/AGENT.md` for full orchestration plan.
