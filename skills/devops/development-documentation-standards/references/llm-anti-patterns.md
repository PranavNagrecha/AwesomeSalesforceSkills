# LLM Anti-Patterns — Development Documentation Standards

Common mistakes AI coding assistants make when generating or advising on Salesforce
documentation standards. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: `@return` on a `void` method or constructor

**What the LLM generates:** an ApexDoc block for a `void` method (or a constructor) that
includes a `@return` tag, often `@return void` or `@return Nothing`.

**Why it happens:** the model has seen thousands of documented non-`void` methods and
reflexively emits the full tag set regardless of the actual signature.

**Correct pattern:**

```apex
/**
 * Recalculates and persists the rollup.
 * @throws DmlException if the update cannot be committed.
 */
public void refreshRollup() { /* no @return */ }
```

**Detection hint:** grep for `@return` in a block whose declaration is `void ` or is a
constructor (method name equals the class name, no return type). The checker flags this.

---

## Anti-Pattern 2: JavaDoc bleed — wrong or unsupported tags

**What the LLM generates:** JavaDoc/Javadoc-only tags that ApexDoc doesn't define, such as
`@exception` (instead of `@throws`), `@serial`, `@inheritDoc`, or `{@value}`.

**Why it happens:** ApexDoc is JavaDoc-derived, so the model reaches for the full JavaDoc tag
set rather than the Apex-specific subset.

**Correct pattern:** use the ApexDoc vocabulary only — block tags `@param @return @throws
@author @deprecated @example @group @see @since @version`; inline tags `{@code} {@link}
{@literal} {@hidden}`. Use `@throws`, not `@exception`.

**Detection hint:** any tag outside that list — especially `@exception`, `@inheritDoc`,
`{@value}`, `@serial` — is JavaDoc bleed.

---

## Anti-Pattern 3: `@param` tags that drift from the signature

**What the LLM generates:** `@param` tags whose names or order don't match the method
parameters — leftover tags after a refactor, or invented parameter names.

**Why it happens:** the model documents the *concept* of the method rather than reading its
exact current signature, and doesn't re-check names/order.

**Correct pattern:** one `@param` per parameter, in signature order, using the exact parameter
name:

```apex
/**
 * @param accountName ...
 * @param industry ...
 */
public Account createAccount(String accountName, String industry) { /* ... */ }
```

**Detection hint:** the count of `@param` tags differs from the parameter count, or a tag names
an identifier not in the parameter list. The checker reports both.

---

## Anti-Pattern 4: Single-asterisk block that isn't ApexDoc

**What the LLM generates:** a well-formed-looking doc block opened with `/*` instead of `/**`.

**Why it happens:** ordinary multiline comments (`/* ... */`) are far more common in training
data than the two-asterisk ApexDoc opener.

**Correct pattern:**

```apex
/**   <-- two asterisks
 * Creates an account.
 */
```

**Detection hint:** a comment block containing `@param`/`@return`/`@throws` that opens with
`/*` but not `/**` is a dropped ApexDoc block.

---

## Anti-Pattern 5: Asserting a GA/Beta maturity for ApexDoc

**What the LLM generates:** "ApexDoc is a GA feature introduced in Spring '25" or "the Beta
ApexDoc parser," attaching a maturity label to a documentation convention.

**Why it happens:** models pattern-fill release/maturity language onto anything that sounds
like a platform feature.

**Correct pattern:** describe ApexDoc as a standardized *comment convention and coding
guideline*. State no GA/Beta/Pilot status — the official docs don't give one.

**Detection hint:** any "Generally Available", "Beta", "Pilot", or "introduced in <release>"
claim about ApexDoc without a release-notes citation.

---

## Anti-Pattern 6: Documenting the obvious instead of the contract

**What the LLM generates:** noise like `@param accountName The account name` or a summary that
restates the method name (`createAccount` → "Creates an account"), adding no information.

**Why it happens:** the model fills every tag to look thorough, echoing the identifier rather
than describing constraints, side effects, and failure modes.

**Correct pattern:** document what the signature can't say — valid ranges, null-handling, side
effects, and which exceptions fire when (`@param accountName The name; must not be blank`,
`@throws ... if accountName is blank or the DML fails`).

**Detection hint:** a `@param` description that is the parameter name re-spaced, or a summary
that is the method name re-spaced, with no constraint or behavior added.
