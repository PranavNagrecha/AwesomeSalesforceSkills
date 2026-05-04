# Gotchas — CI/CD for Experience Cloud

Non-obvious behaviors that bite real Experience Cloud pipelines.

---

## Gotcha 1: CMS Managed Content is not covered by SFDX

**What happens.** A pipeline that deploys ExperienceBundle assumes
the bundle's CMS content travels with it. Articles, images, video
assets — all live in CMS Managed Content, which is a separate
storage layer. Bundle deploys reference CMS items by content ID; if
the content doesn't exist in target, the bundle renders broken
widgets.

**When it occurs.** First production deploy after the source org has
real CMS content; or after a sandbox refresh that didn't include CMS.

**How to avoid.** Two valid models:
- **Admin-promotion:** content authors publish to production
  directly; the pipeline never touches CMS. Document this
  explicitly in pipeline READMEs so nobody assumes the bundle
  carries content.
- **Custom export step:** use the CMS REST API to export articles
  from source and import to target as a separate pipeline job.
  Heavier; appropriate when content volume justifies it.

---

## Gotcha 2: Guest-user permission sets reset on sandbox refresh

**What happens.** A sandbox is refreshed from production. The site is
still there, the bundle is still there, but the guest user's
permission-set assignments have been cleared. Anonymous visitors see
"no access" errors.

**When it occurs.** Every sandbox refresh / org copy. Also the first
time a new site is deployed to an environment where someone forgot
to set up the guest user.

**How to avoid.** Pipeline step that re-applies guest-user permission
sets, idempotent. Plus a CI gate (Pattern C in SKILL.md) that
validates the assignments match a known baseline post-deploy.

---

## Gotcha 3: Network metadata must deploy before the ExperienceBundle

**What happens.** Pipeline deploys the ExperienceBundle first, then
the Network metadata. Bundle deploy fails with "Network not found"
or "Site not found"; OR succeeds-but-doesn't-work because the bundle
is stranded without a site to attach to.

**When it occurs.** Pipelines that don't explicitly order metadata
types — relying on SFDX's default ordering, which doesn't always
sequence Network before bundle.

**How to avoid.** Explicit ordered deploy steps in the pipeline.
Pattern A in SKILL.md shows the seven-step shape. Network is step 2,
bundle is step 3.

---

## Gotcha 4: `ExperienceBundle` (Aura) and `DigitalExperienceBundle` (LWR) are different metadata types

**What happens.** Pipeline copies a recipe for `ExperienceBundle`
deploys and applies it to an LWR site. Source paths are wrong;
deploy doesn't find any artifacts to deploy; "succeeds" with zero
changes. Or vice versa — LWR pipeline against an Aura site.

**When it occurs.** Migrating from Aura to LWR, or vice versa, or
copying a pipeline from one site to another that's a different
type.

**How to avoid.** Match the bundle type explicitly:
- LWR: `force-app/main/default/digitalExperiences/`
- Aura: `force-app/main/default/experiences/`

Source path matters; the SFDX deploy command targets a directory
of bundle artifacts.

---

## Gotcha 5: Custom-domain registration requires manual DNS verification

**What happens.** Pipeline deploys `CustomDomain` metadata. Domain
appears in Setup → Domains. The site is "bound" to the domain. But
the domain doesn't resolve — DNS hasn't been updated, or the
domain-ownership verification step hasn't been completed.

**When it occurs.** Production deploys for new domains; rebinding
existing domains during M&A or rebrands.

**How to avoid.** Pipeline emits the Salesforce-supplied DNS target
as a build artifact. The DNS team applies the CNAME. A subsequent
pipeline step (manual approval gate, ServiceNow record, GitHub
environment-protection rule) gates the "announce URL" step on DNS
confirmation. Don't assume metadata-deploy = reachable site.

---

## Gotcha 6: `ExperienceBundleSettings` must be enabled in target before any bundle deploys

**What happens.** First-ever ExperienceBundle deploy to a freshly-created
org / sandbox fails with "ExperienceBundle deploys are not enabled.
Enable them in Setup → Digital Experiences → Settings."

**When it occurs.** New sandboxes, scratch orgs, or any org that's
never had the toggle flipped.

**How to avoid.** One-time-per-org enablement step documented in the
pipeline README. Either deploy `ExperienceBundleSettings` metadata
explicitly as the very first step, or have a runbook entry that says
"before first pipeline run on a new org, enable ExperienceBundleSettings
in Setup."

---

## Gotcha 7: Renaming a BrandingSet API name breaks every site that references it

**What happens.** Theme team renames `CorpBrand_2024__c` →
`CorpBrand_2025__c`. Sites that reference it by API name still point
at the old name; bundles deploy successfully but visual styling is
gone. Pages render unstyled.

**When it occurs.** Naming-convention migrations, BU rebrands.

**How to avoid.** BrandingSet renames are coordinated migrations:
1. Deploy the new BrandingSet alongside the old (both exist in target).
2. Each consuming site updates its bundle to reference the new name and deploys.
3. After all sites have migrated, delete the old BrandingSet.

The rename never "flows through" the system automatically; coordination
across all consuming sites is unavoidable.

---

## Gotcha 8: BrandingSet promotion order matters when the BrandingSet is used by the same package

**What happens.** Bundle and its BrandingSet are in the same metadata
package; SFDX deploys them in default order; bundle deploys before
BrandingSet, references a token that doesn't exist yet, fails or
renders without theme.

**When it occurs.** Greenfield site setup where the same release
introduces both the bundle and its theme.

**How to avoid.** Either two-step deploy (BrandingSet first, then
bundle in a second `sf project deploy start` call) — the cleanest —
or rely on SFDX's default ordering being correct (sometimes is,
sometimes isn't, depends on version). Two-step is safer.

---

## Gotcha 9: Test runs in CI can hit production-rate limits on guest queries

**What happens.** A smoke-test step that hits the site URL via curl,
multiplied across multiple environments, can hit per-IP / per-org
rate limits if the CI runner pool shares an IP.

**When it occurs.** Multi-environment pipelines (dev / QA /
staging / prod) running smoke tests in parallel.

**How to avoid.** Stagger smoke tests; limit concurrent CI jobs to
one per target org; or run the smoke test against a synthetic
session rather than the live URL.
