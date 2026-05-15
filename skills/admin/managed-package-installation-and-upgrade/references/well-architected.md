# Well-Architected Notes — Managed Package Installation And Upgrade

## Relevant Pillars

- **Operational Excellence** — Subscriber-side package installs are a recurring change-management event with predictable failure modes. A repeatable runbook that progresses Developer Sandbox → Full Sandbox → Production replaces ad-hoc "install on Friday" decisions with audit-traceable execution. Operational maturity around package installs reduces both incident rate and mean-time-to-recovery when an install does fail.
- **Security** — The install audience choice and the access-grant mechanism (profile-baked vs. Permission Set Group) materially affect the principle of least privilege. Install for All Users grants are durable and hard to reverse; the modern Permission Set Group path is reversible and auditable. Direct (non-AppExchange) install URLs may not have passed Security Review and warrant a published security justification before install.
- **Reliability** — The 48-hour Salesforce-side data retention window on uninstall is the only built-in undo for package-introduced data. Subscriber-driven pre-export to durable storage is the difference between "we can recover" and "the data is gone." Push-patch upgrades arrive with publisher-set timing — monitoring publisher release notes is the reliability prerequisite for stable production behavior.

## Architectural Tradeoffs

- **Sandbox depth vs. release-train velocity.** Installing in Developer Sandbox → Full Sandbox → Production catches more issues but extends the install window from hours to days. Patch versions usually justify the shorter (sandbox-skipped) path; minor and major versions almost never do. The decision criterion is the publisher's release-note delta — if the release notes include any rename, required-field addition, or Flow version replacement, take the full sandbox path.
- **Install for Admins Only + Permission Set Group vs. Install for All Users.** The latter is faster at install time and removes a post-install grant step. It also embeds the access grant in every affected profile, making revocation a per-profile edit and breaking the org's principle-of-least-privilege baseline. The former is reversible, auditable, and survives uninstalls (subscriber-org Permission Sets do; bundled Permission Sets don't).
- **Pre-staging Named Credential secrets vs. post-staging.** Some packages assume the InstallHandler will configure auth; the InstallHandler cannot set client secrets because they're not known at install time. Pre-staging the External Credential principal before install lets InstallHandler reference it cleanly; post-staging requires admins to know the exact post-install field names. Publisher documentation often omits this decision.

## Anti-Patterns

1. **Production-first install.** Skipping sandbox install because "the vendor says it's safe" — the most common cause of post-install support tickets. Vendors test on their orgs, not yours.
2. **Trusting Install for All Users.** Bakes access into profile settings, making the grant non-reversible without per-profile edits. Permission Set Groups are the modern, reversible alternative.
3. **Uninstall without pre-export.** Trusts the 48-hour Salesforce-side retention as a recovery mechanism. The retention is a sanity check; durable pre-export to subscriber storage is the actual recovery path.
4. **No push-patch monitoring.** Subscribers learn about patch upgrades from deployment failures or user complaints. The mitigation is monitoring the publisher's release-note channel as part of the org's release-train inputs.

## Official Sources Used

- First-Generation Managed Packaging Developer Guide v66.0 — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/sharing_apps.htm
- Installing Packages (Subscriber Behavior) — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/install_or_uninstall_a_package.htm
- Run Apex on Package Install/Upgrade — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/apex_post_install_script.htm
- ISVforce Guide v66.0 — https://developer.salesforce.com/docs/atlas.en-us.packagingGuide.meta/packagingGuide/packaging_intro.htm
- Uninstall a Package and Delete Components — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/uninstall_package.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
