# LLM Anti-Patterns — Platform Encryption

Common mistakes AI coding assistants make when generating or advising on Salesforce Shield Platform Encryption.
These patterns help the consuming agent self-check its own output.

UNVERIFIED (2026-10-20): the field-type eligibility lists in Anti-Patterns 3 and 8, "probabilistic is the default", and the operator limits beyond equals / not equals come from Help pages; the corpus has no eligibility table. Every other claim below carries its corpus line.

## Anti-Pattern 1: Recommending Probabilistic Encryption on Filterable Fields

**What the LLM generates:** "Enable encryption on Contact.Email using the probabilistic scheme" without checking whether SOQL filters depend on that field.

**Why it happens:** Probabilistic provides stronger confidentiality, and the model defaults to the strongest option without assessing the filter requirement.

**Correct pattern:**

```
Before choosing an encryption scheme, classify each field:
- If the field appears in ANY SOQL WHERE clause, list view filter, report filter,
  duplicate rule, or automation criteria -> CaseSensitiveDeterministicEncryption
  or CaseInsensitiveDeterministicEncryption (api_meta 264 L45625-45626).
- If the field is display-only and never filtered -> ProbabilisticEncryption.

Deterministic is the scheme that "lets customers filter on encrypted data"
(api_meta 264 L127865-127866). Whether a filter on a probabilistic field
returns zero rows or an error is not in the corpus - test both.
```

**Detection hint:** If the advice uses probabilistic encryption on Email, Phone, or any field used in lookup matching or deduplication, filters on that field will stop working.

---

## Anti-Pattern 2: Getting Existing Data and History Wrong in Either Direction

**What the LLM generates:** Either "enabling the policy only encrypts new writes, run a re-encryption job for the rest" or "enable the policy and all data, including history, is encrypted."

**Why it happens:** Both are half-remembered. The corpus describes a background process and two exceptions.

**Correct pattern:**

```
- A background encryption process applies the active key material to
  encrypted data (api_meta 264 L127877-127882); after Platform Encryption is
  turned on, existing field values and History related-list rows are
  encrypted (secguide 262 L4899-4902).
- Field-history and feed duplicates are skipped unless
  PlatformEncryptionSettings.enableEncryptFieldHistory = true (default false).
- FieldHistoryArchive copies stay unencrypted until Salesforce re-archives
  them (secguide 262 L4903-4904).
```

**Detection hint:** Advice that never mentions field history or `FieldHistoryArchive`, or that tells the user to "run a re-encryption job" as the only path, is incomplete.

---

## Anti-Pattern 3: Attempting to Encrypt Formula or Lookup Fields

**What the LLM generates:** "Encrypt the formula field that displays the full account number" or "Encrypt the lookup field to protect the relationship."

**Why it happens:** LLMs generate field-agnostic encryption recommendations without checking field type eligibility.

**Correct pattern:**

```
Help-only (UNVERIFIED 2026-10-20) - Shield Platform Encryption cannot encrypt:
- Formula fields, lookup and external lookup fields
- Auto-Number and Roll-Up Summary fields
- Fields already using Classic Encrypted Text (a separate feature,
  secguide 262 L2548)

Corpus-grounded: criteria-based sharing rules can't use encrypted fields
(secguide 262 L3478-3479) - so a field that drives one needs a sharing redesign.
```

**Detection hint:** If the advice recommends encrypting a formula, lookup, auto-number, or roll-up summary field, it is proposing an unsupported configuration.

---

## Anti-Pattern 4: Misdescribing What Name-Field Encryption Does to Lookups

**What the LLM generates:** "Encrypt the Name field on Account" with no mention of lookups — or the opposite overstatement, "enhanced lookups only search recently accessed records."

**Why it happens:** The side effect is non-obvious, and the second form is a confident paraphrase with no source.

**Correct pattern:**

```
Enhanced lookups are "an updated lookup dialog interface that lets users
filter, sort, and page through search results" (api_meta 264 L44309-44311).
Help says Name-field encryption turns them on and that this can't be undone
(UNVERIFIED 2026-10-20). Test lookup search in a sandbox and tell users
before rollout.
```

**Detection hint:** Name-field encryption advice that is silent about lookups, or that says "recently accessed records only", needs correcting.

---

## Anti-Pattern 5: Recommending Cache-Only Keys Without Availability Planning

**What the LLM generates:** "Use Cache-Only Keys for the strongest security — the key is never stored in Salesforce."

**Why it happens:** LLMs rank options by security strength and skip the operational dependency.

**Correct pattern:**

```
Cache-Only Keys let users "apply key material stored outside of Salesforce
to data on demand" (api_meta 264 L118684-118687), fetched through a named
credential (obj 264 L283716-283717), and need the Cache-Only Key Service
add-on (obj 264 L134306). The key service sits on the read path.

Before choosing Cache-Only Keys:
- Confirm the key service's availability matches the org's.
- Turn on enableReplayDetection (api_meta 264 L118689-118692).
- Write an outage runbook (the exact outage behaviour is UNVERIFIED 2026-10-20).
- Consider customer-supplied (BYOK) material for key control without a
  runtime dependency.
```

**Detection hint:** If the advice recommends Cache-Only Keys without discussing the availability dependency, the risk is understated.

---

## Anti-Pattern 6: Claiming Deterministic Encryption Supports LIKE and SOSL

**What the LLM generates:** "Use deterministic encryption so you can search encrypted fields with LIKE or SOSL."

**Why it happens:** LLMs generalize from the fact that deterministic encryption supports some filtering.

**Correct pattern:**

```
Documented operators on deterministic fields: equals and not equals
(api_meta 264 L33328-33329). Two variants: CaseSensitiveDeterministicEncryption
and CaseInsensitiveDeterministicEncryption (L45625-45626).

LIKE, range comparisons, ORDER BY and SOSL are not documented as supported
(the "not supported" statement itself is Help-only, UNVERIFIED 2026-10-20).
If wildcard or full-text search is required, re-evaluate encryption.
```

**Detection hint:** If the advice claims LIKE, range, or SOSL works on deterministically encrypted fields, the capability is overstated.

---

## Anti-Pattern 7: Settling the "View Encrypted Data" Question From Memory

**What the LLM generates:** Either "assign View Encrypted Data so integration users can read the Shield-encrypted SSN; others see `*********`" or the confident opposite, "Shield has no permission of any kind; anyone with FLS Read sees plaintext."

**Why it happens:** Salesforce has two encryption features. Classic Encryption (the *Encrypted Text* field type) masks values and is governed by **View Encrypted Data** (secguide 262 L2486, L2499-2503; note at L2548). For Shield the corpus only says you "can set encrypted data permissions to protect sensitive data from unauthorized users" (secguide 262 L305-306). The "no permission needed since Spring '17" statement lives in Help KB 000382508 and is UNVERIFIED (2026-10-20) here.

**Why this one is dangerous:** either answer, given without a test, can leave a need-to-know requirement unmet while the rollout looks complete.

**Correct pattern:**

```
1. Field-level security is the access control you design and document.
2. "View Encrypted Data" and asterisk masking are documented for Classic
   Encryption (secguide 262 L2486, L2499-2503).
3. For Shield, log in as each affected profile in a sandbox and record who
   sees plaintext before telling an auditor anything.
4. Administering Shield needs Customize Application + Manage Encryption Keys
   (api_meta 264 L127848-127849) - administration, not read access.
```

**Detection hint:** A Shield rollout plan that cites a permission as the read control without a sandbox test, or that rules one out without a test, is asserting something the corpus does not settle.

---

## Anti-Pattern 8: Inventing Encryptable Custom Field Types (Number, Checkbox, Currency)

**What the LLM generates:** An encryptable-types list that reads "Text, Long Text Area, Text Area, Phone, URL, Email, Date, Date/Time, Number (limited), Checkbox." The hedge — "Number (limited)" — is the tell.

**Why it happens:** The model completes a field-type list with the rest of the Setup picker.

**Correct pattern:**

```
Help-only list (UNVERIFIED 2026-10-20) of encryptable CUSTOM field types:
  Email, Phone, Text, Text Area, Text Area (Long), Text Area (Rich),
  URL, Date, Date/Time

Consequence for design: a numeric identifier that must be encrypted
(SSN, account number, policy number) has to be modelled as Text.
Decide this at schema-design time.
```

**Detection hint:** in any "fields you can encrypt" list, a parenthetical hedge (`(limited)`, `(partial)`, `(in some cases)`) attached to a field type is a strong fabrication signal. In metadata, check `<encryptionScheme>` (api_meta 264 L45623) only on field types the current Help list names.
