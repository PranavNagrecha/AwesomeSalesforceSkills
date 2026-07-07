# Gotchas — Development Documentation Standards

Non-obvious behaviors that cause real problems when documenting Salesforce code. The theme:
ApexDoc is a convention, so the failure mode is *silent* — nothing errors, the docs are just
wrong or missing.

## Gotcha 1: The compiler never validates ApexDoc

**What happens:** a `@param` that names a renamed parameter, a `@return` on a `void` method,
or a class with no doc block at all compiles and deploys cleanly.

**When it occurs:** always — the Apex compiler enforces ordinary comment syntax but does not
enforce ApexDoc syntax or check that a comment matches the code beneath it.

**How to avoid:** treat documentation accuracy as a review-and-CI responsibility. Run the
skill's checker; make coverage a code-review gate. Never assume "it compiled" means "it's
documented correctly."

---

## Gotcha 2: `/*` vs `/**` silently drops the block

**What happens:** the code looks documented in the editor, but generated docs are empty for
that element.

**When it occurs:** the block opens with a single asterisk (`/*`). That's an ordinary
multiline comment; documentation generators only recognize `/**`.

**How to avoid:** always open ApexDoc with `/**` and end with `*/`. The checker flags
declarations whose only preceding comment is a `/*` block.

---

## Gotcha 3: A detached block documents nothing

**What happens:** a perfectly-formed ApexDoc block is ignored and the declaration reads as
undocumented.

**When it occurs:** something sits between the block and the declaration — a blank line, a
statement, or an annotation placed *above* the comment instead of below it.

**How to avoid:** the block must **immediately precede** the class/method/constructor/property.
Place annotations (`@AuraEnabled`, `@isTest`) between the doc block and the declaration, not
above the block.

---

## Gotcha 4: `@return` on a void method or constructor

**What happens:** the tag is meaningless and signals the doc was copy-pasted without reading
the signature; reviewers stop trusting the block.

**When it occurs:** a `@return` is added to a `void` method or a constructor, or omitted from a
non-`void` method.

**How to avoid:** `@return` belongs on non-`void` methods only. Void methods and constructors
get a description plus `@param`/`@throws` as needed — never `@return`.

---

## Gotcha 5: Inventing naming rules instead of adopting the official ones

**What happens:** a team writes a "standard" that contradicts Salesforce's prescribed
conventions, and code, tooling, and new hires fight it.

**When it occurs:** the standard is authored from personal preference rather than the official
Apex conventions (capital-first classes, lowercase verb-first methods, meaningful variables,
Java standards otherwise).

**How to avoid:** adopt the official conventions verbatim as the baseline and layer only
genuinely org-specific additions (prefixes, object naming) on top.

---

## Gotcha 6: Asserting a maturity level ApexDoc doesn't have

**What happens:** output claims ApexDoc is a "GA feature since Spring '25" or similar.

**When it occurs:** a maturity label is pattern-filled onto what is actually a documentation
convention and coding guideline, not a licensed or version-gated feature.

**How to avoid:** describe ApexDoc as a comment convention. Do not state GA/Beta/Pilot — the
official docs don't.
