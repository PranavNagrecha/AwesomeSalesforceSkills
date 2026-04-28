# Well-Architected Notes — Fit-Gap Analysis Against Org

## Relevant Pillars

- **Operational Excellence** — Fit-gap is the routing manifest for the rest of the build pipeline. A clean matrix means deterministic handoff to `object-designer`, `flow-builder`, and `apex-builder` without re-litigation per row. A sloppy matrix produces builders that improvise — a failure mode Operational Excellence exists to prevent.
- **Scalability** — The risk-tag taxonomy includes `data-skew` and `customization-debt` precisely because fit-gap is the cheapest place to catch scalability problems. Catching a data-skew pattern at scoring time costs minutes; catching it after build costs months.
- **Reliability** — `license-blocker` and `governance` tags catch row-level reliability issues (a feature the persona literally cannot reach is not reliable, and a row that violates the org's governance pattern destabilizes deployment). The matrix is the first artifact where these surface.

## Architectural Tradeoffs

- **Tier accuracy vs. throughput.** A perfectly-classified matrix takes time. A "good enough" matrix is faster but produces re-work downstream. The break-even is around 80% accuracy: above that, downstream cost dominates; below that, scoring cost dominates. Most projects under-invest in scoring.
- **AppExchange-first vs in-house build.** AppExchange managed packages can collapse Custom rows to Standard, but they introduce vendor risk, license cost, and upgrade-cadence dependencies. The fit-gap notes this explicitly via the `no-AppExchange-equivalent` and `customization-debt` tags.
- **Probing the production org vs probing a sandbox.** Production probing is harder (access control, change-management) but produces a correct matrix. Sandbox probing is easier and produces a matrix that may be wrong by 10–30% of rows.

## Anti-Patterns

1. **No-probe fit-gap.** Producing the matrix from the requirements list alone, without inputs on the target org's edition, license SKUs, installed packages, and existing automation. The matrix is unusable as a build plan.
2. **Tier-three escape avoidance.** Refusing to classify any row as Unfit, instead jamming wrong-platform requirements into Custom. This produces multi-month build efforts that fail in production. Unfit is a healthy classification.
3. **Fit-gap-as-roadmap.** Conflating classification with prioritization. The matrix routes; it does not rank. Prioritization is a separate exercise that consumes the matrix.
4. **No risk tags.** A matrix with empty `risk_tag[]` arrays everywhere is a red flag. Real engagements have a 30–50% tag rate; zero tags means the reviewer skipped the risk pass.

## Official Sources Used

- Object Reference — https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_concepts.htm
- Metadata API Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_intro.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Salesforce Help: Edition Comparison — https://help.salesforce.com/s/articleView?id=sf.overview_edition.htm (canonical authority for what is "Standard" per edition)
- Salesforce Help: User Licenses and Permission Set Licenses — https://help.salesforce.com/s/articleView?id=sf.users_understanding_license_types.htm (license-blocker classification)
- AppExchange Listing Standards — https://appexchange.salesforce.com/listingDetail (currency check for managed-package alternatives)
- Salesforce Architects: Well-Architected Adaptable framework — https://architect.salesforce.com/well-architected/adaptable/intentional (governance + customization-debt framing)
