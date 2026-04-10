# Gotchas — AMPscript Development

Non-obvious Salesforce Marketing Cloud platform behaviors that cause real production problems in AMPscript development.

## Gotcha 1: Data Extension Primary Keys Cannot Be Changed After Creation

**What happens:** Once a Data Extension is created and its primary key field(s) are set, the PK configuration is permanent. There is no UI or API mechanism to change which field(s) serve as the primary key on an existing DE. Teams that set `EmailAddress` as the PK and later discover they need `ContactKey` as the PK must create a new DE, migrate data, update all AMPscript `Lookup` calls, and retire the old DE.

**When it occurs:** This becomes critical when the business changes its identifier strategy (e.g., moving from email-based to contact-key-based identity), when the initial DE was created without a canonical identity field, or when a merge/deduplication need requires a composite PK that the original DE does not support.

**How to avoid:** Before creating any DE, confirm the stable, unique subscriber identifier that will be used as the PK — typically `ContactKey` or `SubscriberKey` for subscriber-scoped DEs. Document the PK choice in the DE design record. Run `search_knowledge.py "data extension design"` and consult the `data-extension-design` skill before creating lookup DEs that AMPscript will query.

---

## Gotcha 2: Generic Preview Does Not Evaluate AMPscript Lookup Calls

**What happens:** When an email is previewed in Email Studio without a subscriber selected (the default "generic preview"), all `Lookup()`, `LookupRows()`, `AttributeValue()`, and `IF` conditions that depend on subscriber data return empty strings rather than errors. The email visually appears correct — all personalization slots are blank, which looks like "it needs a subscriber to show real data." Teams accept this and send to production without catching logic errors, broken variable references, or missing ELSE branches.

**When it occurs:** Every time a content author or developer uses the generic preview tab rather than the "Preview by Contact" mode with a real subscriber record selected. Automated test sends to non-personalized seed addresses also exhibit this behavior if the seed address has no matching records in the lookup DEs.

**How to avoid:** Always test AMPscript personalization by previewing with a specific subscriber contact selected (Preview → Preview by Contact → choose a subscriber with known DE data). Additionally, send to a seed list that contains records matching each conditional branch (a Platinum, Gold, Silver, and no-tier subscriber) to validate all IF/ELSEIF/ELSE paths render correctly before the production send.

---

## Gotcha 3: Block Syntax in Subject Lines Renders as Literal Text

**What happens:** Placing `%%[ SET @x = AttributeValue("Field") ]%%` or any `%%[ ... ]%%` block in the email subject line or preheader field causes Marketing Cloud to render the literal block text — including the `%%[` and `]%%` delimiters — to every subscriber's inbox. The platform does not evaluate block syntax in these fields; it only evaluates inline `%%= expression =%%` syntax.

**When it occurs:** This typically happens when a developer writes the logic in the body, confirms it works, then copies the same pattern into the subject line field. It also occurs when subject line templates are shared from a different platform or tool that uses a different syntax convention.

**How to avoid:** Subject line and preheader personalization must use only `%%=AttributeValue("FieldName")=%%` or `%%=Lookup("DE", "Field", "MatchField", _subscriberkey)=%%` inline syntax. Any variable computation needed in the subject (e.g., conditional text) must be set in a body-level `%%[ ... ]%%` block and then referenced inline in the subject via `%%=v(@varName)=%%`. Test with a test send rather than UI preview only.

---

## Gotcha 4: LookupRows() Silently Caps at 2,000 Rows Without Error

**What happens:** `LookupRows()` returns a maximum of 2,000 rows regardless of how many matching records exist in the DE. When a subscriber has more than 2,000 matching rows, the function returns exactly 2,000 in an unspecified order with no warning, no error, and no indication of truncation. FOR loops that assume completeness will silently produce incomplete output.

**When it occurs:** This affects high-volume transactional DEs (order history, event log, product interaction history) where power users accumulate thousands of records. It also affects non-subscriber-scoped DEs where the match field is not the subscriber key, causing many rows to match.

**How to avoid:** Use `LookupOrderedRows("DE_Name", N, "SortField", "DESC", "MatchField", @value)` with an explicit row cap when subscriber data volume could be large. This makes the limit intentional and deterministic. For email use cases, displaying more than 5–10 rows is rarely appropriate; set the cap accordingly. If a complete dataset is truly required, move the aggregation to a SQL Query Activity pre-send and store the result in a flat DE row per subscriber.

---

## Gotcha 5: Smart Quotes and Non-ASCII Characters Cause Silent Parse Failures

**What happens:** AMPscript requires straight ASCII double quotes (`"`) in all string literals and function arguments. Copying AMPscript from Word, Google Docs, Outlook, or a rich-text HTML editor frequently introduces Unicode curly/smart quotes (`"` U+201C, `"` U+201D) or smart apostrophes (`'` U+2019). The Marketing Cloud parser fails silently — it either renders the block as empty, skips the lookup, or in some cases generates a generic "script error" at send time without identifying the offending character.

**When it occurs:** Any time AMPscript is authored or reviewed outside of the Marketing Cloud content editor or a plain-text editor. Common in handoff workflows where content is drafted in Word or a ticket system and then pasted into Email Studio.

**How to avoid:** Always author AMPscript in the Marketing Cloud content editor, in VS Code with a plain-text file, or another editor set to use straight quotes. When pasting from another source, run a find-and-replace for smart quotes before saving. A detection regex for smart quotes in AMPscript: look for `\u201C`, `\u201D`, `\u2018`, `\u2019` in the raw HTML source of the email.

---

## Gotcha 6: _subscriberkey Is Case-Sensitive in Some Contexts

**What happens:** The system variable `_subscriberkey` (all lowercase) is the canonical reference to the current subscriber's key during an email send. In some older content blocks or Cloud Page contexts, practitioners use `_SubscriberKey` (mixed case) or `SubscriberKey` (without underscore). AMPscript variable names are case-insensitive, but the system variable `_subscriberkey` must match the platform's defined name exactly — the underscore prefix is required and the casing matters in some execution contexts.

**When it occurs:** Primarily affects Cloud Page AMPscript where the send context differs from email, and in older content blocks migrated from legacy Email Studio versions.

**How to avoid:** Use `_subscriberkey` (lowercase, underscore prefix) consistently in all AMPscript. When migrating old content, search for alternate casings and normalize. If `_subscriberkey` returns empty in a Cloud Page context, the page may be accessed outside a send context — use `QueryParameter("subkey")` to pass the key via URL parameter for landing page scenarios.
