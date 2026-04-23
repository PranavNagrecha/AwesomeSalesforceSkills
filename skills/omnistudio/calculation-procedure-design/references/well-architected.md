# Well-Architected Notes — Calculation Procedures

## Relevant Pillars

- **Operational Excellence** — rate tables maintained by business, not
  devs, is a huge ops win.
- **Reliability** — matrix versioning + effective dates preserve
  historical correctness.
- **Performance** — matrix lookup beats code path for tabular rules.

## Architectural Tradeoffs

- **Matrix vs code:** matrix is tunable by business; code is more
  powerful. Prefer matrix when rules are tabular.
- **Many small matrices vs one big matrix:** small matrices are easier
  to review but require more procedure steps; big matrices are easier to
  reason about at a glance but harder to diff.
- **Effective-dated vs switch-over activation:** effective dates preserve
  back-dated quote correctness at the cost of slightly more complex
  lookup logic.

## Matrix Hygiene

- Non-overlapping ranges, enforced in review.
- Explicit wildcard fallback row.
- Named versions referenced by procedure, not "active" alone.

## Official Sources Used

- Calculation Procedures —
  https://help.salesforce.com/s/articleView?id=sf.os_calculation_procedures.htm
- Calculation Matrices —
  https://help.salesforce.com/s/articleView?id=sf.os_calculation_matrices.htm
