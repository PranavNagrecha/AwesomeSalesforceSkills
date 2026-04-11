# Gotchas — AI Use Case Assessment

Non-obvious Salesforce platform behaviors that cause real problems during AI use case assessment.

## Gotcha 1: Edition Bundles Do Not Guarantee Feature Availability

**What happens:** An org has Salesforce Unlimited Edition and assumes that all Einstein features are included. In practice, several high-value AI capabilities — including Einstein for Service generative features (Work Summaries, Service Replies), Einstein for Sales (Opportunity Scoring, Lead Scoring), and Agentforce — require separate add-on licenses that are not bundled with any standard edition. A technical feasibility score of "go" assigned solely based on "we have Unlimited Edition" is incorrect and will lead to blocked implementations.

**When it occurs:** Most commonly when an admin or architect performs the technical feasibility assessment from memory rather than pulling the org's License and Permission Set License inventory from Setup > Company Information > Permission Set Licenses. Also occurs when sales teams communicate features as part of the edition without clarifying which require add-ons.

**How to avoid:** For every candidate use case, look up the specific license requirement in the Salesforce Help documentation for that feature. Cross-reference against the org's actual Permission Set License list in Setup. Do not rely on sales materials or edition marketing pages — check the feature's setup guide directly.

---

## Gotcha 2: Einstein Model Training Latency Is Not Displayed During Assessment

**What happens:** Einstein predictive features (Lead Scoring, Opportunity Scoring, Case Classification) require a model training period after activation — typically ranging from 24 hours to several weeks depending on record volume and outcome variance. This training latency is not visible during the pre-implementation assessment phase. An org can have the correct license, correct data volume, and good data quality scores, and still see a "Gathering Data" status after activation for weeks. The assessment will show these use cases as ready; the implementation will reveal the delay as a surprise.

**When it occurs:** Most commonly in orgs with sufficient record volume (e.g., 2,000+ Opportunities) but low outcome variance — for example, an org that closes 95% of its opportunities because they only log deals that are nearly certain to close. The model cannot learn a meaningful signal from an essentially binary outcome distribution.

**How to avoid:** During data readiness scoring, add a variance check for predictive use cases: what percentage of historical outcomes are distributed across possible outcome values? For Opportunity Scoring, review the closed-won vs. closed-lost ratio over the last 12 months. A ratio more extreme than 80/20 in either direction is a signal that model training quality will be degraded even if record volume is sufficient. Flag this in the quality sub-dimension score.

---

## Gotcha 3: Data Cloud Population Is Not a One-Time Setup

**What happens:** During assessment, an org confirms it has a Data Cloud license and therefore marks all Agentforce grounding use cases as technically feasible. However, Data Cloud readiness is not binary — it depends on which data streams are actively ingested, how recently they were refreshed, and whether the identity resolution rules have been run. An org can have Data Cloud licensed and partially configured but have critical data objects (e.g., e-commerce transaction history, support interaction history) not yet mapped or flowing. Use cases grounded on those objects are technically infeasible despite the license existing.

**When it occurs:** Most commonly in orgs that purchased Data Cloud as part of an Agentforce bundle but have not completed the ingestion and identity resolution setup. The license is present in Setup, but the data model is incomplete. Assessment teams confirm the license and mark feasibility as confirmed without auditing which data streams are actually populated.

**How to avoid:** During data readiness scoring for any Agentforce grounding use case, explicitly enumerate the data objects the agent needs to retrieve context from and verify each is: (a) ingested into a Data Cloud Data Stream, (b) mapped to a Data Model Object, and (c) included in the identity resolution ruleset. An incomplete check on any of these three conditions should reduce the unification sub-dimension score and may produce a Data Blocked recommendation.

---

## Gotcha 4: "AI Readiness" Trailhead Badges Do Not Map to Feature Availability

**What happens:** Practitioners complete Trailhead modules on AI strategy and Einstein features and use their learning as a proxy for understanding what their specific org can do. Trailhead content frequently covers features in general terms without distinguishing which license tier, edition, or Data Cloud configuration is required. Assessment outputs based on Trailhead knowledge alone tend to overestimate feasibility.

**When it occurs:** Common in orgs where the assessment is performed by a Trailhead-certified admin rather than a licensed Salesforce architect or SI partner with hands-on Einstein experience. The admin understands the concept of the feature but has not verified the prerequisites for their specific org configuration.

**How to avoid:** Supplement Trailhead learning with direct review of the feature's Setup page in the org (even if the feature is not yet activated) and the official Salesforce Help setup guide for the specific feature. Setup pages frequently display prerequisite warnings and license requirement notices that are not present in Trailhead content.

---

## Gotcha 5: Impact Scores Inflate for Use Cases That Sound Strategic But Are Poorly Defined

**What happens:** During the Impact-Effort scoring workshop, use cases described in strategic language ("AI-powered customer 360", "intelligent revenue forecasting") consistently receive high impact scores from business stakeholders because the language activates aspirational thinking rather than concrete analysis. When the same use cases are later decomposed into actual Salesforce features, the impact is substantially lower — or the use case turns out to be a multi-year platform investment, not a single feature activation.

**When it occurs:** When the brainstorm list is generated by executives or marketing stakeholders who frame use cases at the strategy layer rather than the feature layer, and the Impact-Effort scoring happens before those use cases are decomposed into concrete Salesforce capabilities.

**How to avoid:** Before scoring any use case on the Impact-Effort matrix, require a one-sentence feature-level definition: "This use case means activating [specific Einstein/Agentforce feature] on [specific object or process] to produce [specific measurable output]." If a use case cannot be defined at this level before scoring, it is not yet ready to score — decompose it first, or split it into multiple more concrete use cases.
