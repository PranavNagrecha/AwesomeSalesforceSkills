# Examples — Knowledge Taxonomy Design

## Example 1: Multi-Product SaaS Support Org Flattening a Deep Single-Group Taxonomy

**Context:** A SaaS company runs a 450-agent service org supporting three cloud products. Their Knowledge base has grown to 1,800 articles organised under a single Data Category Group with 5 hierarchy levels: `Products → Cloud Product → Version → Feature Area → Sub-Feature`. Agents report that finding relevant articles takes 3–4 navigation clicks, and the Search Activity Gaps dashboard shows 40% of internal searches return zero results.

**Problem:** The single deep tree mixes two independent classification dimensions — product/version and topic/feature — inside one hierarchy. Agents can only filter by navigating the tree, not by composing filters from independent axes. Articles at leaf nodes (Level 5) are hard to discover because search relevance scoring in SOSL is weakened by over-categorisation depth. New articles are miscategorised because authors face 60+ leaf nodes to choose from.

**Solution:**

```text
Before (single group, 5 levels):
  Products
    Cloud CRM
      v2024
        Case Management
          Email-to-Case        ← articles live here (Level 5)
        Knowledge
          Search Configuration ← articles live here (Level 5)
    Cloud ERP
      ...

After (two groups, 2–3 levels each):
Group 1: Products (2 levels)
  Cloud CRM
    Case Management
    Knowledge
    Billing
  Cloud ERP
    Financials
    Inventory
  Cloud HCM
    Payroll
    Onboarding

Group 2: Article Types (1 level — flat)
  How-To
  Troubleshooting
  Reference
  Known Issue
  Release Note

Each article tagged: one Products leaf + one Article Types leaf.
Agents filter: Products = "Cloud CRM / Knowledge" AND Article Types = "Troubleshooting"
```

**Why it works:** Two shallow, independent groups compose at query time via AND logic in Knowledge search. Agents apply two single-click filters instead of navigating 5 levels. SOSL category-match scoring is sharper because articles sit at shallower nodes. The Article Types group is flat (Level 1 only) because topic type has no meaningful sub-classification for this org.

---

## Example 2: KCS Solve Loop Implementation with Validation Status Gating

**Context:** A 120-agent contact centre has high case volume (8,000 cases/month) but only 3 Knowledge authors who are also subject-matter experts. The backlog for new articles is 6 weeks. Agents frequently tell customers "I'll look into that and get back to you" because no article exists for the issue. Search Activity Gaps shows 55 distinct zero-result search terms repeated across multiple weeks, meaning the same content gaps are being hit repeatedly.

**Problem:** The publication process requires expert authorship before any article goes live. This creates a bottleneck — agents identify gaps, experts queue new articles, but the queue never clears. Zero-result searches compound because unaddressed gaps persist across the 90-day Search Activity Gaps window.

**Solution:**

```text
Validation Status picklist design:
  Not Validated         → default for new articles
  Work In Progress (WIP)→ agent-created, published, pending expert review
  Validated             → expert-reviewed, canonical version

Workflow:
  1. Agent opens new case, searches Knowledge, finds nothing useful
  2. Agent creates a new article DURING case resolution:
     - Sets Validation Status = Work In Progress
     - Publishes immediately (publish permission granted to all agents)
     - Links article to case
  3. Expert reviews WIP queue weekly (filter: Validation Status = WIP)
  4. Expert edits article content, sets Validation Status = Validated
  5. If article is too poor to rescue: expert sets to Draft for rework or archives

Measurement:
  - Weekly: count WIP articles created vs Validated (Evolve Loop velocity)
  - Monthly: export Search Activity Gaps list, compare to prior month baseline
  - Target: zero-result gap list shrinks by ≥10% month-over-month in first quarter
```

**Why it works:** The Solve Loop removes the creation bottleneck by allowing agents to publish imperfect but timely articles immediately. The Evolve Loop keeps quality improving asynchronously. Agents see their articles used by peers (linked cases, view counts), which sustains adoption. Search Activity Gaps tracking closes the feedback loop by confirming gaps are closing.

---

## Anti-Pattern: One Data Category Group With All Dimensions Combined

**What practitioners do:** Create a single Data Category Group named `All Knowledge` and build a deep tree that encodes product, topic, audience, and region all in one hierarchy: `All Knowledge → Internal/External → Product → Topic → Audience`.

**What goes wrong:** Every new classification dimension requires a complete restructuring of the tree. Articles must be re-assigned when any dimension changes. The hierarchy becomes unmaintainable past 3 dimensions because the combinatorial explosion forces either duplicated nodes or articles that are mis-classified by one of the encoded dimensions. SOSL search must traverse deep category paths, reducing relevance scoring for articles at deep nodes. Most critically, this structure forces agents to navigate the full tree path to filter on any single dimension, defeating the purpose of category-based filtering.

**Correct approach:** Identify classification dimensions that are *independently useful* for filtering (product, topic type, audience, region). Assign each independent dimension its own Data Category Group. Each group stays shallow (1–3 levels). Articles are tagged with one category from each active group. Agents compose filters across groups using AND logic, achieving the same narrowing with far less navigation overhead and without the restructuring cost when dimensions change.
