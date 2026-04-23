# Examples — LWC Performance Budgets

## Example 1: Bundle Size Manifest

```yaml
# budgets/lwc-budgets.yaml
components:
  accountOverview:
    maxMinifiedKb: 40
    maxWireAdapters: 3
    owner: accounts-team
  productCatalog:
    maxMinifiedKb: 60
    maxWireAdapters: 2
    owner: commerce-team
```

A pre-deploy script reads the built artefacts and fails if any
component is over cap.

## Example 2: Lighthouse CI Assertion

```json
{
  "ci": {
    "assert": {
      "assertions": {
        "largest-contentful-paint": ["error", {"maxNumericValue": 2500}],
        "interaction-to-next-paint": ["error", {"maxNumericValue": 200}]
      }
    }
  }
}
```

## Example 3: Wire-Adapter Audit

```bash
# Counts @wire decorators per LWC
grep -rn "@wire" force-app/main/default/lwc --include="*.js" \
    | awk -F: '{print $1}' | sort | uniq -c | sort -rn
```

Components with > 3 wires are flagged for review.

## Example 4: Regression Playbook

- LCP p75 > 2.5 s for 3 consecutive days → open a ticket.
- Ticket assignee runs a targeted trace (Chrome DevTools performance
  profile on the page, not synthetic).
- Root cause categorised: bundle-size regression, new wire, data
  volume, image weight.
- Fix → re-measure → close.
