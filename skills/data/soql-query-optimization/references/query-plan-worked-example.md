# Worked Example — Reading an `explain` Plan and Doing the Threshold Arithmetic

## 1. Request

The REST API's Query Performance Feedback resource (Beta, API 30.0+) analyzes a query, report, or list view without running it. Pass the SOQL, or the Id of a report or list view, as `explain`:

```bash
curl -H "Authorization: Bearer $ACCESS_TOKEN" \
  "https://MyDomainName.my.salesforce.com/services/data/v67.0/query/?explain=SELECT+Name+FROM+Merchandise__c+WHERE+CreatedDate+=+TODAY+AND+Price__c+>+10.0"
```

An invalid query returns `MALFORMED_QUERY`; an invalid report or list view Id returns `INVALID_ID`.

## 2. Response (from the REST API Developer Guide)

```json
{
  "plans": [
    {
      "cardinality": 1,
      "fields": ["CreatedDate"],
      "leadingOperationType": "Index",
      "notes": [
        {
          "description": "Not considering filter for optimization because unindexed",
          "fields": ["IsDeleted"],
          "tableEnumOrId": "Merchandise__c"
        }
      ],
      "relativeCost": 0.0,
      "sobjectCardinality": 3,
      "sobjectType": "Merchandise__c"
    },
    {
      "cardinality": 1,
      "fields": [],
      "leadingOperationType": "TableScan",
      "notes": [
        {
          "description": "Not considering filter for optimization because unindexed",
          "fields": ["IsDeleted"],
          "tableEnumOrId": "Merchandise__c"
        }
      ],
      "relativeCost": 0.65,
      "sobjectCardinality": 3,
      "sobjectType": "Merchandise__c"
    }
  ]
}
```

## 3. Reading it

| Field | First plan | Meaning |
|---|---|---|
| `leadingOperationType` | `Index` | The CreatedDate index drives the query |
| `fields` | `CreatedDate` | Index fields used; null unless the operation is `Index` |
| `relativeCost` | 0.0 | Under 1.0, so selective; the guide defines above 1.0 as not selective |
| `notes` | IsDeleted unindexed | No secondary filtering of deleted rows by index |
| `sobjectCardinality` | 3 | Approximate rows in the object; use it to sanity-check your own count |

Plans are sorted most to least optimal, and the first is the one that runs. `Sharing` as the leading operation means the user's sharing rules narrow the rows; a plan that is selective only for a narrowly shared user may not be for an integration user who sees everything.

## 4. Threshold worksheet

Fill one row per filter and one for the intersection. Object rows include the Recycle Bin.

| Filter | Index type | Rows matched (GROUP BY) | Threshold for N rows | Under threshold? | Under 2× (AND test)? |
|---|---|---|---|---|---|
| `Region__c = 'West'` | Custom | 180,000 | 100,000 (N = 1,000,000) | No | Yes (< 200,000) |
| `Tier__c = 'Gold'` | Custom | 120,000 | 100,000 | No | Yes |
| Intersection | — | 21,000 | 100,000 | Yes | — |

Threshold formulas: standard index = 30% × min(N, 1,000,000) + 15% × max(N − 1,000,000, 0); custom index = 10% × min(N, 1,000,000) + 5% × max(N − 1,000,000, 0). These reproduce the LDV guide's examples (2M → 450,000 standard; 5M → 900,000 standard and 300,000 custom; 500K → 50,000 custom).

Neither filter passes alone, both pass the twice-threshold test, and the intersection passes, so the AND condition can be selective. Confirm with the plan rather than the worksheet alone; also check that neither filter returns more than 20% of the object's rows, the point at which the optimizer stops using the indexes for an AND.
