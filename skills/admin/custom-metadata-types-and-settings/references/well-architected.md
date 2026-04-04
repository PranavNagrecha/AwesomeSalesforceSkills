# Well-Architected Notes — Custom Metadata Types And Settings

## Relevant Pillars

- **Operational Excellence** — The most impactful pillar for this skill. Choosing CMT over Custom Settings for deployable configuration eliminates an entire class of manual post-deploy steps, reduces environment drift, and makes configuration changes visible in source control and code review. The wrong choice creates invisible operational risk every deployment cycle.

- **Reliability** — Both storage types can create reliability problems when misused. CMT accessed in tight loops without defensive null handling fails silently. Hierarchical Custom Settings return null when no org-default record exists, causing NullPointerExceptions in production. The correct access pattern and defensive fallback defaults are reliability requirements, not optional polish.

- **Performance** — CMT SOQL queries cost zero against the 100 SOQL governor limit. Custom Settings consume the limit (once per transaction, after which they are cached). In high-volume trigger scenarios or batch jobs that call a helper once per record, this difference is material. Choose CMT when the configuration is static and performance is critical.

## Architectural Tradeoffs

**Deploy-time stability vs runtime flexibility:** CMT gives you configuration that is consistent across all users and is controlled by the release process. Hierarchical Custom Settings give you runtime flexibility to override behavior per user or profile without any deployment. These are genuinely different capabilities — choosing CMT when you need per-user overrides forces you to build a custom resolution layer that duplicates what the platform already provides.

**Governor limit headroom vs operational simplicity:** For most orgs with moderate Apex complexity, the Custom Setting SOQL cost (1 per transaction, cached) is negligible. In high-volume automation (batch jobs, trigger-heavy record processing, integrations processing thousands of records per hour), the SOQL budget matters and CMT's zero-cost model is architecturally safer.

**Deployment artifact vs org-only data:** Custom Setting records are org-specific data, not deployment artifacts. This is correct when the values are meant to be environment-specific (users in production are different from users in UAT — user-level overrides should not copy blindly). It is wrong when the values are supposed to be identical in all orgs and controlled by the release team.

## Anti-Patterns

1. **Using CMT to simulate per-user overrides** — creating one CMT record per user to store preferences. CMT has a 200-record limit per type, does not have a built-in resolution hierarchy, and turns user preference management into a deployment operation. Hierarchical Custom Settings exist precisely for this use case and are dramatically simpler.

2. **Using Hierarchical Custom Settings for deployable org configuration** — storing routing rules, feature flags, or integration endpoints in a Custom Setting because it is "easy to change in production." The values are now invisible to source control, cannot be reliably promoted through environments, and require manual setup in every org. Custom Metadata Types solve this at no additional complexity cost.

3. **Creating new List Custom Settings** — List Custom Settings are deprecated in Lightning Experience. New implementations that use them create invisible technical debt and prevent the configuration from being included in packages. Migrate to CMT for all new flat configuration requirements.

## Official Sources Used

- Custom Metadata Types (Help) — https://help.salesforce.com/s/articleView?id=sf.custommetadatatypes_overview.htm
- Custom Settings (Help) — https://help.salesforce.com/s/articleView?id=sf.cs_about.htm
- Apex Developer Guide: Custom Metadata Types — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_custommetadatatypes_overview.htm
- Apex Developer Guide: Custom Settings — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_methods_system_custom_settings.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
