# LLM Anti-Patterns — Hyperforce Architecture

Common mistakes AI assistants make when reasoning about Hyperforce migrations and architecture. These help the consuming agent self-check its own output.

## Anti-Pattern 1: claiming a region change is a Setup-level toggle

**What the LLM generates:** "To move your org to a different Hyperforce region, go to Setup → Company Information and update the region setting."

**Why it happens:** LLMs over-generalize from "Setup configures the org" to "Setup configures the infrastructure." Setup doesn't expose region as a self-service option.

**Correct pattern:** A new-region landing requires a Salesforce engagement and contract change — it is not a customer self-service operation. The Setup → Company Information page may *display* the instance and region but does not let the customer change them.

**Detection hint:** any answer about "switching regions" that points to a Setup screen rather than a Salesforce engagement.

---

## Anti-Pattern 2: equating Hyperforce migration with feature unlocks happening automatically

**What the LLM generates:** "Once your org is on Hyperforce, Private Connect / Data Cloud / regional Einstein is enabled automatically."

**Why it happens:** "Hyperforce-only" is correctly characterized in training data as a prerequisite, but the next step (separately licensing or activating the feature) often gets dropped in summaries.

**Correct pattern:** Hyperforce migration is a *prerequisite*, not an enablement. Each Hyperforce-only feature has its own activation, licensing, or configuration path on top of being on Hyperforce. The migration unlocks the *possibility*; the feature still needs its own project.

**Detection hint:** any answer that promises Hyperforce-only features turn on as a side effect of migration.

---

## Anti-Pattern 3: confusing data residency with data sovereignty

**What the LLM generates:** "By choosing the EU-Frankfurt region, you satisfy GDPR sovereignty requirements; data is European and protected from US legal process."

**Why it happens:** Residency and sovereignty are related concepts that LLMs flatten into one. The Schrems II case law specifically distinguishes them.

**Correct pattern:** Hyperforce regions deliver at-rest residency — the records live in that region. Sovereignty (legal-process scope) is a separate consideration involving the cloud provider's home jurisdiction, the cloud provider's legal entity structure, and contractual mechanisms (SCCs, BCRs). Region selection is necessary but not sufficient for sovereignty obligations.

**Detection hint:** any answer that claims Hyperforce region choice alone satisfies a "sovereignty" obligation. Legal review is required, not just Salesforce architecture.

---

## Anti-Pattern 4: claiming Hyperforce gives customers controllable cross-region failover

**What the LLM generates:** "Use Hyperforce's region pairing to design active-active failover with customer-controlled failover triggers."

**Why it happens:** AWS / Azure regional failover patterns are common in training data; LLMs apply them to Hyperforce by analogy.

**Correct pattern:** Hyperforce manages failover at the platform level. Customers cannot trigger it, observe it directly, or design active-active across Hyperforce regions inside a single org. For customer-controllable HA across orgs/regions, the answer is multi-org strategy with replication, not Hyperforce region pairing.

**Detection hint:** any answer that describes "Hyperforce active-active" or "customer-triggered Hyperforce failover" — neither exists.

---

## Anti-Pattern 5: omitting customer-side IP allowlist work

**What the LLM generates:** "Salesforce handles the migration; the customer does not need to update IP allowlists."

**Why it happens:** Migration assistance does some networking work; LLMs generalize "Salesforce handles networking" too far.

**Correct pattern:** The customer is responsible for updating customer-side firewalls, middleware allowlists, partner-org allowlists, identity-provider allowlists, and Setup → Network Access entries. The Hyperforce IP CIDRs (cloud-provider-owned) are different from First-Gen ranges. Day-1 incidents are dominated by missed customer-side allowlist updates.

**Detection hint:** any migration plan that doesn't enumerate customer-side allowlist update owners and dates.

---

## Anti-Pattern 6: conflating Hyperforce migration with Salesforce Functions decommission

**What the LLM generates:** "Migrating to Hyperforce will retire your Salesforce Functions; plan replacements as part of the migration."

**Why it happens:** Both are platform-level transitions Salesforce announces concurrently in customer communications; LLMs link them causally.

**Correct pattern:** They are unrelated programs with separate timelines. Salesforce Functions retires on its own schedule regardless of Hyperforce status. Hyperforce migration does not trigger or accelerate Functions decommission.

**Detection hint:** any answer that bundles Functions retirement into the Hyperforce migration plan as a sub-task.

---

## Anti-Pattern 7: assuming Government Cloud is a Hyperforce region

**What the LLM generates:** "For FedRAMP / GovCloud workloads, choose the Government Cloud region during Hyperforce migration."

**Why it happens:** "Region" is the right vocabulary; Government Cloud sounds region-shaped; LLMs collapse them.

**Correct pattern:** Salesforce Government Cloud (and Government Cloud Plus) is a separate licensed product with its own org type, data centers, and compliance certifications (FedRAMP Moderate / High, IL5, ITAR). It is not a region option inside the commercial Hyperforce migration. A regulated workload requiring GovCloud lands on Government Cloud, not on a commercial Hyperforce region.

**Detection hint:** any answer that includes "Government Cloud" in a list of Hyperforce regions or describes GovCloud as a checkbox during migration.
