# LLM Anti-Patterns — Custom Label Management

Common mistakes AI coding assistants make when handling user-facing strings.

## Anti-Pattern 1: Hard-coding English strings in LWC templates

**What the LLM generates:** `<h1>Welcome, please log in</h1>` directly in the template.

**Why it happens:** The model treats LWC like a static web page without considering i18n.

**Correct pattern:**

```
Create a Custom Label `Welcome_LoginPrompt`, import in JS via
@salesforce/label/c.Welcome_LoginPrompt, and reference in template
as {labels.welcome}. Now translatable and reviewable without code.
```

**Detection hint:** LWC `.html` with prose English text not bound to a `labels` import or variable.

---

## Anti-Pattern 2: Hard-coding error messages in Apex addError

**What the LLM generates:** `acc.addError('Amount cannot be negative');`

**Why it happens:** Model generates validation logic without externalizing messages.

**Correct pattern:**

```
acc.addError(System.Label.Error_AmountNegative);

Create the label with a short-description explaining the scenario so
translators have context.
```

**Detection hint:** Apex `addError('...')` with a hard-coded English message.

---

## Anti-Pattern 3: Renaming a label Name to reflect a value change

**What the LLM generates:** Renames label `Error_Msg` → `Error_Negative_Amount`.

**Why it happens:** Model treats Name as a display string rather than an API handle.

**Correct pattern:**

```
Label Names are API references — renaming breaks Apex and LWC
references. Keep Name stable; change the Value instead. If semantics
change enough to want a new Name, add a new label and deprecate the
old one after references migrate.
```

**Detection hint:** Diff shows label Name change with matching Apex edits.

---

## Anti-Pattern 4: Splitting a label over 1,000 chars ad hoc

**What the LLM generates:** Three labels concatenated in Apex with no naming pattern.

**Why it happens:** Model brute-forces the limit without considering translator experience.

**Correct pattern:**

```
Use consistent suffix convention: My_Long_Text_Part1, My_Long_Text_Part2.
Concatenate in a helper (MessageBuilder.forEmail('My_Long_Text')) that
joins parts by base name. Translators see grouped parts, not
mysteriously-numbered labels.
```

**Detection hint:** Labels named with arbitrary suffixes concatenated in Apex string assembly.

---

## Anti-Pattern 5: Building a parallel Map<String,String> instead of using System.Label

**What the LLM generates:** `Map<String,String> labels = new Map<String,String>{ 'welcome' => 'Welcome!' };`

**Why it happens:** Model invents a parallel i18n mechanism without knowing about `System.Label`.

**Correct pattern:**

```
Use System.Label.My_Label directly. It's compiled, package-aware,
translated via Translation Workbench, and tracked by metadata
dependency tooling. A parallel Map<String,String> is unversioned,
untranslatable, and invisible to the Setup UI.
```

**Detection hint:** Apex class defining a static Map of string->string for "labels".
