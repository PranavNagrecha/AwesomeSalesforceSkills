# CPQ vs Standard Products Decision — Work Template

Use this template when evaluating whether an org should adopt Salesforce CPQ or stay with standard Products and Pricebooks.

## Scope

**Skill:** `cpq-vs-standard-products-decision`

**Request summary:** (fill in what the user asked for)

## Context Gathered

Record the answers to the Before Starting questions from SKILL.md here.

- Product catalog size: ___ active products, ___ pricebooks
- Bundle requirements: (none / simple kits / complex bundles with option constraints)
- Pricing model: (flat list price / volume tiers / contracted rates / multi-dimensional)
- Number of quoting users: ___
- Current quoting approach: (standard objects / CPQ / manual / none)

## Feature Requirements Matrix

| Capability | Required? | Standard Objects | CPQ | Notes |
|---|---|---|---|---|
| Product catalog management | Yes / No | Native | Native | |
| Multiple pricebooks | Yes / No | Native | Native | |
| Product bundles with options | Yes / No | Custom build | Native | |
| Guided selling (question-based) | Yes / No | Flow (limited) | Native | |
| Volume-based discount schedules | Yes / No | Custom formula | Native | |
| Multi-dimensional discounting | Yes / No | Not feasible | Native | |
| Contracted / customer-specific pricing | Yes / No | Custom build | Native | |
| Subscription management | Yes / No | Custom build | Native | |
| Renewal / co-terming automation | Yes / No | Not feasible | Native | |
| Advanced multi-tier approvals | Yes / No | Approval Process (limited) | Native | |
| Quote PDF generation (dynamic) | Yes / No | Standard template (limited) | Native | |

## Cost Comparison

| Cost Category | Standard + Custom | Salesforce CPQ |
|---|---|---|
| Licensing (annual) | $0 | ___ users x $75/mo x 12 = $___ |
| Implementation estimate | $___ | $___ |
| Annual maintenance estimate | $___ | $___ |
| **3-Year TCO** | **$___** | **$___** |

## Migration Assessment

- Current state: (greenfield / existing standard quotes / existing CPQ)
- Historical quote records to migrate: ___ records
- Integrations to update: (list systems that read/write quote data)
- Estimated migration effort: ___ weeks

## Recommendation

**Recommended approach:** (Standard Products + Pricebooks / Salesforce CPQ)

**Rationale:**

(Summarize the key factors that drove the recommendation. Reference the feature matrix, cost comparison, and migration assessment.)

**Tradeoffs acknowledged:**

(List what the org gives up with the chosen approach. No recommendation is without tradeoffs.)

## Checklist

Copy the review checklist from SKILL.md and tick items as you complete them.

- [ ] Product catalog size and complexity have been documented
- [ ] Quoting workflow requirements are mapped
- [ ] CPQ licensing cost has been calculated for the actual user count
- [ ] Custom development alternative has been estimated for each required CPQ feature
- [ ] 3-year total cost of ownership comparison is complete
- [ ] Migration risk from current state has been assessed
- [ ] Recommendation includes clear tradeoffs, not just a single option

## Notes

Record any deviations from the standard analysis and why.
