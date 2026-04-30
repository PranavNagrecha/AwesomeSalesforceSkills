# LLM Anti-Patterns — Lookup Filter Cross Object Patterns

Common mistakes AI coding assistants make when generating or advising on lookup filters.

## Anti-Pattern 1: Inventing function calls in the filter expression

**What the LLM generates:** `TRIM(Contact.Name) equals $Source.Display_Name__c` or `IF(... , ... , ...)` inside the filter.

**Why it happens:** The LLM transfers formula-field syntax onto lookup filters because both look like declarative expressions in the UI.

**Correct pattern:**

```text
Contact.AccountId  equals  $Source.AccountId
```

The grammar is strictly `field operator field-or-value`. To use a transformed value, build a formula field on the relevant object first, then reference that field in the filter.

**Detection hint:** Any open paren in the filter expression — `(`, `TRIM(`, `IF(`, `TEXT(` — is wrong.

---

## Anti-Pattern 2: Two-hop traversal on `$Source`

**What the LLM generates:** `User.Region__c equals $Source.Account.Owner.Region__c`

**Why it happens:** The LLM extrapolates from cross-object formula syntax where multi-hop traversal is fine.

**Correct pattern:** Add `Account.Owner_Region__c` (a formula on Account that resolves `Owner.Region__c`), then `User.Region__c equals $Source.Account.Owner_Region__c`.

**Detection hint:** Count dots after `$Source.` — more than two segments after `$Source.` (e.g., `$Source.A.B.C`) is invalid.

---

## Anti-Pattern 3: Using the filter as a security boundary

**What the LLM generates:** "We can prevent users from selecting confidential accounts by filtering the Account lookup on `IsConfidential__c = false`."

**Why it happens:** The LLM treats UI affordances as security.

**Correct pattern:** Lookup filters are UX guidance, not access control. Confidential records should be hidden via OWD + sharing rules + field-level security. A user with the record ID can still paste it via API.

**Detection hint:** Any time the LLM frames a lookup filter as "preventing access," "blocking visibility," or "hiding records from unauthorized users."

---

## Anti-Pattern 4: Suggesting "Modify All Data" as the bypass

**What the LLM generates:** "Grant the integration user the 'Modify All Data' permission and the lookup filter will be skipped."

**Why it happens:** The LLM conflates the admin-bypass setting (profile-scoped) with broad permissions.

**Correct pattern:** Admin bypass is profile-name-matched and only matches the literal `System Administrator` profile. Permission-set permissions do not bypass. Either change the integration user's profile or rewrite the filter to include `OR($Profile.Name = "Integration", ...)`.

**Detection hint:** Any mention of "Modify All Data," "View All Data," or generic permission strings as the filter-bypass mechanism.

---

## Anti-Pattern 5: Skipping the optional-first staging step

**What the LLM generates:** A required filter deployed straight to production with no migration plan.

**Why it happens:** The LLM treats the request as "implement this constraint" instead of "introduce this constraint to a system with existing data."

**Correct pattern:** Stage as optional → measure violators with a report → backfill or grant temporary bypass → flip to required.

**Detection hint:** Any "deploy this filter as required" recommendation without an explicit step that counts existing-record violations first.
