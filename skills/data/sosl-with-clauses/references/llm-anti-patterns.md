# LLM Anti-Patterns — SOSL WITH Clauses

Common mistakes AI coding assistants make when generating or advising on SOSL WITH clauses.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Reordering WITH clauses freely

**What the LLM generates:** WITH clauses in whatever order they were mentioned, e.g. `WITH
HIGHLIGHT` before `WITH DATA CATEGORY`, or `WITH SNIPPET` after `WITH NETWORK`.

**Why it happens:** SOQL trains the model that filter/sort clauses are order-independent, so it
generalizes that freedom to SOSL — but SOSL enforces one fixed WITH order.

**Correct pattern:**

```sql
-- canonical order: DATA CATEGORY, then SNIPPET, then HIGHLIGHT
FIND {refund} RETURNING KnowledgeArticleVersion (Id WHERE PublishStatus='online')
  WITH DATA CATEGORY Product__c AT Billing__c
  WITH SNIPPET (target_length=200)
  WITH HIGHLIGHT
```

**Detection hint:** flag any query where the WITH-clause keywords are not a subsequence of
`DivisionFilter, DATA CATEGORY, SNIPPET, NETWORK, PricebookId, METADATA, HIGHLIGHT,
SPELL_CORRECTION`.

---

## Anti-Pattern 2: Inventing a maturity label or a wrong SNIPPET range

**What the LLM generates:** "the Beta `WITH SNIPPET` clause (GA in Spring '23)…" or a
`target_length` range like "up to 500 characters."

**Why it happens:** models pattern-fill GA/Beta labels and half-remember numeric limits. The
syntax page and the snippet detail page differ superficially, and the model picks the wrong one.

**Correct pattern:** the docs give no GA/Beta/Pilot label for these clauses — do not assert one.
The dedicated `WITH SNIPPET` reference states the range is 50–1,000 characters, default 300.

**Detection hint:** any "Generally Available"/"Beta"/"Pilot" claim without a release-notes
citation, or a `target_length` bound other than 50–1,000.

---

## Anti-Pattern 3: Using DATA CATEGORY without the required RETURNING + WHERE PublishStatus

**What the LLM generates:** a bare `FIND {x} WITH DATA CATEGORY ...` with no `RETURNING`, or a
`RETURNING KnowledgeArticleVersion (Id)` with no `WHERE PublishStatus`.

**Why it happens:** the model treats `DATA CATEGORY` like an independent filter and omits the
structural requirements the clause depends on.

**Correct pattern:**

```sql
FIND {x} RETURNING KnowledgeArticleVersion (Id, Title WHERE PublishStatus='online')
  WITH DATA CATEGORY Geography__c ABOVE Europe__c
```

**Detection hint:** a `WITH DATA CATEGORY` query missing `RETURNING`, or a `RETURNING` article
spec with no `PublishStatus` predicate.

---

## Anti-Pattern 4: Combining data-category specs with OR / AND NOT

**What the LLM generates:** `WITH DATA CATEGORY Product__c AT A__c OR Region__c AT B__c` or an
`AND NOT` between category specs.

**Why it happens:** SQL/SOQL boolean logic makes `OR`/`NOT` between predicates feel natural, but
`DATA CATEGORY` only supports joining multiple specifiers with `AND`.

**Correct pattern:**

```sql
... WITH DATA CATEGORY Product__c AT A__c AND Region__c AT B__c
```

**Detection hint:** an `OR`, `AND NOT`, or `NOT` operator appearing between `DATA CATEGORY`
specifiers.

---

## Anti-Pattern 5: Assuming HIGHLIGHT works on any field type

**What the LLM generates:** advice that `WITH HIGHLIGHT` will emphasize matches in picklist,
number, formula, or rich-text-area fields, or that it highlights an unlimited number of records.

**Why it happens:** "highlight the matches" reads as a universal presentation feature, so the
model omits the documented field-type and record-count constraints.

**Correct pattern:** state that highlighting works only on auto number, email, text, text area,
and long text area fields, and that a maximum of 25 records per entity per query are highlighted
(API 39.0+, custom fields/objects 40.0+).

**Detection hint:** any claim that `HIGHLIGHT` covers picklist/number/formula/rich-text fields,
or that omits the 25-records-per-entity cap.

---

## Anti-Pattern 6: Expecting SNIPPET/HIGHLIGHT output on a wildcard search

**What the LLM generates:** a `FIND {custom*}` query wired to render snippets or `<mark>`
highlights, presented as if the shaping will appear.

**Why it happens:** the model treats wildcards and result-shaping as independent features and
doesn't surface that one suppresses the other.

**Correct pattern:** note that snippets aren't displayed and wildcard terms aren't highlighted;
use complete terms when the excerpt/highlight matters, or drop the shaping expectation for
wildcard searches.

**Detection hint:** a `FIND` term containing `*` or `?` alongside `WITH SNIPPET` or
`WITH HIGHLIGHT` with no caveat that the shaping won't be generated.
