# LLM Anti-Patterns — SOSL Search Result Limits

Common mistakes AI coding assistants make when generating or advising on SOSL result limits.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming SOSL returns up to 2,000 records by default

**What the LLM generates:** advice like "a single-object SOSL returns up to 2,000 records" or
example code that expects thousands of rows from `[FIND 'x*' RETURNING Account(Id, Name)]`.

**Why it happens:** the model latches onto the well-known 2,000 *statement* ceiling and applies
it as the per-object default, ignoring the 250-record single-object rule that most training
data never surfaces.

**Correct pattern:**

```apex
// Single object with no WHERE/ORDER BY caps at 250, not 2,000.
// Add a WHERE or ORDER BY inside RETURNING to reach 2,000.
List<List<SObject>> r = [FIND 'x*' RETURNING Account(Id, Name WHERE IsActive__c = true)];
```

**Detection hint:** any claim that a bare single-object SOSL returns "up to 2,000" without a
`WHERE`/`ORDER BY` inside the `RETURNING` parentheses.

---

## Anti-Pattern 2: Getting the multi-object formula wrong (dividing 250, or ignoring it)

**What the LLM generates:** "each object returns up to 250" for any object count, or an invented
formula like "250/n" or "2,000 per object."

**Why it happens:** the model reproduces the memorable "250" figure without the min(2000/n, 250)
qualifier, and rarely reasons about how object count changes the per-object cap.

**Correct pattern:** each object returns **min(2000/n, 250)**. With 2 objects that is 250; with
10 objects it is 200 (2000/10); with 16 objects it is 125. The division only bites once `n > 8`.

**Detection hint:** any per-object figure that stays fixed at 250 regardless of object count, or
divides 250 by `n` instead of dividing 2,000.

---

## Anti-Pattern 3: Ignoring View All Data vs. per-user permission filtering

**What the LLM generates:** a debugging plan that reproduces a missing-record report "as an
admin" and concludes the query is fine when the record appears.

**Why it happens:** the model treats SOSL as returning a single objective result set and omits
the documented per-user filtering layer.

**Correct pattern:** reproduce as the affected user. Only View All Data holders see the full
computed set; everyone else has permission filters applied to the results, so a standard user
can receive fewer records than an admin for the identical search.

**Detection hint:** guidance that says "run it as an admin to check" without a caveat that
non-admins have record-permission filters applied to search output.

---

## Anti-Pattern 4: Treating the SearchQuery length thresholds as errors

**What the LLM generates:** "if the search string is too long, Salesforce throws an exception —
wrap it in try/catch," or no length handling at all.

**Why it happens:** the model assumes length overruns fault loudly, as they do for many APIs.

**Correct pattern:** these thresholds fail *silently*. Over 4,000 characters the logical
operators are removed; over 10,000 characters zero rows are returned. Guard proactively:

```apex
if (searchQuery.length() > 4000) {
    throw new SearchInputException('Over 4,000 chars: logical operators would be removed.');
}
```

**Detection hint:** a `try/catch` around `Search.query` presented as the length safeguard, or
any claim that an over-length `SearchQuery` "will error."

---

## Anti-Pattern 5: Recommending "search more objects" to find a missing record

**What the LLM generates:** advice to add more objects to the `RETURNING` clause so the search
"covers more ground" and stops missing records.

**Why it happens:** the model reasons intuitively that a wider search returns more, without the
min(2000/n, 250) mechanics that make each added object shrink every object's slice.

**Correct pattern:** narrow, don't widen. Scope to the single object holding the record (the
documented "Joe" remedy) and add a `WHERE`/`ORDER BY` inside its `RETURNING` parentheses.

**Detection hint:** any remedy for a missing record that *increases* the object count in
`RETURNING`.

---

## Anti-Pattern 6: Asserting a GA/Beta status or the wrong API-version pin

**What the LLM generates:** "this GA feature..." or attributing the 2,000-record scan to the
wrong API version (e.g. "since API 21.0").

**Why it happens:** models pattern-fill maturity labels and default to familiar API numbers.

**Correct pattern:** the docs do not stamp these limits as GA/Beta/Pilot — do not invent a
maturity level. Attribute the version pin exactly as documented: the 2,000-record scan and the
2,000-total ceiling "start with API version 28.0," and the 100,000-character statement limit is
the org default.

**Detection hint:** any "Generally Available"/"Beta" label on these limits, or an API-version
number for the scan limit that is not 28.0.
