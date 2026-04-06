---
name: knowledge-base-administration
description: "Use this skill when setting up, configuring, or managing Salesforce Lightning Knowledge — including enabling the feature, designing record types on Knowledge__kav, configuring Data Categories for organization and visibility control, setting up publishing workflows, and layering approval processes. Trigger keywords: Lightning Knowledge setup, Knowledge article record types, Data Category visibility, Knowledge publishing workflow, Knowledge__kav configuration. NOT for Knowledge in Experience Cloud (use the experience-cloud-knowledge skill), NOT for Einstein Article Recommendations surfacing (use einstein-article-recommendations skill), NOT for Knowledge search tuning or Apex programmatic article management."
category: admin
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Security
  - Operational Excellence
  - Reliability
triggers:
  - "How do I set up Lightning Knowledge in a new Salesforce org?"
  - "Knowledge article record types are not showing the right fields to different user groups"
  - "How do Data Categories control who can see Knowledge articles, and how do I configure visibility by role?"
tags:
  - knowledge
  - lightning-knowledge
  - data-categories
  - knowledge-base
  - publishing-workflow
  - record-types
inputs:
  - "Confirmation that Lightning Knowledge is enabled (or the intent to enable it — irreversible decision)"
  - "List of article types or content categories needed (e.g., FAQ, How-To, Known Issue)"
  - "Audience segments requiring different article visibility (internal agents, partners, customers)"
  - "Approval or review process requirements before articles can be published"
outputs:
  - "Lightning Knowledge configuration plan with record type layout per audience"
  - "Data Category Group structure with role/profile/permission-set visibility assignments"
  - "Publishing workflow decision: native statuses only vs. Validation Status picklist vs. full approval process"
  - "Review checklist confirming the Knowledge setup is production-ready"
dependencies: []
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-06
---

# Knowledge Base Administration

This skill activates when an admin or architect needs to set up or manage Salesforce Lightning Knowledge — covering the one-time enablement decision, record type design on the `Knowledge__kav` object, Data Category configuration for dual-purpose organization and access control, and publishing workflow design using native statuses, Validation Status, and optional approval processes.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Lightning Knowledge enabled?** Navigate to Setup > Knowledge Settings. If the toggle is OFF, understand that enabling it is irreversible — once turned on, Classic Knowledge article types are permanently replaced by Lightning Knowledge record types on the single `Knowledge__kav` object. There is no undo path.
- **Most common wrong assumption:** Practitioners often assume Data Categories are purely organizational (like tags). In reality, they serve dual duty: content categorization AND access control. A user must have visibility to at least one category in every Data Category Group assigned to an article in order to see that article. Misconfigured visibility silently hides articles from users who expect to see them.
- **Platform constraints:** A single Salesforce org supports up to 5 Data Category Groups active for Knowledge (additional groups can exist but only 5 apply to Knowledge simultaneously). Each group supports up to 5 hierarchy levels and 100 categories per group.

---

## Core Concepts

### Lightning Knowledge and the Knowledge__kav Object

Lightning Knowledge consolidates all article content onto a single standard Salesforce object: `Knowledge__kav` (the Knowledge Article Version object). Unlike Classic Knowledge, which used separate custom objects for each article type, Lightning Knowledge uses standard record types on `Knowledge__kav` to differentiate content types (e.g., FAQ, How-To, Known Issue). This means page layouts, field sets, and Lightning record pages are configured per record type — the same tooling used for any other Salesforce object.

Enabling Lightning Knowledge is a one-way migration. The Setup toggle activates the feature and converts existing Classic article types into record types. There is no disable path and no rollback. Once enabled, Classic Knowledge Setup options disappear and the `Knowledge__kav` object is the permanent storage layer.

Each Knowledge Article has a parent `Knowledge__ka` (Knowledge Article) record that acts as the container, while `Knowledge__kav` records represent individual versions. Published articles always have exactly one published version. Archiving a published article creates a new Archived version rather than modifying the Published version in place.

### Data Categories: Dual-Purpose Organization and Access Control

Data Categories are hierarchical category groups that admins attach to Knowledge articles. Their dual role is critical:

1. **Organization**: Categories allow agents and customers to browse or filter articles by topic. A support team might use a "Products" category group with subcategories for each product line.
2. **Access Control**: Salesforce evaluates category visibility before showing articles to any user. Visibility is granted through Role Hierarchy, Profiles, or Permission Sets. If a user has no visibility into any category in a group that is assigned to an article, that article is invisible to them — regardless of object-level permissions.

The visibility model is additive: users inherit visibility from their role hierarchy. An admin must explicitly deny visibility to restrict access downward. Default visibility for unauthenticated guest users must be set separately via the Guest User Category Visibility settings.

Unclassified articles (articles with no category assigned from a group) are visible only to users with "View All Data" or explicit "Manage Categories" permissions — a common cause of articles disappearing immediately after creation.

### Publishing Workflow: Statuses, Validation Status, and Approval Processes

Every Knowledge article version moves through three native platform statuses:

- **Draft**: Article is being authored or edited. Not visible to end users.
- **Published**: Article is live. Exactly one published version can exist per article at any time. Publishing a new version automatically archives the previous published version.
- **Archived**: Article is retired from public view but preserved for history and potential restoration.

On top of native statuses, admins can enable a **Validation Status** picklist on `Knowledge__kav`. This is an admin-customizable picklist (values like "Validated", "Not Validated", "In Review") that signals content quality. Validation Status is separate from publish status — an article can be Published but flagged as "Not Validated." Agents can filter article searches by Validation Status to surface only quality-assured content.

For organizations requiring formal review before publishing, Salesforce supports standard **Approval Processes** on `Knowledge__kav`. An approval process can require sign-off from a subject-matter expert before a Draft article can transition to Published. Approval processes on Knowledge articles use the same Process Builder/Flow-backed approval framework as other objects, with the constraint that only the record owner or users with "Manage Articles" permission can submit articles for approval.

---

## Common Patterns

### Pattern: Record Type per Content Audience

**When to use:** When different teams produce different content types that need distinct field sets and layouts. For example, a support team authoring detailed technical Known Issue articles needs different fields than a marketing team writing FAQ articles for customers.

**How it works:**
1. Enable Lightning Knowledge in Setup > Knowledge Settings.
2. Navigate to Setup > Object Manager > Knowledge > Record Types.
3. Create a record type for each content type (e.g., "FAQ", "How-To", "Known Issue", "Release Note").
4. Assign page layouts per record type — hide internal-only fields (e.g., "Root Cause") from the customer-facing layout.
5. Assign record types to profiles so authors only see record types relevant to their role.

**Why not the alternative:** Using a single record type with all fields visible causes layout clutter and risks exposing internal fields (root cause analysis, workaround notes) to customer-facing surfaces. Record types enforce the separation cleanly without custom Apex.

### Pattern: Data Category Groups for Layered Visibility

**When to use:** When the org serves multiple audiences (internal agents, partners, customers via Experience Cloud) who should see overlapping but distinct article sets.

**How it works:**
1. Create Data Category Groups in Setup > Data Category Groups. Limit to 5 active groups for Knowledge.
2. Design the hierarchy to reflect your content taxonomy (e.g., "Products > Product A > Feature X").
3. In Setup > Roles, assign category visibility per role: "Include subcategories" to inherit the tree downward, or "Exclude" to explicitly block.
4. Test visibility by logging in as a representative user from each role before go-live.
5. For guest/unauthenticated users, set the default category visibility under Knowledge Settings > Guest User Category Access.

**Why not the alternative:** Using only object-level sharing or permission sets for article access bypasses the Data Category visibility check — articles remain invisible even if the user has object read access unless category visibility is also configured.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| Single article type, small team, no approval needed | One record type + native Draft/Published/Archived statuses | Lowest overhead; sufficient for simple use cases |
| Multiple content types with different field requirements | Separate record type per content type with distinct page layouts | Record types are the standard mechanism for layout differentiation on a single object |
| Content quality signal needed without blocking publish | Enable Validation Status picklist; train authors to mark status | Non-blocking; lets agents filter by quality without stopping publication |
| Regulated content requiring sign-off before publishing | Approval Process on Knowledge__kav + Validation Status | Approval processes enforce the gate; Validation Status surfaces the approval outcome |
| Multiple audiences with different article visibility needs | Data Category Groups with role-based visibility assignments | The only platform-native mechanism for audience-scoped article visibility |
| Migrating from Classic Knowledge | Plan record types before enabling Lightning Knowledge; enablement is irreversible | Post-enablement reconfiguration is possible but article type recategorization requires bulk data updates |

---

## Recommended Workflow

Step-by-step instructions for an admin or agent working on Knowledge setup:

1. **Confirm readiness for irreversible enablement**: Verify that all stakeholders understand Lightning Knowledge cannot be disabled once enabled. Document the decision. Confirm whether Classic Knowledge is in use and whether a migration plan exists for existing articles.
2. **Design record types before enabling**: Map out the content types needed (e.g., FAQ, How-To, Known Issue). Determine which fields belong on each layout. Plan profile-to-record-type assignments. This design is much harder to change after articles are created at scale.
3. **Enable Lightning Knowledge and configure record types**: Toggle Lightning Knowledge in Setup > Knowledge Settings. Create record types in Object Manager > Knowledge > Record Types. Build page layouts per record type. Assign record types to author profiles.
4. **Design and activate Data Category Groups**: Create category groups in Setup > Data Category Groups. Build the hierarchy. Assign visibility to roles and profiles. Set guest user defaults if articles will surface to unauthenticated users. Test visibility by logging in as a test user from each audience segment.
5. **Configure publishing workflow**: Decide whether native statuses are sufficient, or whether Validation Status and/or Approval Processes are needed. Enable Validation Status under Knowledge Settings if required. Build Approval Processes in Setup > Approval Processes targeting the Knowledge__kav object if formal sign-off is needed.
6. **Pilot and validate**: Have representative authors create articles of each record type, assign to categories, submit through the publishing workflow. Confirm visibility for each audience segment. Check that archived versions are preserved correctly.
7. **Document operational procedures**: Record the record type taxonomy, Data Category structure, and publishing workflow in an internal admin runbook. Knowledge administration decisions compound over time — undocumented decisions lead to inconsistent setups.

---

## Review Checklist

Run through these before marking Knowledge setup work complete:

- [ ] Lightning Knowledge enablement decision documented and acknowledged as irreversible
- [ ] Record types created with appropriate page layouts per content type
- [ ] Record types assigned to correct author profiles
- [ ] Data Category Groups created and active (5 max for Knowledge)
- [ ] Role/profile/permission-set visibility assigned for each audience; guest user defaults set if applicable
- [ ] Unclassified article visibility tested — confirm articles without categories behave as expected
- [ ] Publishing workflow configured (native statuses, Validation Status, and/or Approval Process)
- [ ] At least one test article created, published, and verified visible to each intended audience
- [ ] Archived version behavior verified (previous published version archived on re-publish)

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **Lightning Knowledge enablement is irreversible** — Once you enable Lightning Knowledge in Setup, there is no disable toggle. Classic Knowledge article types are permanently converted to record types on `Knowledge__kav`. Do not enable in production without a complete design review and stakeholder sign-off.
2. **Unclassified articles are invisible by default** — If an article has no Data Category assigned from any active Knowledge Category Group, it is only visible to users with "View All Data" or "Manage Articles" permission. New authors who forget to assign categories inadvertently publish invisible articles, leading to "I can't find the article I just published" support requests.
3. **Publishing a new version archives the previous one immediately** — There is no "schedule replacement" option. When you click Publish on a new version, the currently published version transitions to Archived instantly. If the new version has errors, you must immediately restore or publish a corrected version — there is no rollback to the previous published state.
4. **Data Category visibility is additive from role hierarchy, not subtractive** — Administrators cannot use role hierarchy to restrict visibility downward using inheritance alone. A child role inherits parent role visibility. If you need a child role to see fewer categories than the parent, you must explicitly configure that child role's visibility separately, not rely on inheritance.
5. **Approval Processes on Knowledge__kav require "Manage Articles" to submit** — Only the article owner or a user with the "Manage Articles" permission can submit a Knowledge article for approval. If authors lack this permission, they cannot trigger the approval workflow, breaking the publishing gate. Assign "Manage Articles" to author profiles intentionally.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| Knowledge Setup Decision Document | Records the Lightning Knowledge enablement decision, confirming it is irreversible and that stakeholders have approved |
| Record Type Taxonomy | Table of record types, associated layouts, and profile assignments |
| Data Category Group Map | Hierarchy diagram of category groups with role/profile visibility matrix per audience |
| Publishing Workflow Decision | Documents choice of native statuses / Validation Status / Approval Process and the rationale |
| Admin Runbook | Operational procedures for ongoing Knowledge management (creating article types, updating categories, managing approvals) |

---

## Related Skills

- `architect/knowledge-vs-external-cms` — Use when deciding whether to use Salesforce Knowledge or an external CMS for content management
- `agentforce/einstein-copilot-for-service` — Knowledge article quality directly bounds Einstein Service Replies grounding quality; review both skills when deploying AI-assisted service
- `admin/delegated-administration` — Use alongside this skill when Knowledge article management responsibilities are delegated to non-admin users
