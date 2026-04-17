# LLM Anti-Patterns — Salesforce Object Queryability

## Anti-Pattern 1: Compound object names that don't exist

**What the LLM generates:** `PermissionSetGroupAssignment`, `UserPermissionSet`, `ProfilePermissionSetMember`.

**Why it happens:** LLMs pattern-match on naming conventions. "There's `PermissionSetAssignment` and `PermissionSetGroup` — clearly `PermissionSetGroupAssignment` exists."

**Correct pattern:** Validate every sObject name against `/sobjects/` describe output BEFORE issuing a query. Refuse to fabricate.

**Detection hint:** Any sObject name ending in `Assignment`, `Member`, or `Link` that wasn't present in a validated describe response.

---

## Anti-Pattern 2: "Not queryable in this org" as a catch-all

**What the LLM generates:** Any query failure → report "not queryable in this org" → move on.

**Why it happens:** LLMs prefer narrative completion over diagnostic precision.

**Correct pattern:** Classify the failure into one of the six modes. Report the mode, not the symptom.

---

## Anti-Pattern 3: Silent `try/except: pass` around query code

**What the LLM generates:**
```python
try:
    results = run_query(q)
except Exception:
    results = []
```

**Why it happens:** LLMs want "robust" code that "doesn't crash."

**Correct pattern:** Catch specific exceptions, classify, log, and propagate OR retry. Never silently coerce to empty.

---

## Anti-Pattern 4: Reusing one error handler for all dimensions

**What the LLM generates:** One shared `except:` block wraps 9 different probe queries. First failure kills all 9.

**Why it happens:** DRY instinct applied wrong.

**Correct pattern:** Each probe query gets its own try/except. A failed PSG query shouldn't prevent Object CRUD from being queried.

---

## Anti-Pattern 5: Assuming API v62 everywhere

**What the LLM generates:** Hard-coded `/services/data/v62.0/` in every probe.

**Why it happens:** LLM picks the version it saw most recently.

**Correct pattern:** Read the client's API version from `sf` config or use the `/services/data/` listing endpoint to pick the newest. Document the minimum required version per probe.

---

## Anti-Pattern 6: Retrying on 400 errors

**What the LLM generates:** Exponential-backoff retry on every non-200.

**Why it happens:** Generic resiliency pattern.

**Correct pattern:** 400 errors almost never fix themselves via retry. Only retry 500 / 503 / 429. 400 = the query is wrong; fix it or classify and move on.

---

## Anti-Pattern 7: Concatenating user input into SOQL

**What the LLM generates:** `f"SELECT Id FROM User WHERE Username = '{username}'"`.

**Why it happens:** Fast string-template pattern.

**Correct pattern:** Use bind variables or the `sf` CLI's parameterized query. SOQL injection is real for probes that accept caller-supplied filters.

---

## Anti-Pattern 8: Dumping full result rows into logs

**What the LLM generates:** `logger.debug(json.dumps(results))` where results contain User records.

**Why it happens:** Debug-logging habit.

**Correct pattern:** Log row counts, field names, and shape. Never PII values. See `references/gotchas.md` in `user-access-diff` for the redaction contract.

---

## Anti-Pattern 9: Treating `{"totalSize": 0}` as an error

**What the LLM generates:** `if not results: raise FailedQuery()`.

**Why it happens:** Conflating "no rows" with "query broken."

**Correct pattern:** Empty result is success. Record it as `dimension_compared` with a note ("user has no PSG assignments"), not `dimension_skipped`.

---

## Anti-Pattern 10: Fabricating an error class

**What the LLM generates:** Classifying a real 500 as "object doesn't exist" (Mode 1) because the body says "Internal Server Error" and the LLM decided that's what Mode 1 looks like.

**Why it happens:** LLMs map unfamiliar error strings to the closest known category.

**Correct pattern:** Classify against the actual `errorCode` field in the response payload — the structured field, not the free-text message. If unknown, classify as "unknown_mode" and escalate rather than guess.
