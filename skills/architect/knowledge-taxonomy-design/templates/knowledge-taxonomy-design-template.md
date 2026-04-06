# Knowledge Taxonomy Design — Work Template

Use this template when designing or restructuring a Salesforce Knowledge taxonomy.

## Scope

**Skill:** `knowledge-taxonomy-design`

**Request summary:** (fill in what the user asked for — e.g., "Design a Knowledge taxonomy for a 3-product SaaS org migrating from a legacy KM system")

---

## Context Gathered

Answers to the Before Starting questions from SKILL.md:

- **Distinct products / business units requiring separate article sets:**
- **Current article count and growth rate:**
- **Agent populations (authors vs consumers):**
- **Channel surfaces (Service Console / Experience Cloud / Agentforce RAG):**
- **Existing content governance process:**
- **Validation Status requirement (none / simple approval / full KCS):**

---

## Taxonomy Design

### Data Category Groups

| Group Name | Classification Dimension | Level 1 Examples | Level 2 Examples | Level 3 (if needed) | Justification |
|---|---|---|---|---|---|
| (e.g., Products) | (e.g., Product family) | (e.g., Cloud CRM, Cloud ERP) | (e.g., Case Mgmt, Knowledge) | (leave blank if not needed) | (e.g., >500 articles per product) |
| (e.g., Article Types) | (e.g., Topic type) | (e.g., How-To, Troubleshoot) | (n/a — flat) | n/a | (e.g., topic type is independent of product) |

**Active groups total:** __ / 3 default limit
**Limit increase required:** yes / no — (if yes, note support case status)

### Category Count Check

| Group | Total Categories | Within 100-category limit? |
|---|---|---|
| (Group 1 name) | | yes / no |
| (Group 2 name) | | yes / no |

---

## Article Lifecycle Design

### Publication Status Workflow

```
Draft → Published → Archived
  ↑         ↓
  └─────────┘  (Archived can be restored to Draft)
```

**Who can publish (role/profile):** (e.g., Knowledge Authors + Agents with Manage Articles permission set)
**Who can archive:** (e.g., Knowledge Admin only)
**Bulk archive review cadence:** (e.g., quarterly review of articles not viewed in 180 days)

### Validation Status Design

**Validation Status enabled:** yes / no

| Status Value | Meaning | Who Sets It | Publish Allowed? |
|---|---|---|---|
| Not Validated | Default for new articles | System (default) | (yes/no — per policy) |
| Work In Progress | Agent-created, Solve Loop | Agent | yes |
| Validated | Expert-reviewed, canonical | Domain Expert | yes |
| (custom value if needed) | | | |

**Picklist finalised before production enablement:** yes / no

---

## KCS Implementation Plan (if applicable)

**KCS level:** Solve Loop only / Solve + Evolve Loop

### Solve Loop (agent creation during case work)

- Agent permission to publish: granted via (profile / permission set)
- Trigger for article creation: (e.g., agent searches and gets zero results; prompted via Flow)
- Default Validation Status on agent-created articles: Work In Progress
- Case-to-article link: (e.g., Case.Knowledge__c junction, or manual related list)

### Evolve Loop (expert review)

- Review queue filter: Validation Status = Work In Progress
- Review cadence: (e.g., weekly, every Monday)
- Reviewer role: (e.g., Product SME, Senior Support Engineer)
- Escalation path if article cannot be improved: (e.g., archive, assign to Knowledge Admin)

---

## Content Gap Analysis

**Search Activity Gaps baseline date:** (date of first export)
**Export cadence:** (e.g., weekly every Friday)
**Storage location:** (e.g., shared Google Sheet, Confluence page)

| Gap Term | First Seen | Article Created? | Article Published Date | Status |
|---|---|---|---|---|
| (e.g., "reset MFA") | (date) | yes / no | (date) | Open / Closed |

**Month-over-month gap closure target:** __ % reduction per month

---

## Migration Sequence (for restructuring existing taxonomies)

| Step | Action | Owner | Completion Criteria |
|---|---|---|---|
| 1 | Create new Data Category Groups and category tree in Setup | Knowledge Admin | Groups visible in Setup |
| 2 | Export article-to-category mapping from current state (Data Loader) | Knowledge Admin | CSV exported and validated |
| 3 | Map old categories to new categories (transformation spreadsheet) | Architect | Every old leaf maps to a new leaf |
| 4 | Load new DataCategorySelection records via Data Loader | Knowledge Admin | All articles re-assigned |
| 5 | Verify visibility for affected profiles (test user per profile) | QA | All test users see expected articles |
| 6 | Archive old Data Category Group (deactivate, do not delete) | Knowledge Admin | Group deactivated; no user impact |
| 7 | Monitor Search Activity Gaps for 30 days post-migration | Knowledge Owner | Gap list stable or shrinking |

---

## Review Checklist

Copy from SKILL.md and tick as completed:

- [ ] Total active Data Category Groups ≤ 3 (or limit increase approved)
- [ ] No Data Category Group exceeds 5 hierarchy levels or 100 categories
- [ ] Each article type's field set documented and matches audience information need
- [ ] Validation Status picklist values defined and mapped to roles before enablement
- [ ] KCS Solve Loop process documented and communicated to agent population
- [ ] Search Activity Gaps dashboard accessible and baseline gap list captured
- [ ] Article migration / re-categorisation sequence planned with rollback approach

---

## Notes

(Record any deviations from the standard pattern and the rationale for each deviation.)
