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

---

## Anti-Pattern 7: Claiming Shield Plaintext Is Gated by a "View Encrypted Data" Permission

**What the LLM generates:** "Assign the *View Encrypted Data* permission to the profiles that need plaintext; users without it will see the value masked as `*********`." Common variants: a rollout checklist item "grant View Encrypted Data to integration users," a warning that middleware will start receiving blanks after encryption is enabled, or the claim that removing the permission is a way to restrict who can read an encrypted SSN.

**Why it happens:** Salesforce has two unrelated encryption features and the model merges them. Classic Encryption (the *Encrypted Text* custom field type, still supported) genuinely does mask with asterisks and genuinely is governed by **View Encrypted Data**. Shield Platform Encryption is the newer, differently-architected feature, and Salesforce dropped the permission requirement for it beginning **Spring '17** (KB 000382508, "View Encrypted Data Permission Not Needed with Shield Platform Encryption Beginning Spring '17"). Pre-2017 blog posts, admin cheat sheets and certification study notes overwhelmingly describe the Classic behaviour, and both features are called "encryption" in the same Setup tree.

**Why this one is dangerous:** it fails in the *exposure* direction and it fails silently. The team believes it has applied a need-to-know control; the platform applied none. Every user who could read the field before encryption still reads plaintext after it, and because the Encryption Statistics page reports 100% success the rollout looks complete. Encryption converts a would-be FLS project into a checked box.

**Correct pattern:**

```
Shield Platform Encryption is TRANSPARENT above the storage layer.
  - Anyone with field-level security Read on the field sees plaintext.
  - Anyone without FLS Read sees nothing — there is no masked rendering.
  - There is no per-field decrypt permission of any kind.

To restrict who sees an encrypted value, edit field-level security.
Encryption and access control are orthogonal workstreams; shipping one
does not deliver the other.

Administering Shield needs: Customize Application + Manage Encryption Keys.
Those govern setup and key operations, not read access.

"View Encrypted Data" applies ONLY to Classic Encrypted Text fields.
```

**Detection hint:** grep for `View Encrypted Data` in the same document as `Shield`, `Platform Encryption`, `tenant secret`, `deterministic`, or `probabilistic` — the permission cannot legitimately co-occur with any of them. Also flag the literal mask string `*********` or `*******` alongside Shield vocabulary; Shield produces no asterisks. In a permission-set metadata diff, `<name>ViewEncryptedData</name>` proposed as part of a Shield rollout is the executable form of the same error.

---

## Anti-Pattern 8: Inventing Encryptable Custom Field Types (Number, Checkbox, Currency)

**What the LLM generates:** An encryptable-types list that reads "Text, Long Text Area, Text Area, Phone, URL, Email, Date, Date/Time, Number (limited), Checkbox." The hedge — "Number (limited)", "Number (in some cases)", "Currency where supported" — is the tell: it makes an invented entry look researched.

**Why it happens:** The model knows the shape of the answer (a list of common custom field data types) and completes it with the rest of the Setup field-type picker rather than with the documented subset. Field-type enumerations are exactly the kind of list an LLM will pad to look complete.

**Correct pattern:**

```
Encryptable CUSTOM field types — the complete list:
  Email, Phone, Text, Text Area, Text Area (Long), Text Area (Rich),
  URL, Date, Date/Time

NOT encryptable: Number, Checkbox, Currency, Percent, Formula, Reference
(lookup), Auto-Number, Roll-Up Summary, Geolocation, Picklist, Id.

Consequence for design: a numeric identifier that must be encrypted
(SSN, account number, policy number) has to be modelled as Text.
Decide this at schema-design time — changing the type after data exists
is a migration, not a field edit.
```

**Detection hint:** in any "fields you can encrypt" list, the tokens `Number`, `Checkbox`, `Currency`, `Percent`, `Picklist` or `Geolocation` are always wrong. A parenthetical hedge (`(limited)`, `(partial)`, `(in some cases)`) attached to a field type in such a list is a strong fabrication signal on its own. In metadata, a `<fields>` block whose `<type>Number</type>` sits next to `<encryptionScheme>` will fail deployment.
