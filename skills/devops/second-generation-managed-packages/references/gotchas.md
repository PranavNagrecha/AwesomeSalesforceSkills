# Gotchas — Second-Generation Managed Packages

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

---

## Gotcha 1: `--code-coverage` Omission Creates an Unpromotable Version — Forever

**What happens:** Running `sf package version create` without the `--code-coverage` flag produces a valid beta package version (with a 04t ID) that installs correctly. Everything appears normal. When the team attempts to promote the version with `sf package version promote`, the CLI returns an error: the version has no coverage data and cannot be promoted. There is no way to add coverage data retroactively to an existing package version — the version is permanently unpromotable.

**When it occurs:** Any time `--code-coverage` is omitted during `sf package version create`. This commonly happens when developers optimize for fast iteration cycles and only add the flag "before release." Once the build artifact is created without the flag, it is too late.

**How to avoid:** Always include `--code-coverage` in any version creation command that might be promoted. In CI/CD pipelines, separate fast-iteration jobs (no `--code-coverage`) from release-candidate jobs (`--code-coverage` always on). Treat the release-candidate job as the source of the 04t ID used in promotion — never promote a version that was not built with coverage.

---

## Gotcha 2: Package-to-Dev-Hub Association Is Permanent and Cannot Be Transferred

**What happens:** Once a managed 2GP package is created against a Dev Hub org, it is permanently associated with that org. The Dev Hub org instance determines where the package lives. If the Dev Hub org becomes unavailable — due to expiry (Developer Edition), org decommission, or losing ISV partner status — the package becomes inaccessible. Installed packages in subscriber orgs cannot receive version updates. New installs of any version associated with the orphaned Dev Hub fail. Salesforce support cannot transfer package ownership between Dev Hub orgs.

**When it occurs:** ISVs who use a Developer Edition org as their Dev Hub "just to try it out" and then build packages they intend to distribute. Developer Edition orgs expire on inactivity; once expired, package metadata stored against that Dev Hub is no longer accessible. This also occurs when a company is acquired and needs to migrate its Salesforce partner relationship to a new PBO — package assets cannot follow.

**How to avoid:** Always designate the Partner Business Org (PBO) as the Dev Hub before creating any production-intent managed package. The PBO is a production org maintained by Salesforce for active partners and does not expire. If experimenting, use a disposable namespace in a Developer Edition org and never distribute beta versions of those packages to real subscribers.

---

## Gotcha 3: Subscriber Orgs See Obfuscated Apex — Debugging Through Subscriber Support Console Only

**What happens:** Apex classes, triggers, and Visualforce components inside a managed 2GP package are obfuscated in subscriber orgs. Subscribers and their admins cannot read source code. When a subscriber reports an exception stack trace or a runtime error, the class names and method signatures are visible but the implementation is not. Partners who attempt to debug using standard debugging tools in a subscriber org (e.g., Developer Console, Debug Logs) can see call stacks but not source lines. This is intentional IP protection, but it catches ISVs off guard when troubleshooting subscriber-reported issues.

**When it occurs:** Any time a subscriber org user or admin tries to read, inspect, or debug managed package Apex. Partners themselves encounter this if they log in to a subscriber org using standard user credentials rather than the Subscriber Support Console.

**How to avoid:** Use the Subscriber Support Console (available to ISV partners via the License Management App) to view unobfuscated Apex when debugging subscriber issues. Build comprehensive diagnostic tools — custom objects, platform events, debug-level custom metadata — inside the package so that runtime state is observable without source visibility. Design error messages and exception payloads to be self-describing, since subscribers cannot trace the implementation that produced them.

---

## Gotcha 4: Namespace Linkage Is Irreversible — Choose Namespaces Carefully

**What happens:** When a namespace is registered in a Developer Edition org and linked to a Dev Hub, that association is permanent. The namespace cannot be unlinked, transferred to a different Dev Hub, or reused in another org. If a practitioner links a "real" production namespace to a throwaway Dev Hub, or links the wrong namespace to the production Dev Hub, there is no self-service recovery. Salesforce support cannot reassign namespaces.

**When it occurs:** Practitioners who are experimenting with 2GP and use their intended production namespace in a test setup. Once linked, the namespace is bound to that Dev Hub org and all packages created under it carry that namespace forever.

**How to avoid:** Use a clearly disposable, throwaway namespace (e.g., `testns99`) when learning or prototyping. Reserve the intended production namespace for the production PBO Dev Hub setup. Salesforce's own documentation explicitly warns: "Choose namespaces carefully. If you're trying out this feature or need a namespace for testing purposes, choose a disposable namespace."

---

## Gotcha 5: Patch Versions Cannot Be Created Before the Parent Major.Minor Is Converted (in 1GP→2GP Migrations)

**What happens:** During a 1GP-to-2GP migration, if a team needs a patch version of an unconverted 1GP major.minor (e.g., `4.1.1` when `4.1.0` has not yet been converted to 2GP), the conversion fails. The `sf package convert` command requires the parent major.minor version to be converted first. Teams that defer major.minor conversions while continuing to ship 1GP patch versions can box themselves into a conversion sequencing problem.

**When it occurs:** ISVs who are in the middle of a 1GP→2GP migration and are still issuing 1GP patch releases concurrently. If patch `4.1.1` is needed as a 2GP version but `4.1.0` was never converted, the convert command for `4.1.1` (which requires the `--patch-version` flag) will fail.

**How to avoid:** Before beginning 2GP migration, map out all supported major.minor versions still receiving patches. Convert each major.minor before attempting to convert any of its patch versions. Follow the phased migration approach: convert the minimum required set of major.minor versions before cutting over to 2GP development entirely.
