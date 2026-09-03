# LLM Anti-Patterns

Review every research packet against these failures. The correction column is normative even when the resulting packet is partial.

## 1. Search-snippet citation

**Mistake:** Cite a search result title or excerpt without opening the underlying page.

**Why it happens:** Snippets are fast, concise, and often appear to answer the claim directly.

**Correct form:** Open the source, confirm the relevant passage and page identity, then record the claim, source tier, observed date, and applicable release/product context. A failed open remains a retrieval gap.

## 2. Silent source blending

**Mistake:** Merge attached material, repository knowledge, model memory, and web research into one narrative without provenance.

**Why it happens:** Synthesis naturally removes boundaries between inputs.

**Correct form:** Declare `supplied-only`, `official-salesforce`, or `open-research`. Mark each evidence item with origin and never use outside material to repair a supplied-only gap unless the user explicitly authorizes expansion.

## 3. Atomicity failure

**Mistake:** Put behavior, recommendation, entitlement, and inference in one compound claim with one citation.

**Why it happens:** Natural prose favors broad sentences; sources often support only part of them.

**Correct form:** Split into atomic claims. Classify each as fact, official recommendation, inference, scenario assumption, unknown, or unsupported. Map every source to exactly what it supports.

## 4. Timeless release claim

**Mistake:** Teach changing CLI flags, preview behavior, API support, product names, or lifecycle status as universal.

**Why it happens:** The model compresses versioned documentation into a stable rule.

**Correct form:** Record publication/updated date, Salesforce release or API version, CLI/extension/package version, and lifecycle state when material. Use an applicability note when the target toolchain differs.

## 5. Entitlement inference

**Mistake:** Assume a documented capability is licensed, enabled, provisioned, or permitted in a named org.

**Why it happens:** Official documentation proves platform existence and can be mistaken for customer-state evidence.

**Correct form:** Separate platform behavior from org facts. Verify edition, add-on, licenses, permissions, feature activation, package version, and environment identity through declared evidence; otherwise state `unknown`.

## 6. Official-logo flattening

**Mistake:** Treat reference docs, release notes, blogs, Trailhead modules, videos, help articles, and community posts as equal authorities.

**Why it happens:** All may use Salesforce branding and appear in the same search results.

**Correct form:** Use the repository source hierarchy. Prefer product/reference documentation and release notes for contracts; use blogs for rollout context, Trailhead for pedagogy, and community material as corroborated practitioner guidance.

## 7. Contradiction deletion

**Mistake:** Keep only the source that supports the intended lesson or quietly merge contradictory rollout stages.

**Why it happens:** A single answer feels more useful than a qualified one.

**Correct form:** Preserve both claims, compare dates, product surfaces, release channels, and prerequisites, then state whether the conflict is resolved, scoped, or still open. Do not invent a universal reconciliation.

## 8. Citation dumping

**Mistake:** Attach several links to a paragraph without showing which source supports which assertion.

**Why it happens:** A citation cluster looks well researched while avoiding claim-level work.

**Correct form:** Build a claim ledger with stable IDs. Map one or more sources to each claim and note limitations. The teaching brief may cite adjacent prose or refer back to claim IDs.

## 9. Newest-page bias

**Mistake:** Select the latest publication date even when the page covers preview behavior, a different host, or an unreleased toolchain.

**Why it happens:** Recency is used as a proxy for applicability.

**Correct form:** Compare scope before date: product, release channel, API/tool version, edition, host, and target environment. Newer is preferred only when it governs the same claim context.

## 10. AI-as-authority

**Mistake:** Use another generated summary, repository README claim, or model answer as sole support for product behavior.

**Why it happens:** Secondary summaries are easy to parse and often cite no source limits.

**Correct form:** Treat generated text as a lead, not evidence. Verify load-bearing facts against primary Salesforce documentation, target evidence, or reproducible tool output.

## 11. Copyright over-collection

**Mistake:** Copy long passages, examples, prompts, or templates because a public repository contains them.

**Why it happens:** Verbatim reuse appears accurate and saves authoring time.

**Correct form:** Record the license and provenance, extract ideas/functions, then write original atomic summaries and examples. Quote only short necessary text and attribute it under the applicable license and source policy.

## 12. Research/teaching collapse

**Mistake:** Write an engaging lesson before deciding which claims are supportable.

**Why it happens:** The model optimizes for narrative coherence and fills evidence gaps during explanation.

**Correct form:** Finish terminology, source inventory, claim ledger, contradictions, freshness, and gaps first. Only then hand verified claims to the learning-brief workflow; unsupported claims go under `Do Not Teach as Fact`.
