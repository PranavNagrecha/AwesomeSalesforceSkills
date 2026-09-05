# Well-Architected Notes — Managed Package Installation And Upgrade

## Relevant Pillars

- **Operational Excellence** — Subscriber-side package installs are a recurring change-management event with predictable failure modes. A repeatable runbook that progresses Developer Sandbox → Full Sandbox → Production replaces ad-hoc "install on Friday" decisions with audit-traceable execution. Operational maturity around package installs reduces both incident rate and mean-time-to-recovery when an install does fail.
- **Security** — The install audience choice and the access-grant mechanism (profile-baked vs. Permission Set Group) materially affect the principle of least privilege. Install for All Users grants are durable and hard to reverse; the modern Permission Set Group path is reversible and auditable. Direct (non-AppExchange) install URLs may not have passed Security Review and warrant a published security justification before install.
- **Reliability** — The 48-hour Salesforce-side data retention window on uninstall is the only built-in undo for package-introduced data. Subscriber-driven pre-export to durable storage is the difference between "we can recover" and "the data is gone." Push-patch upgrades arrive with publisher-set timing — monitoring publisher release notes is the reliability prerequisite for stable production behavior.

## Architectural Tradeoffs

- **Sandbox depth vs. release-train velocity.** Installing in Developer Sandbox → Full Sandbox → Production catches more issues but extends the install window from hours to days. Patch versions usually justify the shorter (sandbox-skipped) path; minor and major versions almost never do. The decision criterion is the publisher's release-note delta — if the release notes include any rename, required-field addition, or Flow version replacement, take the full sandbox path.
- **Install for Admins Only + Permission Set Group vs. Install for All Users.** The latter is faster at install time and removes a post-install grant step. It also embeds the access grant in every affected profile, making revocation a per-profile edit and breaking the org's principle-of-least-privilege baseline. The former is reversible, auditable, and survives uninstalls (subscriber-org Permission Sets do; bundled Permission Sets don't).
- **Pre-staging Named Credential secrets vs. post-staging.** Some packages assume the InstallHandler will configure auth; the InstallHandler cannot set client secrets because they're not known at install time. Pre-staging the External Credential principal before install lets InstallHandler reference it cleanly; post-staging requires admins to know the exact post-install field names. Publisher documentation often omits this decision.
- **Certified vs. non-certified, decided before install rather than after.** A certified package brings its own per-transaction governor budget; a non-certified one spends yours. On an object where the package's automation and your own both fire, that is the difference between two independent 100-query budgets and one shared budget you no longer control. Certification also gates whether push upgrades are possible at all. The tradeoff is real — a non-certified package may still be the right tool — but it must be priced into the limits headroom of every transaction the package participates in, not discovered when your trigger starts throwing.
- **Clicking the install vs. deploying it as source.** A UI install is faster and shows the components screen. A source-tracked `installedPackage` file is reviewable, diffable, promotable through environments, and lintable — and it forces `securityType` and `activateRSS` to be written down rather than defaulted. The cost is that the install becomes its own pipeline stage, because the metadata type cannot share a manifest with anything else, and the type does not cover 2GP or unlocked packages at all.

## Anti-Patterns

1. **Production-first install.** Skipping sandbox install because "the vendor says it's safe" — the most common cause of post-install support tickets. Vendors test on their orgs, not yours.
2. **Trusting Install for All Users.** Bakes access into profile settings, making the grant non-reversible without per-profile edits. Permission Set Groups are the modern, reversible alternative.
3. **Uninstall without pre-export.** Trusts the 48-hour Salesforce-side retention as a recovery mechanism. The retention is a sanity check; durable pre-export to subscriber storage is the actual recovery path.
4. **No push-upgrade monitoring, and no answer on whether push is even blockable here.** Subscribers learn about a version change from deployment failures or user complaints. The mitigation is monitoring the publisher's release-note channel as a release-train input, and asking each publisher whether push is enabled for your org and whether they honour a block — `PackageSubscriber.HasRestrictionEnabled` defaults to `false`, so "not blocked" is the default state rather than a decision anyone made.
5. **Letting the install defaults decide the audience.** The Metadata API defaults `securityType` to `AllUsers` and the CLI defaults it to `AdminsOnly`. An install artefact that omits the field has made a security decision without recording one, and the decision changes depending on which tool runs it.
6. **Treating a successful install as a working install.** Seats are not permissions, `activateRSS` defaults to off, and the publisher's install script can leave an asynchronous callout in flight after the install commits. Verification is three checks — version, seats, canary user — not a green deploy result.
7. **An installed package with no named owner.** Licences expire, publishers pivot, and release notes go to an address nobody reads. An unowned package is a scheduled outage with no date on it yet.

## Official Sources Used

- **Metadata API Developer Guide** (Summer '26 / v62 PDF extract, `api_meta.txt`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/api_meta.pdf
  - `InstalledPackage` type: 1GP-only scope, `installedPackages/<ns>.installedPackage` file location, the required `versionNumber` and `activateRSS` fields, `securityType` defaulting to `AllUsers`, the single-metadata-type manifest rule and the 20-package deployment cap (L81389–81462) — supports the Security and Reliability pillar notes and the "implicit defaults" anti-pattern below
  - `Package` type: `apiAccessLevel` (`Unrestricted` / `Restricted`, restrictable by the installing admin after install), `postInstallClass`, `uninstallClass`, `namespacePrefix` (L94260–94326) — supports the least-privilege tradeoff
  - Managed Component Access: the eight component kinds whose permissions are deployable, and "wildcards aren't supported" for namespaced grants (L2431–2469) — supports the Permission Set maintenance cost in the tradeoff section
  - Namespace prefix definition, 1–15 alphanumeric characters, case-insensitive (L22290–22294) — supports the checker's namespace validation
- **Object Reference for the Salesforce Platform** (Summer '26 / v62 PDF extract, `object_reference.txt`) — https://resources.docs.salesforce.com/262/latest/en-us/sfdc/pdf/object_reference.pdf
  - `PackageLicense` (read-only; `AllowedLicenses`, `UsedLicenses`, `ExpirationDate`, `Status` ∈ Active/Expired/Free/Trial) and `UserPackageLicense` (`create()`/`delete()`; `LICENSE_LIMIT_EXCEEDED`) at L207540–207690 and L300772–300866 — supports the Reliability claim that seats and permissions are separate failure modes
  - `PackagePushRequest`, `PackagePushJob`, `PackageSubscriber` (`HasRestrictionEnabled`, `CustomUpgradeType = BlockedBySubscriber`, `OrgStatus`, scheduling is approximate) at L208013–208352 — supports the corrected push-upgrade posture in the Reliability pillar
  - `MetadataPackageVersion.ReleaseState` (`Beta` / `Released`), visible only in the publisher's org (L182729–182835) — supports the beta-in-production caution
- **Apex Reference Guide** (Summer '26 extract, `apexrefguide.txt`) — `InstallHandler` / `InstallContext` (L217773–217930) and `UninstallHandler` / `UninstallContext` (L242362–242400): the script runs as a special system user representing the package, `installerId()` is the only handle on the admin, a failed install script aborts the install while a failed uninstall script does not stop the uninstall, and errors route to the publisher's Notify on Apex Error address — supports the Operational Excellence claim that install diagnostics are not fully visible to the subscriber
- **Salesforce Developer Limits and Allocations Quick Reference** (`salesforce_app_limits_cheatsheet.txt` L189–249) — certified managed packages receive their own per-transaction limits; non-certified packages do not; cumulative cross-namespace ceilings are 11× the per-namespace limit; heap, CPU time, transaction execution time, and unique-namespace count are shared — supports the certification tradeoff below
- **Salesforce CLI** `sf package install --help`, `sf package installed list --help`, `sf package uninstall --help`, `@salesforce/cli/2.149.9` — `--security-type` defaults to `AdminsOnly`, `--upgrade-type` and `--apex-compile` are unlocked-package-only, and `sf package uninstall` is documented as second-generation only with 1GP removal routed to Setup — supports the "two paths, opposite defaults" claim
- **Salesforce Well-Architected** — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html (pillar framing for this file)

Retained from this skill's original authoring, supporting the 48-hour uninstall export window, the
install audience behaviour, and the post-install script contract:

- First-Generation Managed Packaging Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/sharing_apps.htm
- Installing Packages (subscriber behaviour) — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/install_or_uninstall_a_package.htm
- Run Apex on Package Install/Upgrade — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/apex_post_install_script.htm
- Uninstall a Package and Delete Components — https://developer.salesforce.com/docs/atlas.en-us.pkg1_dev.meta/pkg1_dev/uninstall_package.htm

Three claims in this skill rest on those four `pkg1_dev` pages rather than on the PDF extracts, and
could not be re-confirmed: the 48-hour uninstall export retention, the three-radio-button install
audience UI, and "a beta version cannot be installed in production." Each carries its own
UNVERIFIED marker at the point of use — `references/gotchas.md` Gotcha 1 and Gotcha 4, and the
`Salesforce-Specific Gotchas` list in `SKILL.md` — rather than only here.
