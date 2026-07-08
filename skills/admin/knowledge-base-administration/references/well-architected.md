# Well-Architected Notes — Knowledge Base Administration

## Relevant Pillars

- **Security** — Data Category visibility is the primary access control mechanism for Knowledge articles. A misconfigured category group can expose internal escalation procedures to external customers or render every classified article invisible. Security design must treat Data Category visibility configuration with the same rigor as object-level sharing and permission sets. The Guest User profile's category visibility must be explicitly reviewed for any org with public-facing Knowledge surfaces — guest users have no role, so nothing in the role hierarchy governs them, and the org-wide *Default Data Category Visibility* fallback is easy to leave permissive by accident. Two further controls belong in the same review: the per-article channel flags (`IsVisibleInCsp`, `IsVisibleInPrm`, `IsVisibleInPkb` — the three writable ones; `IsVisibleInApp` is defaulted on create and not settable), which decide publishing eligibility per audience surface, and the "Share internal Knowledge articles externally" app permission, which decides who may push internal content outward at all. Because Data Category Visibility definitions on roles, permission sets, and profiles are combined with a logical OR, a permission set granted for an unrelated reason can silently widen an external audience's article access.

- **Operational Excellence** — Lightning Knowledge enablement is irreversible. Operational excellence demands that record type design, Data Category taxonomies, and publishing workflows are designed upfront and documented in admin runbooks before the feature is enabled in production. Knowledge administration compounds: a poorly designed category hierarchy becomes expensive to reorganize once hundreds of articles are classified against it.

- **Reliability** — Publishing a new article version immediately archives the current published version with no rollback. Reliable publishing operations require author training, review workflows (Validation Status and/or Approval Processes), and a documented restoration procedure for cases where a newly published version contains errors.

- **Performance** — Not a primary concern at the feature-configuration level. However, large Data Category Group hierarchies (deep nesting, many categories) can slow article search filtering. Keep hierarchies shallow (3–4 levels, against a platform maximum of 5) and stay within the default ceiling of 3 active category groups.

- **Scalability** — Record type design scales well as content volume grows, provided the taxonomy is defined early. Data Category Groups have default platform limits: 5 category groups with 3 active at a time, 100 categories per group, 5 hierarchy levels, and a maximum of 8 categories from one group on a single article. Salesforce Support can raise the group and category limits on request, but a design that needs the increase is usually a design that should consolidate first.

## Architectural Tradeoffs

**Native statuses vs. Validation Status vs. Approval Process:**
Native statuses (Draft/Published/Archived) are zero-configuration and sufficient for small teams with high author trust. Validation Status adds a non-blocking quality signal without stopping publication — appropriate for teams that want searchable quality indicators without enforcement. Approval Processes enforce a blocking gate but introduce latency into publishing cycles. Choose based on the organization's content governance requirements, not technical preference.

**Data Categories for visibility vs. External CMS segmentation:**
Salesforce Knowledge Data Categories provide audience-scoped visibility within the platform. For organizations serving many distinct external audiences with complex content segmentation needs, an external headless CMS with its own access control model may scale better than the default 3-active-group, 100-category platform limits. The `architect/knowledge-vs-external-cms` skill addresses this tradeoff.

**Role-based visibility vs. Profile/Permission-Set-based visibility:**
Role-based category visibility propagates down the role hierarchy, making it efficient for large user populations — but the parent role is a ceiling, not just a starting point. Child roles inherit the parent's settings and stay in sync with changes to them; an admin can customize and reduce a child's visibility, but cannot raise it above the parent's. A team that sits low in the hierarchy and needs a category its manager's role lacks cannot be served by roles at all. Profile or permission-set-based visibility allows fine-grained overrides but creates maintenance overhead as the org grows. Prefer role-based visibility as the primary mechanism and use profile/permission-set overrides for exceptions — including that one. Experience Cloud is the standing exception: external users commonly share a coarse portal role, and guest and high-volume portal users have no role at all, so permission-set- or profile-based Data Category Visibility is often the only mechanism that reaches them. Salesforce ORs the role, permission set, and profile definitions together, so an external audience's effective visibility is the union of every source — audit all three when a customer can see something they should not.

**Help Center template vs. general Experience Cloud template:**
The Help Center template is purpose-built to expose a knowledge base for public self-service, with search, article pages, and topic navigation already assembled. A general customer-service or partner template can host the same Knowledge surface, but the admin assembles it by hand from Experience Builder components. Choose Help Center when article browsing *is* the site; choose a general template when Knowledge is one capability alongside cases, communities, or commerce, and accept the extra assembly cost. Standing up a second site purely to get the Help Center layout adds a second membership model, a second guest user, and a second SEO surface — rarely worth it.

The template choice also carries a security consequence that is easy to miss: Help Center is public-access, so its default reader is an unauthenticated guest. Guests are matched against the Public Knowledge Base channel, not the Customer channel, and are governed by the Guest User profile's Data Category Visibility rather than by any role. Picking Help Center therefore moves the access-control review onto the guest user, and it means the content-governance question ("is this article safe to publish with no login in front of it?") applies to every article the site surfaces.

**Case deflection as the design objective:**
Salesforce frames Knowledge on an experience site around case deflection, customer satisfaction, and agent productivity rather than around publishing throughput. That reframing changes design decisions: article coverage of top case drivers matters more than article count, topic navigation matters more than category depth, and the channel matrix becomes a content-governance artifact (who decides an article is safe to publish externally) rather than an author-level checkbox. Measure the surface by deflection, not by articles published.

## Anti-Patterns

1. **Enabling Lightning Knowledge without a record type design plan** — Admins enable the feature to explore it, then discover that post-enablement reconfiguration of existing articles requires bulk data updates. Design record types, layouts, and category groups in a Developer sandbox before enabling in any shared environment.

2. **Treating Data Categories as tags only** — Building a category hierarchy for browsability without understanding the access control implications leads to articles being silently hidden from users who should see them, or silently visible to users who should not. Every category visibility change must be validated by logging in as a representative user from each affected audience.

3. **Publishing new article versions without a review step** — The instantaneous archive of the previous published version on re-publish means a typo in a new version immediately goes live. Approval Processes or at minimum a Validation Status review step should gate all re-publishes of high-traffic articles.

4. **Treating the external channel flag as an author-level convenience** — `IsVisibleInCsp`, `IsVisibleInPrm`, and `IsVisibleInPkb` decide whether internal content leaves the org. When any author with Publish Articles can also set them, the org has no gate between internal troubleshooting notes and a public URL. Pair the channel decision with the "Share internal Knowledge articles externally" permission, a named content owner, and (for regulated content) an Approval Process step that inspects the channel fields.

5. **Debugging an empty Experience Cloud Knowledge surface from the outside in** — Teams reliably start at the Experience Builder component, then the channel flag, then Data Category Visibility, and only discover Topics-for-Objects hours later. The dependency runs the other way. Check Topics first, then site-level Knowledge enablement, then the channel flag, then category visibility, then the component. Encode that order in the runbook.

6. **Choosing the channel flag from the template name rather than from the reader** — "Help Center is for customers, so set the Customer channel" is the single most expensive wrong inference in this domain. `IsVisibleInCsp` covers authenticated customer users; unauthenticated visitors to a public-access site are guests and need `IsVisibleInPkb`. The failure is silent and total: a correctly published, correctly categorized, Customer-flagged article renders nothing to a logged-out reader. Decide the channel from who is reading, verify each audience with its own session, and never accept an Experience Builder preview as evidence that the guest path works.

## Official Sources Used

- Salesforce Help — Set Up Lightning Knowledge: https://help.salesforce.com/s/articleView?id=sf.knowledge_setup_lightning.htm
- Salesforce Help — Workflow and Approvals for Articles: https://help.salesforce.com/s/articleView?id=sf.knowledge_setup_workflow.htm
- Salesforce Help — Data Categories: https://help.salesforce.com/s/articleView?id=sf.knowledge_data_categories.htm
- Salesforce Help — Record Type Considerations for Knowledge: https://help.salesforce.com/s/articleView?id=sf.knowledge_record_type_considerations.htm
- Salesforce Help — Data Category Visibility: https://help.salesforce.com/s/articleView?id=sf.category_visibility_whatis.htm&language=en_US&type=5
- Salesforce Help — Modify Default Data Category Visibility: https://help.salesforce.com/s/articleView?id=service.category_visibility_default.htm&language=en_US&type=5
- Salesforce Help — Edit Category Group Visibility: https://help.salesforce.com/s/articleView?id=service.category_visibility_modify.htm&language=en_US&type=5
- Salesforce Help — Enable Salesforce Knowledge in Your Experience Cloud Site: https://help.salesforce.com/s/articleView?id=experience.networks_knowledge_access.htm&language=en_US&type=5
- Salesforce Help — Give Customers Access to Your Knowledge Base Through Help Center: https://help.salesforce.com/s/articleView?id=experience.networks_help_center_intro.htm&language=en_US&type=5
- Salesforce Help — Help Center Set Up Tasks: https://help.salesforce.com/s/articleView?id=experience.networks_help_center_tasks.htm&language=en_US&type=5
- Salesforce Help — Manage Topics in Experience Cloud Sites: https://help.salesforce.com/s/articleView?id=experience.networks_topics_all.htm&language=en_US&type=5
- Salesforce Help — Automatically Assign Topics to Articles: https://help.salesforce.com/s/articleView?id=experience.networks_topics_automatic_topic_assignment.htm&language=en_US&type=5
- Salesforce Help — Topic Catalog (Experience Builder component): https://help.salesforce.com/s/articleView?id=experience.rss_topic_catalog.htm&language=en_US&type=5
- Salesforce Help — Articles with This Topic (Experience Builder component): https://help.salesforce.com/s/articleView?id=experience.rss_articles_with_this_topic.htm&language=en_US&type=5
- Salesforce Help — Set Up and Configure Salesforce Knowledge Users: https://help.salesforce.com/s/articleView?id=service.knowledge_setup_users_lex.htm&language=en_US&type=5
- Salesforce Help — Set Up Actions to Share Article URLs in Channels and Case Publishers: https://help.salesforce.com/s/articleView?id=service.knowledge_send_articles.htm&language=en_US&type=5
- Salesforce Help (Knowledge Article 000382935) — View Knowledge Base Articles on a Lightning Platform Site: https://help.salesforce.com/s/articleView?id=000382935&language=en_US&type=1
- Salesforce Developers — Knowledge__kav object reference (channel visibility field properties, `PublishStatus` picklist values): https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_knowledge__kav.htm
- Salesforce Developers — KnowledgeArticleVersion object reference: https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_knowledgearticleversion.htm
- Trailhead — Enable and Configure Lightning Knowledge, in the project *Build an Experience Cloud Site with Knowledge and Enhanced Chat* (source of the "articles can't be displayed outside an org" Topics prerequisite): https://trailhead.salesforce.com/content/learn/projects/build-a-community-with-knowledge-and-chat/add-knowledge-to-the-community-using-topics
- Trailhead — Set Access for Lightning Knowledge (Set Up Salesforce Knowledge): https://trailhead.salesforce.com/content/learn/projects/set-up-salesforce-knowledge/set-access-for-lightning-knowledge
- Salesforce Knowledge Implementation Guide (PDF) — Data Category Limits table, Data Category Visibility, Initial Visibility Settings, Role-Based Visibility Setting Inheritance, Categorized Article Visibility, Revoked Visibility, Create and Modify Category Groups, Data Category Implementation Tips: https://resources.docs.salesforce.com/latest/latest/en-us/sfdc/pdf/salesforce_knowledge_implementation_guide.pdf
- Salesforce Well-Architected Overview: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
