# LLM Anti-Patterns — Composite API Patterns

Common mistakes AI coding assistants make when generating or advising on Salesforce Composite API usage.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Using /composite/batch/ When Requests Have Dependencies

**What the LLM generates:** A `/composite/batch/` request where subrequest 2 includes a hardcoded placeholder ID or a comment like `// replace with Account ID from subrequest 1`.

```json
{
  "batchRequests": [
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Account/",
      "richInput": { "Name": "Acme" }
    },
    {
      "method": "POST",
      "url": "/services/data/v63.0/sobjects/Contact/",
      "richInput": {
        "LastName": "Smith",
        "AccountId": "REPLACE_WITH_ACCOUNT_ID"
      }
    }
  ]
}
```

**Why it happens:** LLMs associate "batch" with "multiple operations" and default to the Batch resource. The cross-subrequest referenceId capability of `/composite/` is less prominent in training data than the generic concept of batching.

**Correct pattern:**

```json
POST /services/data/v63.0/composite
{
  "allOrNone": true,
  "compositeRequest": [
    { "method": "POST", "url": "...", "referenceId": "NewAccount", "body": { "Name": "Acme" } },
    { "method": "POST", "url": "...", "referenceId": "NewContact", "body": { "AccountId": "@{NewAccount.id}" } }
  ]
}
```

**Detection hint:** Any batch request body containing placeholder strings (REPLACE_WITH, TODO, UNKNOWN_ID) in field values is a sign the LLM needed `/composite/` instead.

---

## Anti-Pattern 2: Ignoring Per-Subrequest Error Inspection

**What the LLM generates:** Response handling that checks only the outer HTTP status code and treats HTTP 200 as full success.

```python
response = requests.post(url, json=payload, headers=headers)
if response.status_code == 200:
    print("All records created successfully")
    return True
```

**Why it happens:** Standard REST API conventions treat HTTP 200 as success. LLMs trained on generic REST API patterns apply this heuristic to Composite responses without accounting for the Salesforce-specific behavior where subrequest failures are embedded inside a 200 envelope.

**Correct pattern:**

```python
response = requests.post(url, json=payload, headers=headers)
data = response.json()
failures = [
    r for r in data.get("compositeResponse", [])
    if r.get("httpStatusCode", 0) >= 400
]
if failures:
    for f in failures:
        print(f"FAILED: {f['referenceId']} — {f['body']}")
    raise IntegrationError("Composite call had subrequest failures")
```

**Detection hint:** Response handling code that reads `status_code == 200` and immediately returns success without accessing `compositeResponse` array entries is missing subrequest error inspection.

---

## Anti-Pattern 3: Using sObject Collection When Subrequests Span Multiple Object Types With Dependencies

**What the LLM generates:** A `/composite/sobjects/` POST request that mixes Accounts, Contacts, and Opportunities in a single `records[]` array, expecting Salesforce to wire parent-child relationships.

```json
{
  "allOrNone": true,
  "records": [
    { "attributes": { "type": "Account" }, "Name": "Acme" },
    { "attributes": { "type": "Contact" }, "LastName": "Smith", "AccountId": "???" }
  ]
}
```

**Why it happens:** LLMs conflate "batch of records" with "sObject Collection" without distinguishing which Composite resources support cross-record ID referencing. sObject Collection DML operations require uniform object types and do not support referenceId wiring between records.

**Correct pattern:** Use `/composite/` for mixed object type inserts with dependencies. Use `/composite/sobjects/` only for same-type bulk operations.

**Detection hint:** Any sObject Collection request body containing records with different `attributes.type` values in a DML (POST/PATCH/DELETE) call — or IDs that appear to be placeholders — indicates misuse of the resource.

---

## Anti-Pattern 4: Exceeding Subrequest Limits Without Splitting

**What the LLM generates:** A loop that adds subrequests to a composite request array without checking the 25-subrequest limit, resulting in request bodies with 30, 50, or 100 entries.

```python
composite_requests = []
for record in all_records:  # might be 80 records
    composite_requests.append({
        "method": "POST",
        "url": f"/services/data/v63.0/sobjects/{record['type']}/",
        "referenceId": f"Ref{record['id']}",
        "body": record
    })
payload = {"allOrNone": True, "compositeRequest": composite_requests}
```

**Why it happens:** LLMs generate the loop pattern correctly but omit the batching logic that chunks the array into groups of 25 before sending. The 25-subrequest limit is a platform constraint that requires explicit enforcement in the caller.

**Correct pattern:**

```python
BATCH_SIZE = 25
for i in range(0, len(all_requests), BATCH_SIZE):
    chunk = all_requests[i:i + BATCH_SIZE]
    payload = {"allOrNone": True, "compositeRequest": chunk}
    response = requests.post(composite_url, json=payload, headers=headers)
    # inspect response before next chunk
```

**Detection hint:** Any composite payload assembly code that does not enforce a maximum chunk size of 25, or any generated payload where `len(compositeRequest) > 25`, has exceeded the platform limit.

---

## Anti-Pattern 5: Confusing sObject Tree With Composite for Flat Record Sets

**What the LLM generates:** A `/composite/tree/` request used to insert a flat list of Accounts with no parent-child nesting, treating it as a general-purpose bulk insert resource.

```json
POST /services/data/v63.0/composite/tree/Account/
{
  "records": [
    { "attributes": { "type": "Account", "referenceId": "Acc1" }, "Name": "Acme" },
    { "attributes": { "type": "Account", "referenceId": "Acc2" }, "Name": "Globex" }
  ]
}
```

**Why it happens:** The LLM recognizes that sObject Tree supports bulk inserts and recommends it without evaluating whether the hierarchical nesting capability is needed. For flat same-type record sets, `/composite/sobjects/` is simpler, supports upsert semantics, and does not carry the all-or-nothing constraint of the tree resource.

**Correct pattern:** Reserve `/composite/tree/` for parent-child hierarchical inserts where child records must be created with a relationship to a parent being created in the same call. For flat bulk creates of the same object type, use `POST /composite/sobjects/` instead — it supports `allOrNone: false` for partial success.

**Detection hint:** A `/composite/tree/` request where all records in `records[]` are the same object type with no nested child record arrays — there is no tree structure being used, and sObject Collection would be more appropriate.
