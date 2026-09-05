# Well-Architected Notes — Knowledge Base Administration

## Relevant Pillars

- **Security** — Data Category visibility is the primary access control mechanism for Knowledge articles. A misconfigured category group can expose internal escalation procedures to external customers or render all articles invisible. Security design must treat Data Category visibility configuration with the same rigor as object-level sharing and permission sets. Guest user default category access must be explicitly reviewed for any org with public-facing Knowledge surfaces.

- **Operational Excellence** — Lightning Knowledge enablement is irreversible. Operational excellence demands that record type design, Data Category taxonomies, and publishing workflows are designed upfront and documented in admin runbooks before the feature is enabled in production. Knowledge administration compounds: a poorly designed category hierarchy becomes expensive to reorganize once hundreds of articles are classified against it.

- **Reliability** — Publishing a new article version immediately archives the current published version with no rollback. Reliable publishing operations require author training, review workflows (Validation Status and/or Approval Processes), and a documented restoration procedure for cases where a newly published version contains errors.

- **Performance** — Not a primary concern at the feature-configuration level. However, large Data Category Group hierarchies (deep nesting, many categories) can slow article search filtering. Keep hierarchies shallow — the Metadata API guide allows 5 levels and 100 categories per group, and `scripts/check_knowledge_base_administration.py` flags anything past 3 levels for a second look. The org-level cap on *active* groups is sized in `architect/knowledge-taxonomy-design`.

- **Scalability** — Record type design scales well as content volume grows, provided the taxonomy is defined early. Data Category Groups have hard platform limits — the Metadata API guide states 100 categories per group and 5 hierarchy levels, and an org-level cap applies to how many groups can be active for Knowledge. Designs that approach these limits should be re-evaluated for consolidation before hitting them, because the escape hatch is expensive: a category developer name "is defined once and cannot be changed later", and a deploy that omits a category deletes it and re-parents its articles.

## Architectural Tradeoffs

**Native statuses vs. Validation Status vs. Approval Process:**
Native statuses (Draft/Published/Archived) are zero-configuration and sufficient for small teams with high author trust. Validation Status adds a non-blocking quality signal without stopping publication — appropriate for teams that want searchable quality indicators without enforcement. Approval Processes enforce a blocking gate but introduce latency into publishing cycles. Choose based on the organization's content governance requirements, not technical preference.

**Data Categories for visibility vs. External CMS segmentation:**
Salesforce Knowledge Data Categories provide audience-scoped visibility within the platform. For organizations serving many distinct external audiences with complex content segmentation needs, an external headless CMS with its own access control model may scale better than the per-group platform limits. The `architect/knowledge-vs-external-cms` skill addresses this tradeoff.

**Deploy the taxonomy vs. build it in Setup:**
Everything else in a Knowledge setup — settings, record types, fields, layouts, profiles, permission sets — belongs in source control and moves through the normal deploy pipeline. `DataCategoryGroup` is the exception, and the Metadata API guide says so directly: deploying category changes between orgs "permanently removes categories and record categorizations that are not specified in your XML file", and Salesforce recommends creating categories and record associations in Setup instead. The resolution most orgs land on is to keep the group XML in the repo as the reviewed design artefact and to apply structural category changes by hand in each org, with the checker in this package run against the retrieved file to confirm the two have not drifted.

**Role-based visibility vs. Profile/Permission-Set-based visibility:**
Role-based category visibility inherits through the role hierarchy (additive only), making it efficient for large user populations. Profile or permission-set-based visibility allows fine-grained overrides but creates maintenance overhead as the org grows. Prefer role-based visibility as the primary mechanism and use profile/permission-set overrides sparingly for exceptions.

## Anti-Patterns

1. **Enabling Lightning Knowledge without a record type design plan** — Admins enable the feature to explore it, then discover that post-enablement reconfiguration of existing articles requires bulk data updates. Design record types, layouts, and category groups in a Developer sandbox before enabling in any shared environment.

2. **Treating Data Categories as tags only** — Building a category hierarchy for browsability without understanding the access control implications leads to articles being silently hidden from users who should see them, or silently visible to users who should not. Every category visibility change must be validated by logging in as a representative user from each affected audience.

3. **Publishing new article versions without a review step** — The instantaneous archive of the previous published version on re-publish means a typo in a new version immediately goes live. Approval Processes or at minimum a Validation Status review step should gate all re-publishes of high-traffic articles.

## Official Sources Used

Primary — read directly for this package (Summer '26 / v62 PDF extractions):

- **Metadata API Developer Guide — `KnowledgeSettings`** (`enableKnowledge`, `enableLightningKnowledge`, `defaultLanguage`, `showValidationStatusField`, `enableKbStandardSharing`, `KnowledgeLanguageSettings` / `KnowledgeLanguage` with `defaultAssigneeType` values `User` and `Queue`, `KnowledgeSuggestedArticlesSettings`, and the sample settings file) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- **Metadata API Developer Guide — `DataCategoryGroup`, `DataCategory`, `ObjectUsage`, and the "Usage" section** (required `active`, `label`, `fullName`; the 100-category and 5-level caps; `objectUsage` valid values `KnowledgeArticleVersion` and `Question`; the warning that deploying a group deletes undeclared categories and re-parents their records; the "name is defined once and cannot be changed later" note; the sandbox-to-production worked example) — same PDF
- **Metadata API Developer Guide — `Profile` / `ProfileCategoryGroupVisibility` and `PermissionSet`** (`categoryGroupVisibilities` is a Profile field from API 41.0 with `visibility` values `ALL` / `CUSTOM` / `NONE`; the `PermissionSet` field list has no equivalent; `PermissionSetObjectPermissions` and `PermissionSetRecordTypeVisibility` shapes) — same PDF
- **Metadata API Developer Guide — `RecordType`, `ArticleType CustomField`, `ChannelLayout`, and the wildcard notes** (record types are not an access control; `businessProcess` is not allowed outside lead/opportunity/solution/case; `RecordType` does not support `*`; `*` on `CustomObject` does not match standard objects; the wildcard does not apply to an individual feature setting) — same PDF
- **Object Reference — `Knowledge__kav`, `KnowledgeArticleVersion`, `Knowledge__DataCategorySelection`, `User.UserPermissionsKnowledgeUser`** (the Knowledge User feature licence requirement; `PublishStatus` values `Draft` / `Online` / `Archived` and the mandatory `PublishStatus`-or-`Id` filter; `IsLatestVersion`, `IsMasterLanguage`, `ValidationStatus`, `ArticleNumber`, the four `IsVisibleIn*` channel flags; the bind-variable restriction and its dynamic-SOQL workaround; the renameable object prefix; the create/delete-only category selection object) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- **Apex Reference Guide — `KbManagement.PublishingService`** (`publishArticle`, `scheduleForPublication`, `archiveOnlineArticle`, `cancelScheduledPublicationOfArticle`, `restoreOldVersion`; all static; date values are GMT) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- **Salesforce App Limits Cheat Sheet** — checked for Knowledge and data category limits and it documents none, which is why the org-level active-group cap in this package carries an UNVERIFIED marker rather than a citation.

Secondary — Salesforce Help articles behind the enablement and Setup-path claims. These cannot be fetched from the authoring environment, so any claim resting on them alone carries an UNVERIFIED marker in the text:

- Salesforce Help — Set Up Lightning Knowledge: https://help.salesforce.com/s/articleView?id=sf.knowledge_setup_lightning.htm
- Salesforce Help — Workflow and Approvals for Articles: https://help.salesforce.com/s/articleView?id=sf.knowledge_setup_workflow.htm
- Salesforce Help — Data Categories: https://help.salesforce.com/s/articleView?id=sf.knowledge_data_categories.htm
- Salesforce Help — Record Type Considerations for Knowledge: https://help.salesforce.com/s/articleView?id=sf.knowledge_record_type_considerations.htm
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
