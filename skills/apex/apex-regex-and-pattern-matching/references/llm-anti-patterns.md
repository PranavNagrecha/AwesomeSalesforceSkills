# LLM Anti-Patterns — Apex Regex And Pattern Matching

Common mistakes AI coding assistants make when generating or advising on Apex regex.

## Anti-Pattern 1: Single-Backslash Regex In An Apex Literal

**What the LLM generates:**

```apex
Pattern p = Pattern.compile('\d{3}-\d{2}-\d{4}');
```

**Why it happens:** LLMs reproduce patterns verbatim from JavaScript and Python examples, where `\d` is a valid escape in the host string literal. Apex string literals share Java's escape rules, so `\d` is either a compile error or silently becomes `d`.

**Correct pattern:**

```apex
Pattern p = Pattern.compile('\\d{3}-\\d{2}-\\d{4}');
```

**Detection hint:** search for `Pattern.compile\(\s*'[^']*\\[dswbn]` — single backslash before any regex metachar inside an Apex string literal is always wrong.

---

## Anti-Pattern 2: Expecting `matches()` To Be Unanchored

**What the LLM generates:**

```apex
if (body.matches('ERROR')) { /* ... */ }
```

**Why it happens:** LLMs map `.matches()` to JavaScript `.test()` or Python `re.search()`. The Apex `matches()` method requires the whole string to match.

**Correct pattern:**

```apex
if (Pattern.compile('ERROR').matcher(body).find()) { /* ... */ }
```

**Detection hint:** `\.matches\(` called on a string that is obviously longer than the pattern (logs, email bodies, notes).

---

## Anti-Pattern 3: Unescaped `$` In Replacement

**What the LLM generates:**

```apex
String out = template.replaceAll('\\{price\\}', '$' + amount);
```

**Why it happens:** LLMs compose replacement strings from user values without realizing `$` is a backreference in Java regex replacement syntax.

**Correct pattern:**

```apex
String out = template.replaceAll('\\{price\\}', Matcher.quoteReplacement('$' + amount));
```

**Detection hint:** any `replaceAll` or `replaceFirst` call whose replacement argument concatenates a variable without `Matcher.quoteReplacement`.

---

## Anti-Pattern 4: Injecting User Input Into The Pattern

**What the LLM generates:**

```apex
Boolean hit = body.matches('.*' + userSearch + '.*');
```

**Why it happens:** LLMs treat the pattern argument like a SQL parameter and concatenate. User input containing `.`, `(`, or `*` becomes live regex.

**Correct pattern:**

```apex
Boolean hit = body.contains(userSearch);
// or if regex is truly required:
Boolean hit = body.matches('.*' + Pattern.quote(userSearch) + '.*');
```

**Detection hint:** a regex string built with `+` concatenation of a variable that originated from a user-facing parameter.

---

## Anti-Pattern 5: Compiling A Pattern Inside A Loop

**What the LLM generates:**

```apex
for (String s : inputs) {
    if (Pattern.compile('\\w+@\\w+').matcher(s).matches()) {
        valid.add(s);
    }
}
```

**Why it happens:** LLMs emit self-contained statements without hoisting invariants. Unit-test templates reinforce this shape.

**Correct pattern:**

```apex
private static final Pattern EMAIL = Pattern.compile('\\w+@\\w+');

for (String s : inputs) {
    if (EMAIL.matcher(s).matches()) valid.add(s);
}
```

**Detection hint:** `Pattern.compile(` inside a `for` or `while` block.

---

## Anti-Pattern 6: Using `.*` On Adversarial Input With A Suffix

**What the LLM generates:**

```apex
Pattern INJECTION = Pattern.compile('<script>.*</script>');
boolean malicious = INJECTION.matcher(userHtml).find();
```

**Why it happens:** LLMs copy "canonical" regexes from security blog posts without reasoning about backtracking complexity on adversarial input.

**Correct pattern:** Use explicit, bounded classes and reluctant quantifiers:

```apex
Pattern INJECTION = Pattern.compile('<script\\b[^>]{0,200}>.*?</script>',
                                    Pattern.CASE_INSENSITIVE | Pattern.DOTALL);
```

**Detection hint:** `.*` or `.+` followed by a specific literal in a pattern that runs on user-controlled HTML or text.

---

## Anti-Pattern 7: Splitting On A Metacharacter Without Escaping

**What the LLM generates:**

```apex
List<String> parts = version.split('.');
```

**Why it happens:** LLMs treat `split` as accepting a literal delimiter (like Python's `str.split('.')`). In Apex it is a regex and `.` matches everything.

**Correct pattern:**

```apex
List<String> parts = version.split('\\.');
```

**Detection hint:** `.split('` followed by one of `. | ( ) $ * + ? [ ] { } \\ ^` — any of those unescaped metacharacters is almost certainly wrong.

---

## Anti-Pattern 8: Assuming Named Groups Are Supported In All API Versions

**What the LLM generates:**

```apex
Pattern p = Pattern.compile('(?<year>\\d{4})-(?<month>\\d{2})');
String year = m.group('year');
```

**Why it happens:** Named groups work in modern Apex (API 47+), but older orgs still on lower API version classes throw compile errors. LLMs assume universal support.

**Correct pattern:** Use numbered groups for compatibility:

```apex
Pattern p = Pattern.compile('(\\d{4})-(\\d{2})');
String year = m.group(1);
```

**Detection hint:** `(?<name>` in a pattern — confirm the containing class API version is at least 47.
