# Examples — DataWeave for Apex

## Example 1: External CSV ingest reshaped to Account upsert

**Context:** A nightly partner-feed delivers a CSV (50–200 rows) of partner accounts to an inbound REST endpoint. The legacy Apex parser is a 180-line nest of `String.split`, header-index lookups, and try/catch around `Decimal.valueOf`. New fields keep getting requested; every change triggers a regression bug elsewhere.

**Problem:** The CSV format adds an optional `parent_external_id` column. The legacy parser breaks because the header-index is hard-coded to 5 columns. The fix would touch every line.

**Solution:**

`force-app/main/default/staticresources/PartnerCsvToAccount_DW.dwl`:

```dwl
%dw 2.0
input payload application/csv header=true
output application/json
---
payload map (row, idx) -> {
    Name: trim(row.partner_name),
    External_Id__c: row.partner_external_id,
    AnnualRevenue: row.revenue as Number default 0,
    Industry: row.industry default null,
    ParentExternalId__c: row.parent_external_id default null
}
```

`PartnerIngestService.cls`:

```apex
public with sharing class PartnerIngestService {
    private static final String SCRIPT_NAME = 'PartnerCsvToAccount_DW';

    public static List<Account> ingestCsv(String csvBody) {
        if (String.isBlank(csvBody)) return new List<Account>();
        Dataweave.Script script = Dataweave.Script.createScript(SCRIPT_NAME);
        Dataweave.Result result;
        try {
            result = script.execute(new Map<String, Object>{ 'payload' => csvBody });
        } catch (Dataweave.ExecuteException e) {
            throw new IngestException('CSV transform failed: ' + e.getMessage());
        }
        return (List<Account>) JSON.deserialize(
            result.getValueAsString(), List<Account>.class
        );
    }

    public class IngestException extends Exception {}
}
```

**Why it works:** The DataWeave script is the spec — adding a column is a one-line edit. The Apex caller stays under 30 lines, deserializes into a typed `List<Account>`, and surfaces transform failures as a single specific exception. The legacy 180-line parser is replaced.

---

## Example 2: SOAP-style XML payload from a billing system flattened to JSON

**Context:** A billing system pushes invoices via SOAP. The XML envelope has 4 levels of nesting and uses repeated `<line>` elements that may appear once or many times. The downstream consumer is a Salesforce LWC that wants a flat JSON list per invoice with line-item totals.

**Problem:** Apex `Dom.Document.getRootElement().getChildElements()` traversal handles the cases, but the resulting Apex is 70+ lines and the "one or many" handling is the source of every bug.

**Solution:**

`force-app/main/default/staticresources/BillingInvoice_DW.dwl`:

```dwl
%dw 2.0
input payload application/xml
output application/json
---
payload.envelope.invoices.*invoice map (inv) -> {
    invoiceNumber: inv.@number,
    customerExternalId: inv.customer.externalId,
    invoiceDate: inv.dates.issued as Date {format: "yyyy-MM-dd"},
    lines: (inv.lines.*line default []) map (line, idx) -> {
        sku: line.sku,
        quantity: line.qty as Number,
        unitPrice: line.unitPrice as Number,
        extendedPrice: (line.qty as Number) * (line.unitPrice as Number)
    },
    total: sum((inv.lines.*line default []) map ((line) -> (line.qty as Number) * (line.unitPrice as Number)))
}
```

Apex caller hands back parsed JSON via `getValueAsString()`; LWC consumes it directly via the `@AuraEnabled` method's return type. The `*line` syntax handles "zero, one, or many" lines safely.

**Why it works:** The transformation declares intent ("for each invoice, for each line, compute extended price, then sum to a total"). The XML schema's quirks (attributes via `@`, repeats via `*`) are handled by DataWeave's syntax rather than verbose DOM walking. Schema drift (an extra optional element) requires only a `default` clause.

---

## Example 3: When NOT to use DataWeave-for-Apex — small reshape

**Context:** A REST endpoint receives `{"id": "abc", "value": 42}` and needs to insert `Setting__c(External_Id__c='abc', Value__c=42)`.

**Problem:** Reaching for DataWeave here costs more than it saves. The script needs a static resource, the Apex needs `Dataweave.Script.createScript` and exception handling, and the test needs a fixture. The total file count is 4 files for a transform that is one Apex line.

**Solution (in Apex, no DataWeave):**

```apex
Map<String, Object> body = (Map<String, Object>) JSON.deserializeUntyped(reqBody);
insert new Setting__c(
    External_Id__c = (String) body.get('id'),
    Value__c = (Decimal) body.get('value')
);
```

**Why it works:** The transformation is small enough that the Apex equivalent is faster to read, write, and test. DataWeave's value compounds with field count and structural complexity; for trivial reshapes, plain Apex is the right answer.

---

## Anti-Pattern: Loading a full DataWeave script per trigger row

**What practitioners do:** A trigger handler calls `Dataweave.Script.createScript('Foo_DW')` inside a loop over `Trigger.new`, executing the script per record.

**What goes wrong:** Each `createScript` call hits the script-load path. Even with `Public` cache control, the per-call overhead is non-trivial; in a 200-row trigger this can blow the CPU budget on its own. The transformation is also redundant — the script is the same on every iteration.

**Correct approach:** Hoist `createScript` above the loop. If the input shape is per-row, build a single composite payload (one JSON array containing all rows) and execute once. DataWeave is at its best on bulk inputs, not row-by-row.
