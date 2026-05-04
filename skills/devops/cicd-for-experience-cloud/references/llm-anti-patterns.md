# LLM Anti-Patterns — CI/CD for Experience Cloud

Mistakes AI coding assistants commonly make when generating Experience
Cloud pipelines. The consuming agent should self-check against this
list before recommending or finalizing pipeline code.

---

## Anti-Pattern 1: Recommending a single `sf project deploy` for the whole package

**What the LLM generates.**

```yaml
- name: deploy everything
  run: sf project deploy start --source-dir force-app --target-org prod
```

**Why it happens.** "Just deploy the project" is the simplest answer
and works for many SFDX projects. It misses Experience Cloud's
metadata-ordering requirements.

**Correct pattern.** Seven-step ordered deploy:

```yaml
- run: sf project deploy start --source-dir force-app/main/default/objects ...
- run: sf project deploy start --source-dir force-app/main/default/permissionsets ...
- run: sf project deploy start --source-dir force-app/main/default/networks ...
- run: sf project deploy start --source-dir force-app/main/default/experiences ...
- run: sf project deploy start --source-dir force-app/main/default/brandingSets ...
- run: bash scripts/assign-guest-permsets.sh prod
- run: bash scripts/smoke-test-site.sh prod
```

**Detection hint.** Any Experience Cloud pipeline with a single
project-wide deploy step is missing the ordering rules.

---

## Anti-Pattern 2: Treating CMS Managed Content as part of the bundle deploy

**What the LLM generates.** Pipeline that deploys ExperienceBundle and
asserts the site has all its content, including articles and images.

**Why it happens.** "Bundle" sounds like it includes everything visual.
The CMS Managed Content / SFDX boundary isn't surfaced unless you
know to look for it.

**Correct pattern.** Two valid models, both explicit in the pipeline:
- Admin-promotion: documented "this pipeline does NOT promote CMS
  content; admins handle it separately."
- Custom export step: separate pipeline job that uses the CMS REST API
  to export from source and import to target.

**Detection hint.** Any Experience Cloud deploy plan that doesn't
mention CMS Managed Content explicitly is missing the question.

---

## Anti-Pattern 3: Forgetting guest-user reconciliation

**What the LLM generates.** Pipeline ends after deploying
ExperienceBundle and BrandingSet — no step that assigns permission
sets to the guest user.

**Why it happens.** "Deploy = done" mental model from non-public-site
SFDX projects.

**Correct pattern.** Every Experience Cloud pipeline includes a
guest-user reconciliation step that:
- Finds the site's guest user (`Profile.Name LIKE '%Site Profile%'`)
- Assigns the required permission sets, idempotent on re-run
- Validates assignments match a baseline before promoting

**Detection hint.** Any pipeline whose last step is "deploy bundle"
or "smoke test" without a guest-user step is going to ship a "no
access" experience for anonymous visitors.

---

## Anti-Pattern 4: Recommending Aura `ExperienceBundle` syntax for an LWR site

**What the LLM generates.** "Deploy your Experience Cloud site with
`sf project deploy start --source-dir force-app/main/default/experiences`."

**Why it happens.** `experiences/` is the Aura-era path; LWR sites
ship under `digitalExperiences/`. Older training data uses the Aura
path.

**Correct pattern.** Match the bundle type to the source-org's site.
LWR → `digitalExperiences/`; Aura → `experiences/`. Verify before
choosing the path.

**Detection hint.** Any LWR-site recipe with `experiences/` in the
deploy path (or vice versa) is wrong by construction.

---

## Anti-Pattern 5: Assuming `sf project deploy` handles custom-domain DNS

**What the LLM generates.** "Deploy `CustomDomain` metadata and your
custom domain is live."

**Why it happens.** "Deploy" is a complete verb in most contexts; the
LLM doesn't surface that DNS is outside Salesforce's control.

**Correct pattern.** Pipeline emits the DNS target as a build
artifact. DNS team applies the CNAME (manually or via their own
automation). A subsequent gate confirms DNS propagation before the
"announce URL" step.

**Detection hint.** Any custom-domain recipe that ends at "metadata
deployed" without a DNS-coordination step is incomplete.

---

## Anti-Pattern 6: Not enabling `ExperienceBundleSettings` on a fresh org

**What the LLM generates.** Setup steps that assume the org is ready
to accept ExperienceBundle deploys without verifying the prerequisite
toggle.

**Why it happens.** First-deploy prerequisites are easy to forget once
they've been done in dev / QA.

**Correct pattern.** Document `ExperienceBundleSettings` enablement
as a one-time-per-org step in the pipeline README. Either include it
as the very first deploy step (idempotent) or have the runbook
explicitly call it out before first run.

**Detection hint.** Any "first time using Experience Cloud in this
org" recipe that doesn't mention `ExperienceBundleSettings` is
missing the prerequisite.

---

## Anti-Pattern 7: Bundle-the-BrandingSet-with-rename pipeline

**What the LLM generates.** "Rename your BrandingSet and redeploy."

**Why it happens.** Renames feel like a single-actor operation; the
LLM doesn't surface that bundles reference BrandingSets by API name
and don't auto-update.

**Correct pattern.** BrandingSet renames are coordinated migrations:
1. Deploy new BrandingSet alongside old.
2. Update each consuming bundle's reference and deploy site-by-site.
3. Delete old BrandingSet only after every consuming site has
   migrated.

**Detection hint.** Any "rename the BrandingSet" plan without
multi-site coordination steps is going to break consuming sites
silently.

---

## Anti-Pattern 8: Putting permset assignment inside the bundle deploy step

**What the LLM generates.** A pipeline step that does
`sf project deploy start ... && sf org assign permset ...` chained
together.

**Why it happens.** Looks like one logical "deploy + configure" unit.
But chaining means a deploy failure doesn't reach the permset step;
also, the chained command is harder to skip / re-run independently.

**Correct pattern.** Separate steps. Deploy step and permset-assignment
step are independent; the latter can be re-run without re-deploying
the bundle.

**Detection hint.** Single pipeline step combining `sf project deploy`
with `sf org assign permset` is mixing concerns.
