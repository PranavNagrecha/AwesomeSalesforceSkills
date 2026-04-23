# PII Redaction — Gotchas

## 1. Trust Layer ≠ Redaction Done

The Trust Layer is a safety net. Redact before you send to it; the
trust layer is the last line, not the only line.

## 2. Free-Text Fields Hide PII

A "Notes" field can contain SSNs, account numbers, anything. Either
drop free-text fields from prompts or run pattern detection on them.

## 3. Tokenization Collisions

If the tokenizer reuses tokens across conversations, the model may
correlate contexts incorrectly. Scope tokens per conversation.

## 4. Retrieved Knowledge Base Content

RAG retrievers pull KB articles. If KB has PII (an email address in a
sample response), the model sees it. Sanitise the KB corpus, not just
live records.

## 5. System Messages Leak Context

System prompts containing "The user's name is Jane Doe and email is
jane@acme.com" leak on jailbreak. Keep system prompts generic; inject
context via variables.

## 6. Logging The Redacted Value

`System.debug('masked=' + maskedEmail + ' raw=' + c.Email)` — the raw
value is now in the log. Audit debug statements.

## 7. Regex Misses Variants

SSN matches `123-45-6789` but misses `123 45 6789` or `123.45.6789`.
Use validated libraries, not ad-hoc regex, for high-risk categories.

## 8. Cross-Object Leaks Via Joins

Redacting a field on Contact does not redact the same info reached via
a lookup chain (`Opportunity.Account.BillingEmail`). Classification is
per logical datum, not per single object hop.
