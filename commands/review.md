# /review — Code Review Command

Triggers the **code-reviewer** agent.

## Usage

```
/review
```

Then paste your code or reference a file path. The agent identifies the component type and runs a full review.

## What Happens

1. Agent identifies component type (Apex / LWC / Flow / OmniStudio)
2. Loads applicable skills from `skills/[domain]/`
3. Checks security first, then performance, scalability, reliability, code quality
4. Produces findings: Critical → High → Medium → Low
5. Includes remediation code snippets for Critical and High findings
6. Scores each WAF pillar

## Variants

**Targeted review:**
```
/review — focus on security
/review — focus on governor limits
/review — this is a PR diff
```

## Agent

See `agents/code-reviewer/AGENT.md` for full orchestration plan.
