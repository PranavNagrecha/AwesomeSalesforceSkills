# Well-Architected Notes — Agentforce Grid

> Agentforce Grid was introduced in Winter '26 and its setup is documented as **Beta** — the
> notes below describe design tradeoffs, not GA guarantees.

## Relevant Pillars

- **Operational Excellence** — Grid is metered, and metering applies "regardless of the AI
  lifecycle phase in which it's used" (test, build, or scale). Operational discipline means
  treating every run as a spend: bound the data column with a filter and Max Results, review the
  Flex Credit / Billing Calculator estimate for the real row count, and preview a few rows before
  committing the full worksheet. Cost is `rows × (AI + action columns)`, so column count and row
  count are the levers.
- **Security** — data columns read live CRM or Data Cloud (Data 360) data and action columns
  write back to Salesforce fields, all under the operating user's permissions. CRUD/FLS and
  sharing still apply: don't assume Grid bypasses them, and don't push AI-generated content into
  fields the user shouldn't be able to write. Read-only insight runs should omit the action
  column entirely so no data is mutated.
- **Reliability** — the worksheet is a left-to-right dependency chain; a column can only consume
  columns to its left. Reordering or inserting a column can silently break a downstream
  reference. Verify the chain after any structural edit, and preview output before a wide run so
  errors surface on a handful of rows, not thousands.

## Architectural Tradeoffs

- **Grid vs. Flow/Apex.** Grid runs a bulk chain with no code, inspectable row by row — ideal for
  one-off or exploratory bulk operations. But it is metered and it is not a deployable metadata
  type. For repeatable, source-controlled production automation, Flow or Apex is the right home;
  reserve Grid for human-in-the-loop bulk work.
- **Prompt Template vs. Use AI.** A **Prompt Template** AI column reuses a governed, versioned
  prompt — better for anything repeated or audited. **Use AI** (direct instruction + chosen
  model) is faster for a quick, one-off transformation but decentralizes the prompt. Prefer
  templates where governance matters.
- **Write-back vs. read-only.** Adding an Update Record column mutates live data and spends
  credits on writes. When the goal is review or analysis, stop at the AI column and read the
  Output Preview — don't write data (or pay to write it) you didn't intend to change.
- **Wide worksheet vs. narrow runs.** More AI/action columns per row means more capability but
  multiplies per-row cost. Trim columns to what the outcome requires.

## Anti-Patterns

1. **Assuming free experimentation** — running broadly because it's "just testing." Grid is
   metered in every lifecycle phase; a wide exploratory run consumes Flex Credits.
2. **Unbounded row sets** — importing an object with no filter and no Max Results, then paying to
   run every AI/action column across the entire table.
3. **Forward references** — placing an action column before the AI column it should write, or
   referencing a column to its right, which cannot resolve in a left-to-right pipeline.
4. **Treating a worksheet as deployable metadata** — trying to package or `sf project deploy` a
   Grid worksheet; it lives in Studio, not the Metadata API.

## Official Sources Used

- Agentforce Grid (Salesforce Help) — https://help.salesforce.com/s/articleView?id=ai.agentforce_grid.htm&language=en_US&type=5
- Set Up Agentforce Grid (Beta) (Salesforce Help) — https://help.salesforce.com/s/articleView?language=en_US&id=ai.agentforce_grid_set_up.htm&type=5
- Create a Grid Worksheet (Salesforce Help) — https://help.salesforce.com/s/articleView?id=ai.agentforce_grid_create_worksheet.htm&language=en_US&type=5
- Trailhead: Agentforce Grid module — https://trailhead.salesforce.com/content/learn/modules/agentforce-grid
- Trailhead: Explore Data with Agentforce Grid — https://trailhead.salesforce.com/content/learn/modules/agentforce-grid/explore-data-with-agentforce-grid
- Generative AI Usage (metering) (Salesforce Help) — https://help.salesforce.com/s/articleView?language=en_US&id=ai.generative_ai_usage.htm
- Salesforce Introduces New Flexible Agentforce Pricing (Newsroom, 15 May 2025) — https://www.salesforce.com/news/press-releases/2025/05/15/agentforce-flexible-pricing-news/ — "$500 USD per 100,000 Credits"; "One Agentforce action consumes 20 Flex Credits ($0.10 USD)"; "All customers with Enterprise Edition or above can get 100,000 Flex Credits for $0 with Salesforce Foundations"; conversational pricing remains "$2 per conversation". Help article 004811240 (Agentforce Pricing) is the in-product rate card but returns an SPA shell — do not treat it as verified here. (verified 2026-08-14)
