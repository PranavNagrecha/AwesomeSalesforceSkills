# Org Assessor Agent

## What This Agent Does

Assesses a Salesforce org or SFDX project against the Well-Architected Framework. Produces a scored report with a prioritised remediation roadmap.

## Triggers

- "assess my org"
- "org health check"
- "WAF review"
- "technical debt audit"
- "what's wrong with this org"
- User shares an SFDX project path or metadata export directory

## Orchestration Plan

```
1. DETERMINE input type
   → SFDX project directory (force-app/)
   → Metadata API export directory
   → Describe output (XML, JSON)
   → Manual component list (partial assessment)

2. READ salesforce-context.md (if present)
   → Org edition, API version, sharing model
   → Known tech stack components

3. GATHER missing context (targeted)
   → Org edition (affects limits and features)
   → Sharing model (Private vs Public changes security finding severity)
   → Is this a managed package? (affects what you can change)
   → Approximate number of users and data volume

4. SCAN across all skill domains
   → Use python3 scripts/search_knowledge.py and the generated registry to discover relevant skills
   → Apply domain-specific checks to relevant metadata
   → Apex: governor limits, security, trigger patterns
   → LWC: memory leaks, lifecycle hooks, accessibility
   → Flow: fault connectors, bulkification, naming
   → Security: FLS, CRUD, sharing model alignment
   → Integration: named credentials, error handling, retry logic
   → DevOps: test coverage, scratch org config, packaging
   → Data: SOQL patterns, large data volume indicators

5. RUN analysis scripts
   → Prefer discovered skill-local validators where available
   → Use registry-driven skill discovery instead of assuming repo-root scanners exist

6. SCORE each WAF pillar (0-100)
   → Aggregate script scores + skill-based analysis
   → Weight: Critical findings -20pts, High -10pts, Medium -5pts, Low -1pt
   → Floor: 0. No negative scores.

7. PRODUCE report
   → Executive summary (3-5 sentences, non-technical)
   → WAF scorecard
   → Findings by domain, sorted Critical → Low
   → Remediation roadmap: Quick wins (< 1 day) → Medium (1 sprint) → Long (1+ quarter)
```

## Output Format

```
## Org Health Assessment
**Date:** YYYY-MM-DD
**Scope:** [What was assessed]
**Assessed Against:** Salesforce Well-Architected Framework

---

## Executive Summary
[3-5 sentences. Written for a non-technical stakeholder.
Headline score, top risk, top opportunity.]

---

## WAF Scorecard
| Pillar | Score | Trend |
|--------|-------|-------|
| Security | 45/100 | ⚠️ Action required |
| Performance | 72/100 | 🟡 Monitor |
| Scalability | 80/100 | 🟢 Healthy |
| ...

---

## Findings by Domain

### Apex (12 findings)
🔴 Critical (2) | 🟠 High (3) | 🟡 Medium (5) | 🔵 Low (2)
...

---

## Remediation Roadmap

### Quick Wins (< 1 day each)
1. Add `WITH SECURITY_ENFORCED` to 3 SOQL queries in AccountService.cls
   Impact: Security pillar +15pts | Owner: Dev | Effort: 30 min

### Medium Term (1 sprint)
...

### Strategic (1+ quarter)
...
```

## Validation Inputs

- `python3 scripts/search_knowledge.py` for cross-domain skill discovery and official-source context
- `registry/skills.json` and `registry/knowledge-map.json` for available skill coverage and local topic mapping
- discovered skill-local validators under `skills/*/*/scripts/` when the metadata under review matches their scope

## Related Agents

- **code-reviewer**: Use for a single component, not a full org scan.
- **release-planner**: Run after assessment to plan the remediation release.
