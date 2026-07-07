# Examples — Development Documentation Standards

All Apex below is illustrative scaffolding authored from the official Apex Developer Guide
ApexDoc pages and naming-conventions page. Replace class/field/method names and namespaces
with your own. ApexDoc is a **comment convention**: the Apex compiler does not validate any
of these tags, so treat the examples as a review target, not a compile guarantee.

## Example 1: Fully-documented class and method

**Context:** a new `AccountService` class other code and agents will consume. You want the
class purpose, the method contract, and a usage example captured in ApexDoc.

**Problem:** a bare `// creates an account` line gives no parameter, return, or exception
contract, is invisible to documentation generators, and gives an AI agent nothing structured.

**Solution:**

```apex
/**
 * Manages Account creation and related operations.
 * @group Account
 * @author Jordan Dev
 * @since 1.0.0
 * @see AccountSelector
 * @example
 * {@code
 * Account a = new AccountService().createAccount('Acme', 'Agriculture');
 * }
 */
public with sharing class AccountService {

    /**
     * Creates a new Account with the given name and industry.
     * @param accountName The name for the new account. Must not be blank.
     * @param industry The industry classification for the new account.
     * @return The inserted Account with its Id populated.
     * @throws AccountService.AccountException if accountName is blank or the DML fails.
     */
    public Account createAccount(String accountName, String industry) {
        if (String.isBlank(accountName)) {
            throw new AccountException('accountName is required');
        }
        Account a = new Account(Name = accountName, Industry = industry);
        insert a;
        return a;
    }

    public class AccountException extends Exception {}
}
```

**Why it works:** the block sits immediately above each declaration, `@param` tags match the
signature order and names, `@return` is present because the method is non-`void`, and the
raised exception has a `@throws`. The `{@code}` inline tag renders the example as code.

---

## Example 2: A `void` method and a constructor

**Context:** a method that mutates state and returns nothing, plus a constructor.

**Problem:** the most common tag error is a `@return` on a method that returns `void` (or on a
constructor) — invalid, and a signal the doc was copied without reading the signature.

**Solution:**

```apex
/**
 * Builds a service bound to a specific business unit.
 * @param unitId The business unit whose records this service operates on.
 */
public AccountService(Id unitId) {
    this.unitId = unitId;
}

/**
 * Recalculates and persists the rollup for the bound unit.
 * @throws DmlException if the update cannot be committed.
 */
public void refreshRollup() {
    // ... no @return here: the method is void
}
```

**Why it works:** constructors and `void` methods take a description plus `@param`/`@throws`
as needed, but never `@return`.

---

## Example 3: Documenting a deprecation

**Context:** an old overload is being retired but callers still reference it.

**Problem:** deleting it breaks callers; leaving it undocumented invites new usage.

**Solution:**

```apex
/**
 * Creates an account by name only.
 * @param accountName The name for the new account.
 * @return The inserted Account.
 * @deprecated Use {@link AccountService#createAccount} (name + industry) instead;
 * this overload leaves Industry null and skips record-type defaulting.
 */
public Account createAccount(String accountName) {
    return createAccount(accountName, null);
}
```

**Why it works:** `@deprecated` states the reason and the `{@link}` inline tag points readers
straight at the successor method, so the retirement is self-documenting.

---

## Example 4: Naming conventions carry half the documentation

**Context:** two versions of the same method — one fighting the conventions, one following them.

```apex
// Against the conventions: noun-ish method name, capitalized, vague variable.
public Account AccountCreation(String x, String y) { /* ... */ }

// Following the official conventions: lowercase verb-first method, meaningful params.
public Account createAccount(String accountName, String industry) { /* ... */ }
```

**Why it works:** Salesforce prescribes capitalized class names, lowercase verb-first method
names, and meaningful variable names. The second signature reads as a sentence with its
`@param`/`@return` tags; the first needs prose to explain what a good name would have said.

---

## Example 5: An org-level design-standards skeleton

**Context:** several developers, inconsistent comments, no agreed rules.

**Problem:** because the compiler never enforces ApexDoc, per-developer discipline drifts.

**Solution:** one central document (see `templates/development-documentation-standards-template.md`)
that pins down:

```text
1. Naming conventions
   - Apex classes: PascalCase, capital first letter
   - Apex methods: lowerCamelCase, verb-first (createAccount, validateInput)
   - Variables: meaningful, no single letters except loop counters
   - Custom objects/fields/automations: <team-agreed prefixes and casing>
2. ApexDoc requirements
   - Required on every public/global class, method, and constructor
   - Required tags: @param (matching signature), @return (non-void only), @throws
   - Deprecations use @deprecated + {@link}
3. Storage
   - The standard and all config/design docs live in <one central location>
4. Enforcement
   - Documentation coverage is a code-review gate; the checker runs in CI
```

**Why it works:** it adopts the official conventions verbatim rather than inventing house
rules, and it closes the enforcement gap the compiler leaves open.

---

## Anti-Pattern: the single-asterisk block

**What practitioners do:** open a doc block with `/*` instead of `/**`.

```apex
/*
 * Creates an account.   <-- one asterisk: NOT ApexDoc
 * @param accountName ...
 */
public Account createAccount(String accountName) { /* ... */ }
```

**What goes wrong:** documentation generators skip the block entirely, so the code looks
documented in the editor but produces empty generated docs — and the compiler says nothing.

**Correct approach:** open ApexDoc blocks with `/**` (two asterisks) and end with `*/`.
