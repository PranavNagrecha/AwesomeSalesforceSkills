# Gotchas — Metadata API Retrieve / Deploy

Second-order issues that surface only after the first round of
`sf project retrieve start` / `sf project deploy start` cycles
have happened. The obvious mistakes (wildcards skip standard
objects, `NoTestRun` rejected by prod) are covered in
`llm-anti-patterns.md` and the sibling
`apex/metadata-api-and-package-xml` skill.

---

## Gotcha 1: `<members>*</members>` does NOT include managed-package or "Hidden" metadata

**What happens:** A team runs a wildcard retrieve against a
sandbox to capture "everything" and commits the result to git as
a baseline. An audit later shows the org has 14 installed managed
packages — none represented in source. The Metadata API treats
managed-package components as belonging to the package namespace,
not the subscriber org, so `<members>*</members>` for `ApexClass`,
`CustomObject`, `Layout`, etc. silently excludes anything with a
namespace prefix (`somepackage__SomeClass`). Components flagged
as "Hidden" inside a managed package are completely invisible —
they don't even appear in `sf org list metadata --metadata-type ApexClass`.

**When it occurs:** Any wildcard retrieve from an org with at
least one managed package installed (so: virtually every
production org, given FSL, CPQ, Pardot, Marketing Cloud Connector
are all managed).

**How to avoid:** Add an explicit `installedPackage` block to the
manifest. The manifest captures the package version (not the
contents — those aren't retrievable by subscribers), enough to
reconstruct the org by re-installing those package versions:

```xml
<types>
    <members>FieldServiceLightning</members>
    <members>SBQQ</members>
    <members>pi</members>
    <name>InstalledPackage</name>
</types>
```

Cross-check with `sf package installed list --target-org <alias>`
to enumerate the namespace prefixes that need to appear.

---

## Gotcha 2: The `<version>` tag in `package.xml` gates which metadata types are even eligible

**What happens:** A team copies a 2-year-old `package.xml` to
bootstrap a new repo. The manifest declares `<version>50.0</version>`
(Spring '20). They add a `<types>` entry for `LightningExperienceTheme`
— a type introduced in v52. The retrieve quietly returns no
results for that type; the deploy validates but doesn't actually
create the component. No error. The API version in the request
limits the catalog of metadata types the request can address —
newer types simply aren't in v50's catalog, so they're skipped
silently rather than rejected loudly.

**When it occurs:** Migrating manifests across major releases
without bumping `<version>`. Also bites teams copying snippets
from Stack Exchange answers written for older API versions.

**How to avoid:** Set a repo-wide policy that `<version>` matches
the current production API version. Add a CI lint that greps
`manifest/*.xml` and fails if `<version>` is older than
`current_prod - 2` (a 2-release rolling tolerance). When the org
refreshes, run a one-shot script that bumps `<version>` in every
manifest in the repo. The introduction-version of each metadata
type is documented under the type's entry in the Metadata Types
Reference; check it before adding a new `<types>` block to a
long-lived manifest.

---

## Gotcha 3: Retrieve order is NOT preserved for `Layout`, related-list, and `RecordType` sections — diffs look chaotic

**What happens:** Two retrieves of the same
`Account-Account Layout.layout-meta.xml` file, minutes apart
against the same org with no intervening changes, produce
different files. `<layoutSections>` blocks come back in
non-deterministic order; inside each section, `<layoutColumns>`
and `<layoutItems>` may also re-order. `<relatedLists>` come
back in whatever order the platform internally stored them —
not insertion order, not display order. Same for
`<recordTypeVisibilities>` inside `Profile`. The git diff shows
hundreds of lines of "changed" XML where nothing actually changed.

**When it occurs:** Any team that re-retrieves a previously
captured `Layout`, `RecordType`, `Profile`, or `PermissionSet`
file as part of a CI sync job. Most painful when reviewers see
a 400-line PR diff that's 100% reordering noise plus 3 lines of
real change buried in it.

**How to avoid:** Normalize before commit. Either (a) post-process
retrieved files with a deterministic XML sort (community tool
`sfdx-git-delta` covers some types; in-house Python with
`xml.etree.ElementTree` and recursive `sorted(child, key=...)`
covers the rest) or (b) configure `git diff` to use a structural
diff for `*.layout-meta.xml` via a custom `.gitattributes` + diff
driver. Treat raw retrieve output as a non-canonical serialization;
the canonical form is what your sort script emits.

---

## Gotcha 4: Deploy validation passes at the per-type level — cross-type circular dependencies fail at the actual deploy

**What happens:** A manifest deploys a `CustomField`
(`Account.Tier__c`) that references a `GlobalValueSet`
(`AccountTierValues`), which is curated by a `CustomMetadata`
type (`Account_Tier_Mapping__mdt`) whose records reference back
to `Account.Tier__c`. `sf project deploy validate` succeeds —
the validation phase checks each type's XML schema independently
and resolves dependencies *within* each type, but doesn't fully
resolve cross-type references. Validation reports "green" with
100% tests passing. The `sf project deploy quick` execution
fails because cross-type resolution order picks an ordering where
the `GlobalValueSet` needs the `CustomField` first, but the
`CustomField` needs the `GlobalValueSet` first.

**When it occurs:** Architectures that mix `GlobalValueSet` ↔
`CustomField` ↔ `CustomMetadata`, or `CustomObject` ↔ `Flow` ↔
`ApexClass` cycles. Also a known hazard with `PermissionSet` ↔
`CustomPermission` ↔ custom-field cycles. The "validation passes
/ deploy fails" pattern is the tell.

**How to avoid:** Don't rely solely on `validate` for high-risk
deploys with cross-type dependencies. Either (a) split into a
2-step sequence — deploy the leaf metadata first (e.g., create
`GlobalValueSet` with placeholder values, then create
`CustomField`, then update `GlobalValueSet` to its final shape)
— or (b) use a "smoke test" sandbox that mirrors prod and runs
the actual deploy (not just validate) as a gating step. The
`validate → quick` window is 10 days; you have time to interpose
a real deploy against a preview environment between the validate
and the prod quick-deploy.

---

## Gotcha 5: `deployedFromIde` and the strict-gating rejection

**What happens:** A `sf project deploy start` against prod returns
"Deploys from the IDE are not allowed by this org's deployment
policy." The CI engineer is confused — there's no IDE involved;
this is GitHub Actions. The Metadata API SOAP envelope includes
a `deployedFromIde` boolean flag that the sf CLI sets to `true`
on every deploy (the flag dates to the Force.com IDE and has
been inherited by `sfdx`, then `sf`). Orgs with strict deployment
gating enabled (Setup → Deployment Settings → "Disable
deployments from Salesforce CLI / IDE") reject any deploy where
this flag is `true`, regardless of origin. Older `ant`-based
Migration Tool deploys don't set the flag and work fine.

**When it occurs:** Enterprises that turned on the strict gating
years ago (often by an admin who's since left) and never reviewed
it. Surfaces when the team migrates from change-sets or `ant` to
`sf` CLI pipelines and the new pipeline hits the rejection on
first prod attempt.

**How to avoid:** First, check whether the strict gating is
actually serving a purpose — it predates modern CI patterns and
is usually a relic. If it can be turned off (Setup → Deployment
Settings → uncheck the restriction), that's the cleanest fix; a
git-tracked manifest + CI pipeline is a stronger audit trail
than the flag was ever defending against. If it must stay on for
compliance, drop down to the raw Metadata API (a thin script
using the SOAP `deploy()` call with `deployedFromIde=false`
explicitly) for prod deploys, while keeping `sf` CLI for all
other environments. Document the exception in the runbook so the
next engineer doesn't repeat the diagnosis.
