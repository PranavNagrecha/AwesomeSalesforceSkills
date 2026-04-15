# Well-Architected Notes — Industries Cloud Selection

## Relevant Pillars

- **Trusted** — The primary trust concern in vertical cloud selection is license gating: standard industry objects are only available in licensed orgs. An architecture that assumes object availability without a license PSL is an untrusted architecture — it will fail in any environment where the license is absent. Trusted selection requires confirming object availability in a licensed sandbox before any development commitment.

- **Adaptable** — Vertical cloud selection decisions have long-term adaptability consequences. Choosing to implement a solution with custom objects instead of licensed vertical cloud standard objects locks the customer into a bespoke data model that cannot absorb future Salesforce Industries product evolution. Choosing the correct vertical cloud standard objects aligns the data model with Salesforce's roadmap and makes future feature adoption (new pre-built OmniStudio components, AI features, regulatory packs) lower-cost. The OmniStudio managed-package-to-platform-native migration decision carries irreversibility that directly constrains future adaptability.

- **Easy** — The correct vertical cloud selection reduces implementation complexity by providing pre-built standard objects, pre-built OmniStudio component libraries, and industry-standard data models. An incorrect selection (wrong vertical, insufficient licenses) increases complexity: every pre-built component that depends on the missing standard objects must be reimplemented as custom development. Ease is maximized by selecting the vertical cloud whose standard object coverage most closely matches the solution requirements.

## Architectural Tradeoffs

**Standard objects vs custom objects:** Industry standard objects carry pre-built platform behavior, relationships, integration hooks, and upgrade compatibility. Custom objects that replicate the same entities require ongoing maintenance and do not receive Salesforce product investment. The tradeoff is license cost against custom build cost and technical debt. For any implementation that will run more than three years, the standard object path is almost always lower total cost.

**Single vertical vs multi-vertical licensing:** Some customer needs span multiple vertical cloud data models (e.g., a bank with an insurance subsidiary). The architecturally correct answer is multi-cloud licensing — both vertical cloud licenses in the same org. This is a supported and documented configuration. The alternative (building the second vertical's objects as custom objects) sacrifices upgrade compatibility and product alignment for a one-time license cost reduction.

**Platform-native OmniStudio vs managed package:** For new orgs on Spring '26+, platform-native OmniStudio is the only model and is not a tradeoff. For existing orgs on managed-package OmniStudio, the migration to platform-native improves Metadata API deployability and source control integration but carries the one-way migration constraint. The tradeoff is migration effort and irreversibility against long-term DevOps and deployment benefits.

## Anti-Patterns

1. **Selecting a vertical cloud by industry name rather than data model requirements** — Recommending Financial Services Cloud because the customer is "in financial services" without checking which specific standard objects are required leads to licensing mismatches. If the customer requires `InsurancePolicy`, FSC alone is insufficient. Object-first selection prevents this anti-pattern.

2. **Treating Industries licensing as all-or-nothing** — Assuming that purchasing any Salesforce Industries product grants access to all vertical cloud standard objects. Each vertical cloud is a separately licensed product. A solution requiring objects from two vertical clouds requires two separate licenses. Confirming the full license scope per object requirement during selection prevents mid-project re-licensing surprises.

3. **Deferring OmniStudio packaging model decision** — Starting OmniStudio component development without confirming whether the org uses platform-native or managed-package OmniStudio. Developing components in the wrong model and later migrating is expensive; migrating managed-package components to platform-native is one-way and irreversible. The packaging model decision must be made and documented before the first component is built.

## Official Sources Used

- Salesforce Industries Feature Overview Spring '26 Release Notes — release notes, OmniStudio platform-native adoption, vertical cloud updates
  URL: https://help.salesforce.com/s/articleView?id=release-notes.rn_industries.htm

- Industries Common Features Developer Guide — standard objects, licensing model, cross-vertical architecture guidance
  URL: https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/ind.industries_common_features.htm

- OmniStudio Package and Salesforce Industries Package — managed package vs platform-native OmniStudio, migration implications
  URL: https://help.salesforce.com/s/articleView?id=ind.v_contracts_omnistudio_package_and_salesforce_industries_package.htm

- Salesforce Well-Architected Overview — Trusted, Adaptable, Easy pillars; architecture quality framing
  URL: https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
