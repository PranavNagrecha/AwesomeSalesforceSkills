# Gotchas — Duplicate Rule Person Account Edge Cases

Non-obvious Salesforce platform behaviours that bite real B2C / Person Account deployments.

---

## Gotcha 1: A match rule built on Contact does not catch PA dedupes from the Account UI

**What happens:** an admin builds the consumer match rule on `Contact` (referencing `Email`, `MobilePhone`, etc.), reasoning "the Person Contact has the email." The Contact-targeted rule fires when somebody edits the Person Contact directly, but the Account-list-view "New Person Account" path writes to the Account side first, and lead-convert that lands on PA fires the **Account**-targeted rule. Both code paths bypass the Contact-targeted rule entirely.

**When it occurs:** every B2C org where the rule was authored from a Contact-flavoured B2B mental model.

**How to avoid:** build the canonical PA match rule on `Account`, target Person fields (`PersonEmail`, `PersonMobilePhone`), and gate with `IsPersonAccount = true`. A separate Contact-targeted rule is fine as defence-in-depth but is not the primary line.

---

## Gotcha 2: `IsPersonAccount` filter is silently optional at metadata-deploy time

**What happens:** the metadata deploy succeeds even when the match formula has no `IsPersonAccount` clause. There is no validation warning. In a mixed B2B + B2C org, the rule then matches Acme Corp against Acme Smith because both have similar `Name` strings.

**When it occurs:** any rule cloned from a B2B template, deployed without review, into a PA-enabled org.

**How to avoid:** treat `IsPersonAccount` as a load-bearing match item. The skill-local checker (`scripts/check_duplicate_rule_person_account_edge_cases.py`) flags its absence as a P0. Add it even on B2C-only orgs as future-proofing.

---

## Gotcha 3: Phone matching without normalization fails on user-entered formatting

**What happens:** the rule uses `matchingMethod = Exact` on `PersonMobilePhone`. User A enters `+1 (555) 010-1234`, user B enters `5550101234`, user C enters `+15550101234`. None of these match each other under `Exact` — but they are the same number. Real duplicates slip through.

**When it occurs:** any rule that picks `Exact` for a phone field instead of the platform's `Phone` matching method (which strips formatting, country codes, and parentheses).

**How to avoid:** use `matchingMethod = Phone` on every phone field item. For cross-region matching where the country code itself varies, store an E.164-normalized value in a custom field via a before-save Flow and match the custom field with `Exact`.

---

## Gotcha 4: Lead-to-PA convert evaluates the Account rule, not a (non-existent) "PA rule"

**What happens:** team configures a Lead-targeted Duplicate Rule and assumes convert is covered. Convert lands on Person Account; the resulting `001` row collides with an existing PA; no rule fires; the org now has two PAs for the same consumer.

**When it occurs:** every B2C org where the team did not realize convert runs the *target*-object rule.

**How to avoid:** always pair a Lead-targeted rule with an Account-targeted, PA-aware rule. Even better: use cross-object match items on the Lead-targeted rule so the dup is surfaced *before* convert (`Lead.Email` ↔ `Account.PersonEmail`).

---

## Gotcha 5: Deleting a Person Account cascades — do not script "delete the Contact only"

**What happens:** a privacy-engineering team writes a "right-to-be-forgotten" Apex job that does `delete contactRecord` for the Person Contact (`003`). The DML fails with `INVALID_CROSS_REFERENCE_KEY` or similar — the platform refuses to delete the Person Contact independently of its Account row.

**When it occurs:** GDPR / DSAR workflows authored from a B2B Contact mental model.

**How to avoid:** delete the **Account** row (`001`). The platform automatically removes the synced Person Contact (`003`) in the same transaction. Document this in the retention runbook so future engineers do not re-discover it.

---

## Gotcha 6: Fuzzy CompanyName method on a person name produces noise

**What happens:** a B2B rule cloned to B2C keeps `Fuzzy: Company Name` on the Account.Name field. CompanyName fuzzy is tuned to ignore corporate suffixes (`Inc`, `LLC`, `Co`). Applied to "Smith, John" vs "Smyth, Jon" it under-matches; applied to common surnames it over-matches.

**When it occurs:** any rule that copy-pasted the matching method from a B2B template.

**How to avoid:** for PA names use `Fuzzy: First Name` and `Fuzzy: Last Name` *separately*, not `Fuzzy: Company Name` on the composed `Name` field. Pair with a high-cardinality field (PersonEmail / PersonMobilePhone) to suppress false positives.

---

## Gotcha 7: `LOWER()` wrapper on Email match field is a no-op or worse

**What happens:** an LLM (or a junior admin) "fixes" perceived case-sensitivity by wrapping the match item or duplicate-rule formula in `LOWER(PersonEmail)`. Either the platform rejects it (formula context mismatch) or the rule starts comparing the lowercased value against the raw stored value and matches *fewer* records than before.

**When it occurs:** any time someone "improves" an email match without realizing it is already case-insensitive.

**How to avoid:** the `Exact` matching method on an Email-type field is case-insensitive by Salesforce default. Leave it alone. The Email type itself enforces canonicalization on save.

---

## Gotcha 8: `PersonEmail` referenced in a non-PA-enabled org fails deploy

**What happens:** a sandbox without Person Accounts enabled rejects a metadata deploy that references `Account.PersonEmail` — the field literally does not exist until PA is enabled.

**When it occurs:** developer sandboxes or scratch orgs that were not provisioned with PA, into which a B2C metadata package is being pushed.

**How to avoid:** ensure PA is enabled on every target org before deploying PA-aware rules. Salesforce Support must enable PA in production; in scratch orgs use the `PersonAccounts` feature in `project-scratch-def.json`. Validate the feature is on with `SELECT Id FROM Account WHERE IsPersonAccount = true LIMIT 1` (or use Schema describe).

---

## Gotcha 9: Standard duplicate-job UI hides results when matching rule is inactive

**What happens:** an admin deactivates a matching rule to edit it, runs a duplicate job from Setup, sees zero results, panics. The job ran against the *active* matching rules — the one being edited contributed nothing.

**When it occurs:** every iteration cycle on a matching rule.

**How to avoid:** matching-rule activation/deactivation costs a few minutes (the rule has to be re-indexed). Plan rule edits in a sandbox. In production, schedule the duplicate job after re-activation has fully indexed (Setup → Duplicate Rules → Matching Rule status shows `Active`).
