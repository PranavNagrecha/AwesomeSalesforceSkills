# Composite API Patterns — Work Template

Use this template when designing or implementing a Salesforce Composite API integration.

## Scope

**Skill:** `composite-api-patterns`

**Request summary:** (fill in what the integration needs to accomplish)

---

## Context Gathered

Answer these before selecting a resource or designing the request body.

- **API version in use:** (e.g., v63.0 for Spring '25)
- **Do subrequests depend on each other's results?** (yes → must use /composite/; no → batch or collection may apply)
- **Record volume per call:** (≤ 25 subrequests for composite/batch; ≤ 200 records for sobjects/tree)
- **Object type uniformity:** (same type → sobjects collection is simplest; mixed types → use /composite/)
- **Atomicity requirement:** (all-or-none → allOrNone: true or tree; partial ok → allOrNone: false with per-subrequest inspection)

---

## Resource Selection

Based on the context above, which Composite resource applies?

| Resource | Endpoint | Use when |
|---|---|---|
| Composite | `POST /composite` | Subrequests reference each other via @{referenceId.field} |
| sObject Collection | `POST/PATCH/DELETE /composite/sobjects` | Bulk CRUD on same object type, up to 200 records |
| sObject Tree | `POST /composite/tree/{SObject}/` | Hierarchical parent-child insert, ≤ 200 records, ≤ 5 levels |
| Composite Batch | `POST /composite/batch` | Independent requests, no result sharing, reduce round trips |

**Selected resource:** ___________
**Reason:** ___________

---

## Composite Request with Reference Chain (template)

The following shows a three-subrequest chain using `/composite/`. Adapt referenceId names, object types, and fields to your use case.

```json
POST /services/data/v63.0/composite
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "allOrNone": true,
  "compositeRequest": [
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Account/",
      "referenceId": "ParentAccount",
      "body": {
        "Name": "<AccountName>",
        "BillingCity": "<City>",
        "Industry": "<Industry>"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Contact/",
      "referenceId": "PrimaryContact",
      "body": {
        "LastName": "<LastName>",
        "FirstName": "<FirstName>",
        "Email": "<Email>",
        "AccountId": "@{ParentAccount.id}"
      }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Opportunity/",
      "referenceId": "InitialOpportunity",
      "body": {
        "Name": "<OpportunityName>",
        "AccountId": "@{ParentAccount.id}",
        "StageName": "Prospecting",
        "CloseDate": "<YYYY-MM-DD>",
        "Amount": 0
      }
    }
  ]
}
```

**referenceId naming convention used:** (describe your pattern, e.g., PascalCase object name + purpose)

---

## Response Parsing (required)

Outer HTTP 200 does not confirm success. Always inspect every subrequest result.

```python
def parse_composite_response(response_json: dict) -> tuple[list, list]:
    """
    Returns (successes, failures) where each entry is the full subrequest result dict.
    """
    successes = []
    failures = []
    for entry in response_json.get("compositeResponse", []):
        if entry.get("httpStatusCode", 0) >= 400:
            failures.append(entry)
        else:
            successes.append(entry)
    return successes, failures
```

---

## Checklist

Copy from SKILL.md and check off before marking the integration complete.

- [ ] Correct Composite resource selected for the dependency and volume profile
- [ ] All referenceId values are unique and case matches their @{} references exactly
- [ ] allOrNone flag is explicitly set with documented atomicity rationale
- [ ] Response parsing inspects every subrequest httpStatusCode — not just outer HTTP 200
- [ ] DML row count estimated (subrequests × records per subrequest) and within org limits
- [ ] Record count per call does not exceed resource limits (25 subrequests; 200 records)
- [ ] API version pinned to v60.0+ in all endpoint URLs
- [ ] Partial failure path handled when allOrNone: false

---

## Notes

(Record any deviations from the standard pattern, environment-specific constraints, or decisions made during implementation.)
