# Well-Architected Notes — CI/CD for Experience Cloud

## Relevant Pillars

- **Reliability** — The seven-step pipeline shape (foundation →
  Network → bundle → BrandingSet → guest-user → smoke → DNS-emit) is
  the reliability investment. Skipping any step produces a
  deploy-succeeds-but-site-broken failure that's confusing to debug
  and sometimes invisible (anonymous-access errors only show up to
  guests, not to the deploy operator).
- **Operational Excellence** — Treating CMS Managed Content as a
  separate promotion track (instead of pretending it rides with the
  bundle) is the operational-clarity investment. Either model
  (admin-promotion or custom-export) is fine; pretending it's
  bundled isn't.
- **Security** — Guest-user permission set assignment is a security
  control that lives in the pipeline. Without an automated gate,
  guest-user permissions can drift after each refresh, exposing
  more (or less) than intended.

## Architectural Tradeoffs

- **Single pipeline vs theme + per-site pipelines.** Single pipeline
  is simpler to operate; multi-pipeline lets the theme team and
  site-feature teams move at different cadences. The break point is
  roughly 3+ sites sharing a BrandingSet — below that, single
  pipeline; above, split.
- **Custom-domain DNS automation vs manual DNS handoff.** Some
  organizations have API access to their DNS provider; pipeline can
  apply CNAMEs automatically. Others have a DNS team with a manual
  process. Pipeline emits the targets either way; whether the
  apply-step is automated or manual is an org-level decision.
- **Smoke test against live URL vs synthetic session.** Live URL is
  the most realistic check but coupled to DNS / CDN / public
  reachability. Synthetic session (curl with the Salesforce instance
  URL directly) bypasses DNS and validates only the
  Salesforce-side. Best practice: both, sequenced (synthetic first,
  live URL after DNS confirmation).

## Anti-Patterns

1. **Deploy-and-forget guest user.** Bundle deploys do not re-apply
   guest-user permission-set assignments. Pipeline must do it
   explicitly.
2. **Assuming CMS Managed Content rides with the bundle.** It
   doesn't. Choose admin-promotion or custom-export, document the
   choice, don't pretend.
3. **No DNS-confirmation gate.** Metadata-deploy success does not
   mean the site is reachable. Gate the "announce" step on DNS
   confirmation.
4. **Pipeline that mixes Aura `ExperienceBundle` and LWR
   `DigitalExperienceBundle` paths without distinguishing them.**
   Different metadata types; different source directories; different
   bundle internals.
5. **Renaming a BrandingSet without coordinating with consuming
   sites.** Breaks every site that references the old API name.

## Official Sources Used

- ExperienceBundle (Aura) — Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_experiencebundle.htm
- DigitalExperienceBundle (LWR) — Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_digitalexperiencebundle.htm
- BrandingSet — Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_brandingset.htm
- ExperiencePropertyTypeBundle — Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_experiencepropertytypebundle.htm
- Network — Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_network.htm
- Salesforce CLI Reference — https://developer.salesforce.com/docs/atlas.en-us.sfdx_cli_reference.meta/sfdx_cli_reference/cli_reference.htm
- Sibling skill (bundle internals) — `skills/devops/experience-cloud-deployment-dev/SKILL.md`
- Sibling skill (generic SFDX CI/CD) — `skills/devops/sfdx-cicd-pipeline/SKILL.md` (where one exists)
