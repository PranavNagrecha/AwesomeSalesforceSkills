# Well-Architected Notes — Knowledge Base Administration

## Relevant Pillars

- **Security** — Data Category visibility is the primary access control mechanism for Knowledge articles. A misconfigured category group can expose internal escalation procedures to external customers or render all articles invisible. Security design must treat Data Category visibility configuration with the same rigor as object-level sharing and permission sets. Guest user default category access must be explicitly reviewed for any org with public-facing Knowledge surfaces.

- **Operational Excellence** — Lightning Knowledge enablement is irreversible. Operational excellence demands that record type design, Data Category taxonomies, and publishing workflows are designed upfront and documented in admin runbooks before the feature is enabled in production. Knowledge administration compounds: a poorly designed category hierarchy becomes expensive to reorganize once hundreds of articles are classified against it.

- **Reliability** — Publishing a new article version immediately archives the current published version with no rollback. Reliable publishing operations require author training, review workflows (Validation Status and/or Approval Processes), and a documented restoration procedure for cases where a newly published version contains errors.

- **Performance** — Not a primary concern at the feature-configuration level. However, large Data Category Group hierarchies (deep nesting, many categories) can slow article search filtering. Keep hierarchies shallow (3–4 levels maximum) and limit total active Knowledge Category Groups to the platform maximum of 5.

- **Scalability** — Record type design scales well as content volume grows, provided the taxonomy is defined early. Data Category Groups have hard platform limits (5 active groups for Knowledge, 100 categories per group, 5 hierarchy levels). Designs that approach these limits should be re-evaluated for consolidation before hitting them.

## Architectural Tradeoffs

**Native statuses vs. Validation Status vs. Approval Process:**
Native statuses (Draft/Published/Archived) are zero-configuration and sufficient for small teams with high author trust. Validation Status adds a non-blocking quality signal without stopping publication — appropriate for teams that want searchable quality indicators without enforcement. Approval Processes enforce a blocking gate but introduce latency into publishing cycles. Choose based on the organization's content governance requirements, not technical preference.

**Data Categories for visibility vs. External CMS segmentation:**
Salesforce Knowledge Data Categories provide audience-scoped visibility within the platform. For organizations serving many distinct external audiences with complex content segmentation needs, an external headless CMS with its own access control model may scale better than the 5-group, 100-category platform limits. The `architect/knowledge-vs-external-cms` skill addresses this tradeoff.

**Role-based visibility vs. Profile/Permission-Set-based visibility:**
Role-based category visibility inherits through the role hierarchy (additive only), making it efficient for large user populations. Profile or permission-set-based visibility allows fine-grained overrides but creates maintenance overhead as the org grows. Prefer role-based visibility as the primary mechanism and use profile/permission-set overrides sparingly for exceptions.

## Anti-Patterns

1. **Enabling Lightning Knowledge without a record type design plan** — Admins enable the feature to explore it, then discover that post-enablement reconfiguration of existing articles requires bulk data updates. Design record types, layouts, and category groups in a Developer sandbox before enabling in any shared environment.

2. **Treating Data Categories as tags only** — Building a category hierarchy for browsability without understanding the access control implications leads to articles being silently hidden from users who should see them, or silently visible to users who should not. Every category visibility change must be validated by logging in as a representative user from each affected audience.

3. **Publishing new article versions without a review step** — The instantaneous archive of the previous published version on re-publish means a typo in a new version immediately goes live. Approval Processes or at minimum a Validation Status review step should gate all re-publishes of high-traffic articles.

## Official Sources Used

- Salesforce Help — Set Up Lightning Knowledge: https://help.salesforce.com/s/articleView?id=sf.knowledge_setup_lightning.htm
- Salesforce Help — Workflow and Approvals for Articles: https://help.salesforce.com/s/articleView?id=sf.knowledge_setup_workflow.htm
- Salesforce Help — Data Categories: https://help.salesforce.com/s/articleView?id=sf.knowledge_data_categories.htm
- Salesforce Help — Record Type Considerations for Knowledge: https://help.salesforce.com/s/articleView?id=sf.knowledge_record_type_considerations.htm
- Lightning Knowledge Guide PDF: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/knowledge_guide.pdf
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
