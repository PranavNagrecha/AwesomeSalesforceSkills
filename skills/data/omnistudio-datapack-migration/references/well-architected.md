# Well-Architected Notes — OmniStudio DataPack Migration

## Relevant Pillars

- **Reliability** — Silent skips (ALREADY_EXISTS) and missing --activate are the two most common DataPack migration failures that cause undetected production issues; pre-import version checks and post-import active version verification are mandatory reliability controls.
- **Operational Excellence** — DataPack migrations without version increment discipline accumulate silent state drift between environments; version number governance must be established before the first migration cycle.
- **Security** — DataPacks contain component logic that runs as the invoking user; reviewing exported DataPack content before importing to production is a security control to prevent unauthorized logic being migrated.
- **Performance** — DataPack imports of large component sets should be batched; very large single DataPack files (many components in one JSON) can cause timeout errors during import.
- **Scalability** — Organizations with many OmniStudio components should establish naming conventions and version tagging before migration workflows become complex.

## Architectural Tradeoffs

**Version increment discipline vs overwrite flag:** Incrementing the version number before each migration is the cleanest approach — it creates an auditable version history and avoids silent skips. Using `--overwrite` is faster but does not increment the version trail and can mask repeated migration failures. Teams with high-frequency deployments should establish a version increment policy.

**Active-only export vs all-versions export:** Active-only export is appropriate for production promotion workflows where only live-tested components are promoted. All-versions export is appropriate for UAT environments where draft work must be visible. Using the wrong mode silently omits content.

**DataPack migration vs CI/CD pipeline:** For teams with regular deployment cadences, DataPack migrations should be embedded in a CI/CD pipeline (see omnistudio/omnistudio-ci-cd-patterns) rather than run manually. Manual DataPack migrations are error-prone due to the silent-skip and missing-activate gotchas.

## Anti-Patterns

1. **packDeploy without --activate** — Deploying without the activate flag is the most common migration mistake. The import appears successful but the active version in the target org is not changed. Always include `--activate` when the intent is to make the migrated version live.

2. **No pre-import version collision check** — Skipping the pre-import query to detect existing version numbers leads to silent ALREADY_EXISTS no-ops that are not discovered until users report seeing the old version.

3. **Conflating OMA with DataPack migration** — Using the OmniStudio Migration Assistant (OMA) for org-to-org migrations when OMA is specifically designed for managed-package-to-Standard-Runtime conversion. These are distinct tools.

## Official Sources Used

- OmniStudio DataPacks — https://help.salesforce.com/s/articleView?id=sf.os_datapacks.htm
- DataPacks and Data Migration with Versioning — https://help.salesforce.com/s/articleView?id=sf.os_datapacks_migration.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html

## Cross-Skill References

- `omnistudio/omnistudio-ci-cd-patterns` — pipeline automation of DataPack deployments
- `omnistudio/omnistudio-deployment-datapacks` — DataPack deployment configuration and CLI setup
