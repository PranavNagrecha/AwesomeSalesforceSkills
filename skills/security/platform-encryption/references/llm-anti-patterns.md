# LLM Anti-Patterns — Platform Encryption

Common mistakes AI coding assistants make when generating or advising on Salesforce Shield Platform Encryption.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Probabilistic Encryption on Filterable Fields

**What the LLM generates:** "Enable encryption on Contact.Email using the default probabilistic scheme" without checking whether SOQL filters depend on that field.

**Why it happens:** Probabilistic is the default and provides stronger confidentiality. LLMs default to the strongest option without assessing the filterable requirement.

**Correct pattern:**

```
Before choosing an encryption scheme, classify each field:
- If the field appears in ANY SOQL WHERE clause, list view filter, report filter,
  duplicate rule, or automation criteria → use Deterministic encryption.
- If the field is display-only and never filtered → use Probabilistic encryption.

Probabilistic encryption silently breaks SOQL filters — queries return zero
results rather than an error. This can corrupt reports and integrations without
any exception being thrown.
```

**Detection hint:** If the advice uses probabilistic encryption on Email, Phone, or any field used in lookup matching or deduplication, SOQL filters will silently break.

---

## Anti-Pattern 2: Assuming Encryption Retroactively Applies to Existing Data

**What the LLM generates:** "Enable the encryption policy on the field and all data will be encrypted."

**Why it happens:** LLMs assume enabling a policy is a one-step operation. Training data does not consistently emphasize the re-encryption requirement.

**Correct pattern:**

```
Enabling an encryption policy encrypts only NEW writes going forward. Existing
records remain unencrypted until a separate re-encryption job is explicitly
initiated and completes. The re-encryption job is asynchronous and can affect
platform performance. Always plan and schedule re-encryption as a distinct step
after enabling the policy.
```

**Detection hint:** If the advice enables encryption without mentioning the re-encryption job for existing data, the implementation is incomplete.

---

## Anti-Pattern 3: Attempting to Encrypt Formula or Lookup Fields

**What the LLM generates:** "Encrypt the formula field that displays the full account number" or "Encrypt the lookup field to protect the relationship."

**Why it happens:** LLMs generate field-agnostic encryption recommendations. They do not check field type eligibility against the platform constraint list.

**Correct pattern:**

```
Shield Platform Encryption CANNOT encrypt:
- Formula fields (calculated at read time)
- Lookup relationship fields and external lookup fields
- Auto-Number fields
- Roll-Up Summary fields
- Fields encrypted with Classic Encrypted Text
- Fields used in criteria-based sharing rules

For formula fields containing sensitive data, restrict access via FLS or
redesign the field as a non-formula field that can be encrypted.
```

**Detection hint:** If the advice recommends encrypting a formula, lookup, auto-number, or roll-up summary field, it is proposing an unsupported configuration.

---

## Anti-Pattern 4: Ignoring the Irreversible Enhanced Lookups Side Effect

**What the LLM generates:** "Encrypt the Name field on the Account object" without mentioning the irreversible switch to enhanced lookups.

**Why it happens:** Training data treats Name field encryption as equivalent to any other field encryption. The enhanced lookups side effect is a non-obvious platform behavior.

**Correct pattern:**

```
Encrypting the Name field on any object automatically and IRREVERSIBLY switches
lookups to enhanced lookups. Enhanced lookups only search recently accessed
records rather than all records. This cannot be undone.

Before encrypting the Name field:
- Confirm users understand the lookup behavior change.
- Test in a sandbox to validate that lookup search still meets user expectations.
- Document the decision as a permanent architectural choice.
```

**Detection hint:** If the advice encrypts the Name field without mentioning enhanced lookups and their irreversibility, a critical side effect is hidden.

---

## Anti-Pattern 5: Recommending Cache-Only Keys Without Availability Planning

**What the LLM generates:** "Use Cache-Only Keys for the strongest security — the key is never stored in Salesforce."

**Why it happens:** LLMs rank options by security strength. Cache-Only Keys are the strongest key management option, so LLMs recommend them without modeling the availability tradeoff.

**Correct pattern:**

```
Cache-Only Keys fetch the key from an external service (AWS KMS, Azure Key Vault)
at every read. If the external key service is unavailable, ALL encrypted data
becomes completely unreadable — users receive errors, not decrypted values.

Before choosing Cache-Only Keys:
- Confirm the external key service SLA is equal to or better than Salesforce SLA.
- Design a failover plan for key service outages.
- Consider BYOK as an alternative that provides key control without a runtime
  availability dependency.
```

**Detection hint:** If the advice recommends Cache-Only Keys without discussing the availability dependency and SLA alignment, the risk is understated.

---

## Anti-Pattern 6: Claiming Deterministic Encryption Supports LIKE and SOSL

**What the LLM generates:** "Use deterministic encryption so you can search encrypted fields with LIKE or SOSL."

**Why it happens:** LLMs generalize from the fact that deterministic encryption supports some SOQL operations. Training data does not consistently distinguish between equality operators and wildcard/full-text search.

**Correct pattern:**

```
Deterministic encryption supports ONLY equality-based SOQL operators:
  =, !=, IN, NOT IN, and case-insensitive matching.

It does NOT support:
  LIKE (wildcard), range comparisons (>, <, >=, <=), ORDER BY, GROUP BY,
  or SOSL full-text search.

There is no Shield encryption option that supports partial-match search.
If wildcard or full-text search is required, the field cannot be encrypted.
```

**Detection hint:** If the advice claims LIKE, range, or SOSL works on deterministically encrypted fields, the capability is overstated.
