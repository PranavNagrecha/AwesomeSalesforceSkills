# /release-notes — Release Notes Command

Triggers the **release-planner** agent.

## Usage

```
/release-notes
```

Feed in a git diff, component list, or sprint description. Get structured release notes with risk flags and a deployment checklist.

## What Happens

1. Agent parses input (git diff / component list / PR list / free text)
2. Classifies each change by type and risk
3. Applies automatic risk flags (sharing changes, trigger modifications, etc.)
4. Produces:
   - Executive summary (stakeholder-ready, non-technical)
   - Changes by type with risk classification
   - Breaking change flags
   - Deployment checklist (pre/during/post)
   - Rollback plan for Critical-risk items

## Variants

**Specific outputs:**
```
/release-notes — risk assessment only
/release-notes — deployment checklist only
/release-notes — stakeholder summary only
```

## Risk Flag Reference

| Change Type | Default Risk |
|-------------|-------------|
| Sharing rule change | 🔴 Critical |
| Permission set change | 🟠 High |
| Trigger modification | 🟠 High |
| New Flow | 🟡 Medium |
| New Apex class | 🟢 Low |

## Agent

See `agents/release-planner/AGENT.md` for full orchestration plan.
