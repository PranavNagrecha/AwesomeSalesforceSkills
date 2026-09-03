# ApexGuru Examples

## Bounded CLI scan

```bash
sf code-analyzer run \
  --rule-selector apexguru \
  --workspace force-app \
  --target "main/default/classes/InvoiceService.cls" \
  --target "main/default/triggers/InvoiceTrigger.trigger" \
  --target-org perf-sandbox \
  --view detail \
  --output-file artifacts/apexguru-invoice.json
```

Record the Git commit and org identity beside the output. The report proves only those two files were analyzed.

## Applicable query finding

A finding points to a query inside a loop. Inspection shows the loop can process 200 trigger records and the query uses the current record's Account ID. Move IDs into a set, query once, map results, preserve sharing/FLS behavior, run 1/200-record tests, and rescan. Add runtime evidence only when it was actually measured.

## Finding needing validation

A recommendation says a query lacks a restrictive filter. The object is small today but projected to grow. Mark `validate`, obtain a query plan and representative cardinality, then decide. Do not dismiss or rewrite the query solely from generic advice.

## Not-applicable finding

Generated managed-package source or an unreachable test fixture can be `not-applicable` only with evidence and a scoped exclusion. Do not suppress the entire rule or engine to silence one file.

## Combined Code Analyzer output

When a JSON file contains PMD and ApexGuru findings, preserve engine attribution. Use the checker's `--allow-other-engines` option and filter the normalized ApexGuru subset; do not re-label PMD findings as ApexGuru.
