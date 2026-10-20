---
name: development-documentation-standards
description: "Standards for Salesforce dev documentation — README, ADR, runbook, release note templates. Triggers: dev documentation standards, ADR template, runbook Salesforce. NOT for automated release notes — use devops/release-notes-automation."
category: devops
salesforce-version: "Spring '25+"
well-architected-pillars:
  - Operational Excellence
triggers:
  - "document my Apex classes and methods so other developers and AI agents can understand the codebase"
  - "set up ApexDoc comment and naming standards for our development team"
  - "add the right doc tags to an Apex method that has parameters, a return value, and throws an exception"
  - "define org-wide naming and documentation conventions for a Salesforce project and where to store them"
  - "review whether our Apex code is properly documented before a release"
tags:
  - development-documentation-standards
  - apexdoc
  - code-comments
  - naming-conventions
  - design-standards
  - maintainability
inputs:
  - "The Apex class(es) or codebase to document or audit"
  - "Existing team conventions, or the intent to define new ones"
  - "Scope: code-level (ApexDoc + naming) vs org-level (design/documentation standards)"
outputs:
  - "ApexDoc-formatted comment blocks on classes, methods, constructors, and properties"
  - "A written, centrally-stored naming + documentation standard for the project"
  - "A documentation-coverage audit that flags undocumented public surfaces and tag gaps"
dependencies: []
version: 1.0.1
author: Pranav Nagrecha
updated: 2026-10-20
---

# Development Documentation Standards

This skill activates when a practitioner wants to document Salesforce code the way the platform prescribes — chiefly **ApexDoc**, Salesforce's standardized, JavaDoc-derived comment format read by humans, documentation generators, and AI agents — and to codify the naming and design conventions that make an org maintainable. It covers the code-level convention (ApexDoc tags, comment placement, naming rules) and the org-level framing (a written design/documentation standard stored in one central location).

Maturity note: Salesforce documents ApexDoc as a **comment convention and coding guideline** ("We recommend using ApexDoc comments", apexdev 264 L13799-13802), not as a licensed or version-gated feature. The Apex Developer Guide section "Document Your Apex Code" carries no GA, Beta or Pilot stamp (apexdev 264 L13798-13806) — do not assert a maturity level the docs don't state. Crucially, "the Apex compiler enforces existing Apex comment syntax ... it doesn't enforce the ApexDoc syntax or check comment accuracy in relation to corresponding Apex code" (apexdev 264 L13825-13826). Correctness here is a team/review responsibility, not a compiler guarantee.

---

## Before Starting

Gather this context before working on anything in this domain:

- **Decide the scope: code-level or org-level.** Code-level work is ApexDoc comments plus Apex naming conventions on specific classes. Org-level work is a written *design standards* document — naming conventions for every customization plus how docs are created, maintained, and centrally stored. They reinforce each other but are different deliverables.
- **Know that nothing here is compiler-enforced.** ApexDoc is a convention. The compiler will happily accept a `@param` that names a parameter that no longer exists, a `@return` on a `void` method, or a class with no doc block at all. Accuracy is caught in code review and by a checker, not at compile time.
- **Use the right delimiter.** An ApexDoc block starts with `/**` and ends with `*/`. A block that opens with `/*` (one asterisk) is an ordinary comment and is **not** treated as ApexDoc: "ApexDoc comments begin with /** and end with */" while other multiline comments use `/*` (apexdev 264 L13830-13832). That doc generators then skip it is an inference, not a corpus statement.
- **Anchor naming rules to the official conventions.** Salesforce prescribes: "classes start with a capital letter, methods start with a lowercase verb, and variable names should be meaningful", following Java standards (apexdev 264 L6699-6700). These are the conventions your documentation should describe, not house preferences invented from scratch.

---

## Questions to Ask Before Configuring

| Ask | Why it matters | What a good answer adds |
|---|---|---|
| Is the ask code-level ApexDoc or an org-level standard? | Before Starting: they are different deliverables | Scope: classes to document, or a standards document to write |
| Does anyone assume the compiler checks ApexDoc? | Gotcha 1: it enforces comment syntax only (apexdev 264 L13825-13826) | A review gate and CI checker plan |
| Do existing blocks open with `/**`? | Gotcha 2: `/*` is an ordinary comment (apexdev 264 L13830-13832) | A list of blocks the checker will flag |
| Where do annotations sit relative to the block? | Gotcha 3: the guide places them between the block and the declaration | A consistent layout the checker accepts |
| Which methods are void, and which have constructors? | Gotcha 4: no `@return` on those (apexdev 264 L13889-13890) | Corrected tags per signature |
| Which naming conventions does the team follow today? | Gotcha 5: the official ones are in apexdev 264 L6699-6700 | A standard that adopts them verbatim |
| Is anyone asserting a maturity label for ApexDoc? | Gotcha 6: the docs state none | Output with no GA, Beta or Pilot claim |

A proper configuration adds a gated, checker-backed standard that adopts the official conventions, instead of one-off comment clean-ups that decay.

---

## Core Concepts

### ApexDoc: what it is and who reads it

ApexDoc is a standardized comment format, based on the JavaDoc standard and tailored to Apex and Salesforce. Salesforce positions it for three audiences at once: **human developers, documentation generators, and AI agents** (apexdev 264 L13799-13800). Its stated purpose is to *facilitate code collaboration and increase long-term code maintainability* — not merely to make code readable in the editor. That framing matters for AI-assisted work: an accurate ApexDoc block is the primary signal an agent uses to understand a method's contract without re-reading the whole implementation.

An ApexDoc comment is a main description followed by tags. It **immediately precedes** the class, interface, enum, method, constructor, or property it documents: "No other code or comments are between the ApexDoc comment block and the element that it describes" (apexdev 264 L13833-13834). The guide's own examples put an annotation (`@Deprecated`, `@IsTest`, `@AuraEnabled(cacheable=true)`) between the block and the declaration (apexdev 264 L14388-14389, L14475-14476, L14755-14756). UNVERIFIED (2026-10-20): that a blank line breaks the association is not stated in the corpus.

### The tag vocabulary

ApexDoc defines a fixed set of **block tags** (begin with `@`, on their own line, after the main description) and **inline tags** (`{@tag ...}` inside prose); the tag table is apexdev 264 L13872-13950 ("Table 3: ApexDoc Tags"):

| Block tag | Documents |
|---|---|
| `@param` | A method/constructor parameter; must match the parameter's name and order |
| `@return` | The return value; **omit for `void` methods and constructors** |
| `@throws` | An exception the method/constructor can raise |
| `@author` | Author(s) of a class/interface/enum (multiple allowed) |
| `@deprecated` | Marks an element deprecated; include the reason and the alternative |
| `@example` | A usage example (often wrapped in `{@code ...}`) |
| `@group` | Groups related elements in generated docs |
| `@see` | A cross-reference (`Class#member`, text, or URL) |
| `@since` | Version or date the element was introduced |
| `@version` | Version of the class/interface/enum |

Inline tags: `{@code text}` (inline code / examples), `{@link reference}` (inline cross-reference), `{@literal text}` (render text literally, no HTML), `{@hidden text}` (prevents an element from appearing in generated docs; the guide writes it with text, apexdev 264 L13929, L14036-14037). The applicable elements differ by tag: `@author` and `@version` apply to class, interface and enum only; `@param` and `@throws` to methods and constructors; `@return` to methods; `@group` to class, interface, enum, method, property and variable; `@deprecated`, `@example`, `@see` and `@since` to all (apexdev 264 L13874-13930).

The rule that bites in review: `@param` order and names must track the signature ("It must match the parameter order and name", apexdev 264 L13886-13887), `@return` is not used for void methods or constructors (apexdev 264 L13889-13890) and is expected where a value is returned ("For methods that return values, use the @return block tag", apexdev 264 L14126), and `@throws` should list "all significant checked and unchecked exceptions that the method can explicitly throw" (apexdev 264 L14129-14130).

### Naming conventions as documentation

Naming is documentation's cheapest form. Salesforce's Apex conventions (apexdev 264 L6699-6700) — capitalized class names, lowercase verb-first method names (`createAccount`, not `AccountCreation`), meaningful variable names — mean the signature already tells most of the story before a single tag is written. A documentation standard should *encode these rules*, not restate arbitrary style. Consistent, convention-following names also make the ApexDoc read correctly: a verb-first method name plus a `@return` reads as a sentence.

### Org-level design standards

Beyond Apex, Salesforce Architects' Design Standards Template frames documentation as an org-wide discipline (UNVERIFIED (2026-10-20): the Architects resource is not in the corpus; everything in this section is Help/Architects-level): conventions for how *every* customization is named (objects, fields, automations, integrations, permission sets), plus a rule that development and configuration documents are created, maintained, and kept in **one central location**. The value is having a single agreed standard rather than per-developer habits; scattered or absent standards are what this addresses. (The architect.salesforce.com resource pages can be access-restricted to direct fetch — verify the template loads in a browser before citing it as your team's authority.)

---

## Common Patterns

### Fully-documented class + method

**When to use:** any new or refactored public/global Apex surface that other code, packages, or agents will consume.

**How it works:** put an ApexDoc block immediately above the class (`@group`, optionally `@author`/`@since`/`@version`, a `{@code}` `@example`) and above each method (one-line summary, then `@param` per argument in order, `@return` if non-`void`, `@throws` per exception). See `references/examples.md` Example 1 and the fill-in-the-blank block in `templates/development-documentation-standards-template.md`.

**Why not the alternative:** a bare `// creates account` line above the method carries none of the parameter/return/exception contract, is invisible to doc generators, and gives an AI agent nothing structured to reason over.

### Documenting a deprecation without breaking callers

**When to use:** you're retiring a method/class but callers still exist.

**How it works:** keep the element, add `@deprecated` with the reason and the replacement (e.g. `@deprecated Use {@link AccountService#createAccount} instead — this overload ignores record types`). The `{@link}` inline tag points readers straight at the successor.

**Why not the alternative:** deleting the method breaks callers; removing only the doc leaves future maintainers guessing why a still-present method shouldn't be used.

### Standardizing a team (org-level)

**When to use:** multiple developers, inconsistent comments, no agreed naming rules.

**How it works:** write one design-standards document that (1) adopts the official Apex naming conventions verbatim, (2) mandates ApexDoc on every public/global class and method with the required tags, (3) names a single central location for the doc, and (4) makes documentation coverage a code-review gate (see `devops/code-review-checklist-salesforce`). Run the skill's checker in CI to keep it honest.

**Why not the alternative:** relying on individual discipline produces drift; because the compiler never checks ApexDoc, an un-gated standard decays silently.

---

## Decision Guidance

| Situation | Recommended Approach | Reason |
|---|---|---|
| New public/global Apex class or method | Full ApexDoc block (`@param`/`@return`/`@throws` as applicable) | It's the contract humans, doc tools, and agents rely on |
| `void` method or constructor | Description + `@param` only, **no** `@return` | `@return` is invalid on void/constructors |
| Private helper with an obvious signature | Short description; tags optional | ApexDoc's value is on the surfaces others consume |
| Retiring a still-referenced method | `@deprecated` with reason + `{@link}` to the replacement | Preserves callers while steering new usage |
| Inconsistent naming across a team | Adopt the official Apex conventions in a written standard | Salesforce prescribes them; don't invent house rules |
| Standards exist but nobody follows them | Make coverage a review gate + run the checker in CI | The compiler never enforces ApexDoc; something else must |
| Org-wide (objects, flows, integrations) drift | A central design-standards document | One agreed source beats per-developer habits |

---

## Recommended Workflow

Step-by-step instructions for an AI agent or practitioner working on this task:

1. **Scope the request** — decide whether the ask is code-level (document/audit specific Apex) or org-level (define a written standard), and identify the classes or the areas in play.
2. **Establish the naming baseline** — confirm the code follows the official Apex conventions (capitalized classes, lowercase verb-first methods, meaningful variables); flag deviations, because good names carry half the documentation.
3. **Write or repair ApexDoc** — for each public/global class and method, add a `/** */` block immediately above the declaration with a summary and the applicable tags (`@param` matching the signature order, `@return` only when non-`void`, `@throws` per exception). Reference `templates/development-documentation-standards-template.md`.
4. **Cross-check tags against signatures** — verify no `@param` names a removed argument, no `@return` sits on a `void` method, every declared exception has a `@throws`, and blocks start with `/**` not `/*`.
5. **Run the checker** — `python3 scripts/check_development_documentation_standards.py --manifest-dir <path>` to surface undocumented surfaces and tag/signature mismatches the compiler will never catch.
6. **Codify and gate (org-level)** — capture the naming + documentation rules in one central design-standards document and wire documentation coverage into the code-review checklist / CI so the standard doesn't decay.

---

## Review Checklist

Run through these before marking work in this area complete:

- [ ] Every public/global class, method, and constructor has an ApexDoc block that **immediately precedes** it (no other code or comments between, apexdev 264 L13833-13834)
- [ ] Every block opens with `/**` (two asterisks), not `/*`
- [ ] `@param` tags match the parameter names and order; no stale params
- [ ] `@return` is present on non-`void` methods and **absent** on `void` methods and constructors
- [ ] Each exception the method can raise has a `@throws`
- [ ] Naming follows the official conventions (capitalized class, lowercase verb-first method, meaningful variables)
- [ ] Deprecated elements carry `@deprecated` with a reason and a `{@link}` to the replacement
- [ ] The team's naming + documentation rules live in one central, agreed location (org-level scope)
- [ ] No GA/Beta/Pilot maturity is asserted for ApexDoc anywhere in the output

---

## Salesforce-Specific Gotchas

Non-obvious platform behaviors that cause real production problems:

1. **The compiler never validates ApexDoc** — a `@param oldName` for a parameter you renamed, a `@return` on a `void` method, or a class with zero docs all compile and deploy cleanly. The lie ships. Only review and the checker catch it, which is why an un-gated standard rots.
2. **`/*` vs `/**` silently changes meaning** — a block opened with one asterisk is an ordinary comment, not ApexDoc (apexdev 264 L13830-13832); that doc generators then skip it is an inference, not a corpus statement. The code looks documented in the editor yet produces empty generated docs.
3. **Detached blocks document nothing** — an ApexDoc block must sit *immediately* above the declaration: "No other code or comments are between the ApexDoc comment block and the element that it describes" (apexdev 264 L13833-13834). An intervening statement or comment breaks the association. UNVERIFIED (2026-10-20): that a blank line or an annotation placed above the comment does so is not in the corpus; the guide's examples show annotations between the block and the declaration (apexdev 264 L14388-14389, L14755-14756), which is the form the checker accepts.
4. **Architect resource pages can 403 on direct fetch** (UNVERIFIED (2026-10-20): an environment observation, not a corpus fact) — the Design Standards Template on architect.salesforce.com may block scripted access; confirm it loads in a browser before treating it as your cited authority.

---

## Output Artifacts

| Artifact | Description |
|---|---|
| ApexDoc comment blocks | `/** */` blocks on classes/methods/constructors/properties with the applicable block and inline tags |
| Design-standards document | A written, centrally-stored standard covering naming conventions and documentation rules (org-level) |
| Documentation-coverage audit | Output of `scripts/check_development_documentation_standards.py` listing undocumented surfaces and tag/signature mismatches |
| Work template | `templates/development-documentation-standards-template.md` — a fill-in ApexDoc block plus a standards checklist |

---

## Related Skills

- `devops/code-review-checklist-salesforce` — make documentation coverage a review gate so the standard is enforced where the compiler won't.
- `apex/test-class-standards` — the parallel convention for test classes; document test intent the same disciplined way.
- `architect/solution-design-patterns` — the broader design-standards framing that org-wide documentation conventions plug into.
