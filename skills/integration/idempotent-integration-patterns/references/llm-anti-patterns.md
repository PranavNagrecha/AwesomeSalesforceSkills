# LLM Anti-Patterns — Idempotent Integration Patterns

Common mistakes AI coding assistants make when designing or advising on idempotent Salesforce integrations.

## Anti-Pattern 1: Generating Idempotency Key on Each Retry

**What the LLM generates:**

```python
for attempt in range(max_retries):
    idempotency_key = str(uuid.uuid4())  # New UUID per attempt
    response = requests.post(url, 
        headers={"X-Idempotency-Key": idempotency_key},
        json=payload)
```

**Why it happens:** LLMs apply the general pattern of adding an idempotency key header without understanding the requirement that the key must be pre-generated and stable across all retries.

**Correct pattern:**

```python
# Generate ONCE before the retry loop
idempotency_key = str(uuid.uuid4())  # Single key for this logical operation

for attempt in range(max_retries):
    response = requests.post(url, 
        headers={"X-Idempotency-Key": idempotency_key},  # Same key every retry
        json=payload)
    if response.ok:
        break
    time.sleep(2 ** attempt)
```

**Detection hint:** Any retry loop that generates `uuid.uuid4()` or an equivalent random key inside the loop body.

---

## Anti-Pattern 2: Using POST Instead of PATCH for Idempotent Inbound Record Writes

**What the LLM generates:** "Use the Salesforce REST API POST endpoint to create Account records: `POST /services/data/v63.0/sobjects/Account`"

**Why it happens:** POST is the standard REST verb for creating resources. LLMs default to it without knowing that PATCH with External ID is the idempotent alternative.

**Correct pattern:**

```
For idempotent inbound record writes:
1. Create a custom External ID field: ExternalId__c (Text, External ID: true, Unique: true)
2. Use PATCH with the External ID value:
   PATCH /services/data/v63.0/sobjects/Account/ExternalId__c/<value>
   
Behavior:
- 0 matches → inserts new record
- 1 match → updates existing record  
- 2+ matches → error (prevents ambiguous updates; ensure field is Unique)

POST always creates → not idempotent; retries create duplicates.
PATCH with External ID → idempotent; retries update existing record.
```

**Detection hint:** Any recommendation to use POST for an integration that needs retry safety.

---

## Anti-Pattern 3: Recommending Publish Immediately for Transactional Platform Events

**What the LLM generates:**

```apex
// Publish immediately when opportunity is closed
EventBus.publish(new DealClosed__e(OpportunityId__c = opp.Id));
```

**Why it happens:** `EventBus.publish()` is the standard Platform Event publish call. LLMs generate it without knowing the Publish Immediately vs. Publish After Commit distinction.

**Correct pattern:**

```apex
// For events correlated with DML: use Publish After Commit
// Option 1: Set PublishBehavior on the event object
DealClosed__e event = new DealClosed__e(
    OpportunityId__c = opp.Id,
    PublishBehavior = 'PublishAfterCommit'
);
EventBus.publish(event);

// With Publish Immediately (default):
// Event delivered BEFORE transaction commits.
// If transaction rolls back → event delivered for non-existent record.

// With Publish After Commit:
// Event delivered ONLY after transaction successfully commits.
// Transaction rollback → event discarded.
```

**Detection hint:** Any `EventBus.publish()` call in a trigger context without discussion of Publish After Commit.

---

## Anti-Pattern 4: External ID Upsert Without Unique Constraint

**What the LLM generates:** "Create an External ID field on the Account object. Then use the upsert endpoint with this field to prevent duplicate records."

**Why it happens:** LLMs describe External ID upsert correctly in principle but omit the requirement to mark the field as Unique.

**Correct pattern:**

```
External ID field MUST be marked as Unique for reliable idempotency.

Without Unique:
- Multiple records can share the same External ID value
- Upsert returns error: "More than one record found for External ID"
- Idempotency fails

Field creation settings:
✓ Data Type: Text (or Number, Email)  
✓ External ID: true  
✓ Unique: true  ← REQUIRED
✓ Case Insensitive: depends on data

After field creation, verify no existing data has duplicates before enabling Unique.
```

**Detection hint:** Any External ID field creation guidance that does not specify marking it as Unique.

---

## Anti-Pattern 5: Treating Salesforce Duplicate Management Rules as Integration Idempotency

**What the LLM generates:** "Enable Duplicate Management rules on the Account object to prevent duplicates from integration retries."

**Why it happens:** Duplicate Management sounds like the correct solution for "prevent duplicate records." It is a different feature for a different problem.

**Correct pattern:**

```
Duplicate Management: Prevents records that MATCH business criteria (e.g., same Name+Email).
- Applied at insert/update time based on matching rules
- Does NOT use integration keys or idempotency keys
- Can block legitimate inserts if business criteria overlap

Idempotent Integration Pattern: Prevents processing the SAME logical operation twice.
- Based on stable external ID or idempotency key
- Works regardless of field value similarity
- Correctly handles: same order, different amounts (update not duplicate)

Both may be needed simultaneously.
Duplicate Management alone is NOT an idempotency solution.
```

**Detection hint:** Any response that recommends Duplicate Management as the solution to integration retry duplication.
