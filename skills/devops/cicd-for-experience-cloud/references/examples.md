# Examples — CI/CD for Experience Cloud

## Example 1 — Pipeline ships, site loads, anonymous access fails

**Context.** First production deploy of a partner portal. The pipeline
runs clean — green check on every step. A partner navigates to the
URL: site loads, but every page shows "You don't have permission to
view this record". Engineering scrambles.

**Wrong cause assumed.** "Permission set deployment failed."

**Actual cause.** Pipeline deployed `ExperienceBundle` and the
permission-set metadata, but never *assigned* the relevant permission
sets to the site's guest user. Bundle deploys do not re-apply
permission-set assignments — they assume the target's guest user is
already configured.

**Right answer.** Add an explicit guest-user reconciliation step:

```bash
# scripts/assign-guest-permsets.sh
set -eu
TARGET=$1
GUEST_USERNAME=$(sf data query --target-org "$TARGET" --json --query \
    "SELECT Username FROM User WHERE Profile.Name LIKE '%Partner Portal Profile%' AND IsActive=TRUE LIMIT 1" \
    | jq -r '.result.records[0].Username')

for ps in Site_Public_Read Site_Lookup_Access Site_FAQ_Access; do
    sf org assign permset --target-org "$TARGET" \
        --on-behalf-of "$GUEST_USERNAME" --name "$ps" || true
done
```

The `|| true` makes the script idempotent — re-running on an
already-assigned guest user doesn't fail.

---

## Example 2 — BrandingSet renamed; every site breaks

**Context.** Theme team renamed the corporate BrandingSet from
`CorpBrand_2024__c` to `CorpBrand_2025__c` to align with a new naming
convention. Six sites that referenced it deploy fine in their next
release — but the brand colors / logo on production are gone. White
unstyled pages.

**What went wrong.** ExperienceBundle metadata references the
BrandingSet by API name. The renamed BrandingSet was deployed, but
the bundles still reference the old API name. Production target has
both BrandingSets briefly (or worse, neither), and the bundle's
dangling reference falls through to default styling.

**Right answer.** Treat BrandingSet renames as **coordinated
migrations**:

1. Theme team announces the rename plan to consuming sites with a
   deadline.
2. New BrandingSet (`CorpBrand_2025__c`) is deployed alongside the
   old one. Both exist in production for a transition window.
3. Each consuming site updates its bundle metadata to reference the
   new API name and deploys.
4. Once all consuming sites are on the new BrandingSet, the old one
   is deleted in a final release.

Site-by-site coordination is unavoidable; the rename itself doesn't
flow through automatically.

---

## Example 3 — Custom-domain deploy looks done, but site is unreachable

**Context.** Pipeline deployed `CustomDomain` and `CustomSite`
metadata. Setup → Domains shows the new domain bound to the site.
Marketing announces the new URL. Customers report the site doesn't
load.

**What went wrong.** Salesforce-side metadata is correct — but DNS
hasn't been updated. The custom domain (`portal.example.com`) doesn't
resolve to the Salesforce-supplied target. The pipeline's job
reported "deploy succeeded" because metadata deployment succeeded; it
didn't know about DNS.

**Right answer.** Pipeline emits the DNS target as a build artifact;
a downstream gate requires DNS confirmation before announcing the
URL.

```bash
# scripts/emit-dns-targets.sh
set -eu
TARGET=$1
sf data query --target-org "$TARGET" --json --query \
    "SELECT MasterLabel, Domain, CnameTarget FROM Domain WHERE Domain != ''" \
    | jq -r '.result.records[] | "\(.Domain) → \(.CnameTarget)"' \
    > dns-targets.txt

cat dns-targets.txt
echo ""
echo "DNS team: apply these CNAMEs, then signal the next pipeline step."
```

The DNS team applies the CNAMEs and signals the pipeline (manual
approval, GitHub deployment review, ServiceNow change-record). The
"announce URL" step is gated on that signal.

---

## Example 4 — `ExperienceBundleSettings` not enabled; first deploy fails

**Context.** First-ever ExperienceBundle deploy to a freshly-created
sandbox. Pipeline fails at step 3 with: "ExperienceBundle deploys
are not enabled. Enable them in Setup → Digital Experiences →
Settings."

**What went wrong.** `ExperienceBundleSettings` is an org-level toggle
that must be enabled before *any* ExperienceBundle deploys. New orgs
don't have it enabled by default.

**Right answer.** Add a one-time-per-org Apex anonymous block (or
`ExperienceBundleSettings` metadata deploy) as a prerequisite step
documented in the pipeline README. The pipeline itself doesn't try
to enable it on every run (it's idempotent, but the failure mode is
clearer if a human enables it once than if the pipeline retries
silently).

---

## Anti-Pattern: Treating CMS Managed Content as part of the bundle deploy

```yaml
- name: deploy bundle (assumes CMS content rides along)
  run: sf project deploy start --source-dir force-app/main/default/experiences --target-org prod
```

**What goes wrong.** The bundle deploys; pages reference CMS articles
by content ID; the articles don't exist in target. Pages render with
broken content widgets. Marketing notices once they look at the site.

**Correct.** Treat CMS Managed Content as a separate promotion track.
Either:

- **Admin-promotion model:** content authors publish in production
  directly, and pipelines never deploy CMS content. Documented:
  "this pipeline does NOT promote CMS content; admins handle it
  separately."
- **Custom export step:** use the CMS REST API to export articles
  from source and import to target as a separate pipeline job.
  More work, but enables full automation.

Either is fine; pretending the bundle deploy carries CMS content is
wrong by construction.
