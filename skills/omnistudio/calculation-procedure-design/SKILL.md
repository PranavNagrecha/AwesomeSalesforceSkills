---
name: calculation-procedure-design
description: "Design OmniStudio Calculation Procedures and Calculation Matrices for pricing, rating, and rules-heavy scoring. Trigger keywords: calculation procedure, calculation matrix, rating engine, pricing matrix, expression set, decision matrix, OmniStudio rules. Does NOT cover: generic Apex-only pricing code, Salesforce CPQ price rules (different product), or Flow-based decision logic."
category: omnistudio
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Performance
  - Reliability
  - Operational Excellence
triggers:
  - "calculation procedure design"
  - "calculation matrix lookup"
  - "pricing engine in omnistudio"
  - "rating matrix versioning"
  - "expression set in calc procedure"
tags:
  - omnistudio
  - calculation-procedure
  - calculation-matrix
  - pricing
  - rules
inputs:
  - Business rules or rate tables in spreadsheet form
  - Input schema (line item, customer, product)
  - Output schema (price, score, eligibility)
outputs:
  - Calculation Procedure design (steps, matrices, constants)
  - Matrix versioning and activation plan
  - Test mode dataset and expected outputs
dependencies:
  - omnistudio/integration-procedure-cacheable-patterns
version: 1.0.0
author: Pranav Nagrecha
updated: 2026-04-28
---

# Calculation Procedure Design

## Core Building Blocks

- **Calculation Matrix** — a versioned table with input columns, output
  columns, and a lookup strategy (exact, range, nearest).
- **Calculation Procedure** — an ordered set of steps that reference
  matrices, constants, aggregations, and expression sets.
- **Constants** — named scalars pulled into steps.
- **Aggregations** — sum/min/max/avg across collections inside the
  procedure.
- **Expression Sets** — boolean expressions that conditionally branch.

## Decision Matrix Rules

Matrix design is where most failures happen.

- **Input columns** should be categorical or banded. Do not try to index
  on a raw continuous number — create bands.
- **Range inputs** need unambiguous, non-overlapping ranges. Ambiguous
  ranges lead to silent wrong answers.
- **Missing row behaviour** must be explicit. Default either to an
  explicit fallback row (`region = *`) or raise.
- **Matrix versioning**: publish a new version, do not edit active rows.
  Activate with effective-dated windows.

## Recommended Workflow

1. Write the rule as a spreadsheet. If it does not fit in a spreadsheet,
   it is not a Calculation Procedure.
2. Classify inputs: categorical, ranged, or bucketed. Decide on banding.
3. Draft the matrix with a fallback row and no overlaps.
4. Build the Calculation Procedure with matrix step + expression set
   steps. Keep the number of steps small.
5. Use test mode with a representative sample set before activation.
6. Version the matrix, add effective dates, and activate.
7. Cache the procedure call from an Integration Procedure when inputs
   are stable (see `omnistudio/integration-procedure-cacheable-patterns`).

## Performance Notes

- Matrix lookups are fast relative to Apex SOQL on custom objects.
- Calculation Procedures called from many UI interactions should be
  wrapped in a cacheable Integration Procedure, not called from the
  browser per-keystroke.
- Large matrices (tens of thousands of rows) still perform well, but
  test-mode runs become slow — sample rather than full-scan.

## Test Mode

Use the built-in test mode with named input/output pairs. Store the
sample dataset in source control as a JSON fixture. Run test mode after
every matrix version activation.

## Official Sources Used

- Calculation Procedures —
  https://help.salesforce.com/s/articleView?id=sf.os_calculation_procedures.htm
- Calculation Matrices —
  https://help.salesforce.com/s/articleView?id=sf.os_calculation_matrices.htm
- OmniStudio Expression Sets —
  https://help.salesforce.com/s/articleView?id=sf.os_expression_sets.htm
