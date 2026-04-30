# Well-Architected Notes — Classic Email Template Migration

## Relevant Pillars

- **User Experience** — Lightning Email Templates use the Email Template Builder, a drag-and-drop, block-based editor that admins can use without HTML knowledge. Classic HTML templates required hand-editing HTML — a barrier that pushed simple template tweaks back to developers. Migration shifts template ownership back to admins, accelerates iteration, and aligns the email-creation surface with the rest of Lightning Experience. Recipients also benefit: Lightning templates render consistently across devices because the builder defaults to email-tested patterns (table-based layout, web-safe fonts, inline styles).

- **Operational Excellence** — Classic email infrastructure (Letterheads, Custom HTML, Visualforce templates) is in maintenance mode. New email features ship for Lightning Email Templates only — Engagement, Email Tracking enhancements, Einstein Send Time Optimization, integration with Outlook/Gmail Inbox add-ins. Retaining Classic templates means accepting that the org cannot adopt new email capabilities without migrating first. Migration removes the structural blocker.

- **Security** — Classic Visualforce email templates ran arbitrary Apex with the running user's permissions. Some legacy templates included unsanitized merge fields (`{!Account.Custom_HTML_Field__c}`) that rendered raw HTML — an XSS vector if the field was user-editable. Lightning Email Templates use a strict merge engine that escapes content by default; the migration is the moment to audit which Classic templates depended on raw HTML rendering and whether the rendering was safe.

## Architectural Tradeoffs

**Migrate Visualforce templates vs retain them:** Visualforce email templates can do things Lightning cannot — controller-driven logic, complex iteration, conditional content based on Apex evaluation. Migrating them forces the logic into either a hand-coded Apex string builder (loses admin-editable surface) or pre-computed record fields (forces denormalization). Retaining VF preserves capability at the cost of split template infrastructure and staying current with VF in an otherwise Lightning-first org. Default: retain VF when the logic is genuine; migrate when the template only used VF for simple merge fields the Lightning engine can handle.

**One Enhanced Letterhead vs many:** Classic Letterheads often proliferated because the editor was painful and copying was easier than maintaining a single asset. Centralizing on 1–3 Enhanced Letterheads per org reduces brand maintenance to a single record but requires upfront agreement on the brand variants. The right tradeoff is centralization for transactional/corporate templates, with separate Enhanced Letterheads only when the brand variant is genuine (e.g., a co-branded letterhead for a partner program).

**Pre-compute conditional logic on records vs accept template limitations:** Lightning's merge engine doesn't support `IF`/`CASE`. Migration can either (a) move conditional logic upstream to formula fields on the merge record, or (b) accept simpler templates without conditional content. Option (a) preserves the email's behavior but adds formula fields the data model didn't otherwise need. Option (b) simplifies the data model but may degrade the email experience. Choose (a) when the conditional content is meaningful (personalized greetings, fallback values); (b) when the conditional was historical noise.

**Bulk metadata-API rewiring vs incremental setup-UI updates:** Bulk via Metadata API is faster, auditable, and produces a deployment artifact. Incremental UI updates are slower but require less Apex / DevOps tooling knowledge. For >10 Email Alerts, Metadata API wins on speed and reliability. For <10, the UI is faster than building the metadata package. Either path requires an old → new ID mapping table; the difference is execution mechanism, not strategy.

## Anti-Patterns

1. **Rewriting all Visualforce templates as Apex string builders to "complete" the migration.** Visualforce email templates remain a supported Salesforce capability. Hand-coded Apex string builders lose the admin-editable surface (only developers can change the email going forward), are harder to test, and don't render in the standard email preview UI. Migrate VF only when the template's Apex logic is excessive for what it does; otherwise retain.

2. **Per-template Enhanced Letterheads.** Recreating one Enhanced Letterhead per Classic Letterhead preserves the proliferation problem. The well-architected outcome is fewer, shared Letterheads. Make centralization a migration goal, not an afterthought.

3. **Skipping the merge-formula audit.** `{!IF()}`, `{!CASE()}`, `{!URLENCODE()}`, `{!$Setup.X}` — none translate. A migration that doesn't audit for these silently produces emails with literal expression strings in the body. Always grep template bodies for `{!IF`, `{!CASE`, `{!$Setup`, `{!System.` before migrating, and decide the per-template handling.

4. **Folder-sharing oversight.** Templates are useless if the running profile of an Email Alert can't see them. Migration plans that ignore folder sharing produce alerts that fail at send time with `INVALID_FIELD: TemplateId is invalid`. Replicate folder structure AND folder sharing as a precondition.

5. **Deleting Classic templates immediately after creating Lightning equivalents.** Activity history, audit logs, and not-yet-rewired downstream consumers may still reference Classic IDs. Deactivate (`IsActive=false`) instead of delete; schedule deletion after a 90-day soak with confirmed zero references.

6. **Trusting the Salesforce preview as the only rendering test.** Outlook's email rendering engine is far more limited than the Salesforce preview's browser engine. A template that looks correct in preview may have broken layouts in Outlook. Always test on real clients before declaring migration complete.

## Official Sources Used

- EmailTemplate sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_emailtemplate.htm
- Lightning Email Templates Help — https://help.salesforce.com/s/articleView?id=sf.email_templates_lightning_overview.htm
- Enhanced Letterheads Help — https://help.salesforce.com/s/articleView?id=sf.email_letterhead_enhanced.htm
- Email Template Builder Help — https://help.salesforce.com/s/articleView?id=sf.email_template_builder_overview.htm
- Visualforce Email Templates — https://help.salesforce.com/s/articleView?id=sf.email_templates_vf.htm
- Workflow Email Alerts — https://help.salesforce.com/s/articleView?id=sf.customize_wfalerts.htm
- OrgWideEmailAddress sObject Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_orgwideemailaddress.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
