# Well-Architected Notes — Custom Metadata Types And Settings

## Relevant Pillars

- **Operational Excellence** — The most impactful pillar for this skill. Choosing CMT over Custom Settings for deployable configuration eliminates an entire class of manual post-deploy steps, reduces environment drift, and makes configuration changes visible in source control and code review. The wrong choice creates invisible operational risk every deployment cycle.

- **Reliability** — Both storage types create reliability problems when misused, but not the ones most teams guard against. `getInstance()` and `getOrgDefaults()` return an object with empty fields rather than null when a hierarchy setting has never been seeded, so the record-level null check that most code carries never fires and a null *field* flows into a cast or a comparison instead. The reliability requirement is a per-field default and a seed script that runs in every environment — not a null guard on the record.

- **Performance** — Both CMT records and custom settings data are served from a cache, so neither costs SOQL when read through the intended path. The performance failure is the one that looks like ordinary Salesforce code: a SOQL query against a `__c` custom setting, which bypasses the application cache and behaves like a custom object query. In a trigger handler called once per record, that is the difference between zero queries and a governor limit.

## Architectural Tradeoffs

**Deploy-time stability vs runtime flexibility:** CMT gives you configuration that is consistent across all users and is controlled by the release process. Hierarchical Custom Settings give you runtime flexibility to override behavior per user or profile without any deployment. These are genuinely different capabilities — choosing CMT when you need per-user overrides forces you to build a custom resolution layer that duplicates what the platform already provides per field.

**Where the data lives vs where the definition lives:** the definition is metadata and the rows are org data, and no amount of manifest engineering changes that. The design question is therefore not "will this deploy" but "who owns the seed script, and is it reviewed like code". A hierarchy setting whose org default is created by hand in each org is a configuration decision with no audit trail.

**Security posture vs integration compatibility:** `enableAdvancedCSSecurity` restricts custom settings values to Apex, flow, and formula operations, and defaults to off. Turning it on is the correct posture for internal configuration and is also a breaking change for any SOAP or Enterprise WSDL consumer that has been reading those values. The tradeoff has to be made deliberately, with the reader inventory in hand, rather than discovered during an incident.

**`Protected` as a packaging attribute, not an access control:** outside a managed package, a Protected custom setting is readable by all profiles including the guest user. Teams that treat the switch as security put values behind a label that does nothing. Inside a managed package the same switch swings the other way and locks the subscriber out of values they may be expected to configure.

## Anti-Patterns

1. **Using CMT to simulate per-user overrides** — creating one CMT record per user to store preferences. CMT has no built-in resolution hierarchy and turns user preference management into a deployment operation. Hierarchical Custom Settings exist precisely for this use case and merge per field.

2. **Using Hierarchical Custom Settings for deployable org configuration** — storing routing rules, feature flags, or integration endpoints in a Custom Setting because it is "easy to change in production." The values are now invisible to source control, cannot be promoted through environments, and require setup in every org. Custom Metadata Types solve this at no additional complexity cost.

3. **Querying a custom setting with SOQL in runtime code** — the query looks like every other sObject read and is the one access path that gives up the cache and spends a governor query. Reserve it for verification and migration scripts.

4. **Making tests pass with `SeeAllData=true`** — custom settings data is invisible to Apex tests by design. Switching the annotation on couples the test to whatever the org happens to contain; seeding in `@TestSetup` keeps it deterministic.

5. **Deferring the permission set** — read access to a custom setting is a `customSettingAccesses` grant. A feature verified only as an admin will read empty for everyone else, and on classes below API 54.0 `DescribeSObjectResult.isAccessible()` will report that everything is fine.

## Official Sources Used

- Apex Developer Guide (v62 PDF), *Custom Settings* — the cache statement ("you don't have to use SOQL queries that count against your governor limits"), the org < profile < user resolution order, the packaging rule "Only custom settings definitions are included in packages, not data", the Protected warning about guest-user readability, and the test-isolation note requiring `SeeAllData=true` or seeded data. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/salesforce_apex_developer_guide.pdf
- Apex Developer Guide (v62 PDF), *Apex Behavior Changes* — the API 42.0 `DUPLICATE_VALUE` behaviour for hierarchy settings inserted in both `@TestSetup` and a test method, and the API 54.0 change to `DescribeSObjectResult.isAccessible()` for custom settings and custom metadata types (supports `references/gotchas.md` §5 and §10).
- Apex Reference Guide (v62 PDF), *Custom Settings Methods* — the SOQL-bypasses-the-cache note, the full `getInstance` / `getValues` / `getAll` / `getOrgDefaults` signatures, the worked `Hierarchy__c` example showing that `getValues(id)` does not merge, and the "returns a new custom setting object … ID set to null" behaviour (supports the Core Concepts merge table in SKILL.md).
- Metadata API Developer Guide (v62 PDF), `CustomObject` — `customSettingsType` (`List` / `Hierarchy`, Hierarchy default), `customSettingsVisibility` (17.0–33.0, superseded), and `visibility` (`Public` default / `Protected` / `PackageProtected`, 34.0+), which supply every element in `references/metadata-examples.md`. https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
- Metadata API Developer Guide (v62 PDF), `SchemaSettings`, `PermissionSet`, `Profile` — `enableAdvancedCSSecurity`, `enableSOSLOnCustomSettings` and `enableListCustomSettingCreation` all defaulting to false, plus `PermissionSetCustomSettingAccesses` / `ProfileCustomSettingAccesses` (47.0+) as the read-access grant (supports the Visibility table in SKILL.md and `references/gotchas.md` §9–10).
- Object Reference for the Salesforce Platform (v62 PDF), *Compound Field Limitations* — "Geolocation fields aren't supported in custom settings" (supports the Decision Guidance row and the checker's Location rule). https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
- Salesforce App Limits Cheat Sheet (v62 PDF), SOQL governor footnote — "This limit doesn't apply to custom metadata types. In a single Apex transaction, custom metadata records can have unlimited SOQL queries" (supports the CMT row of the Governor Limit table).
- Salesforce Well-Architected — Operational Excellence and Reliability framing for the tradeoffs above. https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
