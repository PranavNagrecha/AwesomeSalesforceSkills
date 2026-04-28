# Well-Architected Notes — Duplicate Rule Person Account Edge Cases

This skill maps primarily to **Reliability**, **Operational Excellence**, and **Security** in the Salesforce Well-Architected framework. PA-aware duplicate management is a data-quality control AND a PII-handling control — getting it wrong both pollutes the customer record and increases regulated-data exposure.

## Relevant Pillars

- **Reliability** — duplicate management is a *trust* control. A B2C org whose Account-list-view "New Person Account" path silently creates duplicates loses reliability of every downstream metric (revenue per customer, churn, NPS) until the dups are reconciled. The PA-specific failure modes documented here (`IsPersonAccount` filter missing, Contact-targeted rule failing on Account UI, lead-convert evaluating the Account rule) are reliability defects that look fine in isolation but compound silently. Building rules from `templates/duplicate-rule-person-account-edge-cases-template.md` and validating with the skill-local checker keeps the failure modes out of the deploy pipeline.

- **Operational Excellence** — observability and reviewability of the rule set. Each Matching Rule and Duplicate Rule is a piece of metadata under source control (`objects/Account/duplicateRules/*.duplicateRule-meta.xml`, `matchingRules/*.matchingRule-meta.xml`). The skill-local checker runs in CI, so a regression (someone clones a B2B rule to B2C without the PA gate) is caught at PR time. The standard `Phone` matching method centralizes phone normalization in the platform — there is no "but our normalization function returned different results today" debug session.

- **Security (PII)** — `PersonEmail`, `PersonMobilePhone`, `PersonHomePhone`, `FirstName`, `LastName`, and `BillingPostalCode` are PII. A duplicate rule operates on these fields and surfaces them to end users in alert text. Three security implications:
  - **Scope leakage** — a misconfigured rule (no `IsPersonAccount` filter) can show a B2B user a Person Account row's PII via the duplicate alert. Gate explicitly.
  - **Right-to-be-forgotten** — PA delete cascades both `001` and `003`. A retention/erase job that deletes only one side leaves orphaned PII in the other (it actually fails — see Gotcha 5 — but a misguided "fix" that uses System Mode to force the delete will succeed in corrupting state).
  - **Cross-region phone matching** — storing E.164-normalized phone in a custom field for matching is fine, but that custom field is now ALSO PII; ensure FLS and Shield Encryption (if used) are applied consistently.

## Concrete reliability + security wins

| Without PA-aware rule design | With PA-aware rule design |
|---|---|
| Lead-convert silently produces dup PAs | Account-targeted rule fires on convert; dup is blocked |
| `Fuzzy: Company Name` on Account.Name produces person-name false positives | `Fuzzy: First Name` + `Fuzzy: Last Name` paired with `PersonEmail` Exact |
| Privacy-erase script fails or leaves orphans | `delete account` cascades both rows; runbook documents this |
| Phone match fails on `+1 (555) 010-1234` vs `5550101234` | `matchingMethod = Phone` (or normalized custom field) |
| Mixed B2B + B2C produce cross-universe matches | Two rules, each gated by `IsPersonAccount`, no overlap |

## Architectural Tradeoffs

- **Two parallel rules in mixed orgs vs one combined rule.** Combined-with-OR rules look simpler but produce cross-universe noise. Two gated rules cost a small duplicate-job runtime increase but isolate failure modes. Prefer two.
- **Custom-field E.164 normalization vs platform `Phone` matching method.** The platform method is good enough for single-region orgs and free; the custom-field approach is required for cross-region matching but adds a Flow + a PII field to govern. Pick based on customer geography, not on aesthetic preference.
- **Match formula gates vs Duplicate Rule conditions.** `IsPersonAccount = true` can be expressed as a match-rule item OR as a Duplicate Rule condition. Putting it in the match rule means the rule itself is unambiguous about its scope; putting it in the Duplicate Rule allows reusing one match rule across two duplicate rules. Both are valid; pick consistently per org and document in the rule description.
- **Block vs Allow with alert.** Blocking on insert is the safest default for B2C consumer dedupe (creating a dup is almost always wrong). Allowing on update is usually correct (rep editing an existing record should not be blocked by a self-match).

## Anti-Patterns

1. **Cloning a B2B Account match rule to a PA-enabled org without re-tuning** — the `Fuzzy: Company Name` method, the missing `IsPersonAccount` filter, and the absent `PersonEmail` reference all conspire to make the rule worse than no rule at all. Never clone across the B2B/B2C boundary; always author the B2C rule from the template.
2. **Routing PA dedupe through a Contact-targeted rule** — Contact rules do not fire on the Account UI's "New Person Account" path or on lead-convert. Always lead with an Account-targeted rule.
3. **Hand-rolled Levenshtein in formula fields** — Salesforce ships fuzzy matching methods that are tuned and indexed. Hand-rolled string-distance formulas in custom fields run per-row at evaluation time, do not benefit from the matching engine's indexing, and consume formula-evaluation budget.
4. **Privacy-erase scripts that delete the Person Contact directly** — fails or, with a hack to force System Mode, leaves orphan state. Always erase via the Account row.

## Official Sources Used

- **Person Accounts Implementation Guide** — <https://help.salesforce.com/s/articleView?id=sf.account_person.htm&type=5> — canonical description of the dual-record `001` + `003` shape, sync behaviour, and field surface.
- **Considerations for Using Person Accounts** — <https://help.salesforce.com/s/articleView?id=sf.account_person_considerations.htm&type=5> — limitations and edge cases including delete cascade and lead-convert.
- **Duplicate Rules** — <https://help.salesforce.com/s/articleView?id=sf.duplicate_rules_overview.htm&type=5> — duplicate-rule lifecycle, action settings (Block / Allow with alert), evaluation timing.
- **Matching Rules — How They Work** — <https://help.salesforce.com/s/articleView?id=sf.matching_rules_overview.htm&type=5> — match formula semantics, supported matching methods (Exact, Phone, Email, Fuzzy: First Name, Fuzzy: Last Name, Fuzzy: Street, Fuzzy: Company Name).
- **Standard Matching Rules** — <https://help.salesforce.com/s/articleView?id=sf.matching_rules_standard_rules.htm&type=5> — Salesforce-supplied rules including the standard PA matching rule on Account.
- **Object Reference — Account** — <https://developer.salesforce.com/docs/atlas.en-us.object_reference.meta/object_reference/sforce_api_objects_account.htm> — `IsPersonAccount`, `PersonEmail`, `PersonHomePhone`, `PersonMobilePhone` field semantics.
- **Lead Conversion in Person Account Orgs** — <https://help.salesforce.com/s/articleView?id=sf.leads_convert.htm&type=5> — lead-convert paths and which Duplicate Rule fires on convert.
- **Salesforce Well-Architected — Trusted (Secure)** — <https://architect.salesforce.com/well-architected/trusted/secure> — PII handling and security framing for data-quality controls.
- **Salesforce Well-Architected — Reliable** — <https://architect.salesforce.com/well-architected/reliable> — reliability sub-attributes referenced above.
- **GDPR Right to Erasure on Salesforce** — <https://help.salesforce.com/s/articleView?id=sf.individual_object.htm&type=5> and the Privacy and Data Protection on Salesforce trail — informs the "delete the Account, not the Contact" guidance for PA.
