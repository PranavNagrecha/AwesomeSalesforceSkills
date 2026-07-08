# Duplicate Governance Template

Use this before turning on new matching or duplicate rules.

---

## Scope

| Property | Value |
|----------|-------|
| Object | TODO |
| Business owner | TODO |
| Data steward | TODO |
| Main duplicate source | UI / Integration / Import / Mixed |

## Matching Strategy

| Field or signal | Match type | Confidence | Notes |
|-----------------|------------|------------|------|
| TODO | Exact / Fuzzy / Composite | High / Medium / Low | TODO |
| TODO | Exact / Fuzzy / Composite | High / Medium / Low | TODO |

## Rule Behavior

| Operation | Behavior | Rationale |
|-----------|----------|-----------|
| Create | Block / Alert / Allow | TODO |
| Edit | Block / Alert / Allow | TODO |
| Integration / Import | Block / Alert / Pre-process | TODO |
| Bypass sharing rules | Yes / No | TODO — if Yes, alert text must tell the user what to do about a record they cannot see |
| Apex `allowSave` permitted | Yes / No | TODO — which integrations may save through an Alert, and where those saves are logged |

## Limit Budget

Platform ceilings, not preferences. Fill in before adding another rule.

| Constraint | Max | Currently used |
|------------|-----|----------------|
| Active duplicate rules on this object | 5 | TODO |
| Matching rules in this duplicate rule | 3 | TODO |
| Active matching rules per object, in this duplicate rule | 1 | TODO |
| Active matching rules on this object, across all duplicate rules | 5 | TODO |

## Create-Path Coverage

Duplicate rules are a save-path control. Mark each path Covered, Skipped-by-platform, or Controlled-upstream.

| Create path | Status | Upstream control if skipped |
|-------------|--------|-----------------------------|
| UI save | TODO | n/a |
| Quick Create | Skipped by platform | TODO |
| API / Apex / Bulk API | TODO | External ID + idempotent upsert |
| Community Self-Registration | Skipped by platform | TODO |
| Lightning Sync | Skipped by platform | TODO |
| Einstein Activity Capture | Skipped by platform | TODO |
| Manual merge | Skipped by platform | TODO |
| Undelete | Skipped by platform | TODO |
| Lead conversion (without Apex Lead Convert) | Skipped by platform | TODO |

## Field-Level Access Dependency

Every field a matching rule references must be readable by the users who create or edit the object, or detection silently fails for them.

| Matching-rule field | Profiles / permission sets verified |
|---------------------|-------------------------------------|
| TODO | TODO |

## Survivorship and Merge Rules

| Item | Decision |
|------|----------|
| Master record selection | TODO |
| Field-level survivorship | TODO |
| Related record handling | TODO |
| Exception path | TODO |

## Metrics

- Duplicate alerts per week: TODO
- Merges completed per week: TODO
- False positives sampled: TODO
- Recurrent duplicate source: TODO
