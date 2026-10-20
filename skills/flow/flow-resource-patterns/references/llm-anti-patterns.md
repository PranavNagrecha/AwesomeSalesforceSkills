# LLM Anti-Patterns — Flow Resource Patterns

Common mistakes AI coding assistants make when choosing Flow resource types.

## Anti-Pattern 1: Assignment for derived values instead of Formula

**What the LLM generates:** Two Assignment elements — one to compute `Discounted = Amount - Amount * Rate`, one to later recompute when `Rate` changes.

**Why it happens:** Model thinks procedurally, doesn't know Formula resources stay in sync automatically.

**Correct pattern:**

```
Formula: f_Discounted = {!Amount} - {!Amount} * {!Discount_Rate}

Referencing {!f_Discounted} anywhere recomputes from current inputs.
No stale-value bug, no extra elements.

Prefer Assignment only when:
- the value must persist across a DML that refreshes inputs
- the formula is expensive and referenced many times in a loop
```

**Detection hint:** Multiple Assignment elements computing the same expression, or Assignments after a field-change element to "re-update" a derived value.

---

## Anti-Pattern 2: Hardcoded literals in element fields

**What the LLM generates:** Four Decision elements each comparing `{!Region}` to the literal `"NAMER"`.

**Why it happens:** Model writes the value inline where it's needed.

**Correct pattern:**

```
Promote to Constant:

Constant: c_DEFAULT_REGION = "NAMER"

Reference {!c_DEFAULT_REGION} in all four Decisions. Changing the
region updates one place, not four. Also enables the References
panel to find every use.
```

**Detection hint:** Same string/number literal appearing in 3+ places across a flow's decisions or assignments.

---

## Anti-Pattern 3: SObject dot-access without null guard

**What the LLM generates:**

```
Decision condition: {!getAccountResult.Industry} = "Technology"
```

where `getAccountResult` came from a Get Records that may return nothing.

**Why it happens:** Model doesn't account for no-match case.

**Correct pattern:**

```
A Get Records that finds no match leaves the SObject variable null.
Referencing a field on null throws at runtime. (UNVERIFIED (2026-10-20):
not in the corpus.)

Guard with:
- Decision first: ISBLANK({!getAccountResult.Id}) → null branch
- Or formula: IF(ISBLANK({!getAccountResult.Id}), '', {!getAccountResult.Industry})

Most common in scheduled paths where related records may have been
deleted between trigger and path execution. (UNVERIFIED (2026-10-20):
experience, not a corpus claim.)
```

**Detection hint:** Dot-access on an SObject variable populated by Get Records without a prior ISBLANK/ISNULL check.

---

## Anti-Pattern 4: Building email body via concatenated Assignments

**What the LLM generates:** Five Assignments appending strings: `body = body + firstName + " ..."`.

**Why it happens:** Model applies imperative string-building.

**Correct pattern:**

```
Use a Text Template resource:

Text Template tt_WelcomeBody (Rich-text):
  Hi {!$Record.FirstName},
  Welcome to {!$Label.CompanyName}. Your account id is {!$Record.Id}.

Reference {!tt_WelcomeBody} as the Email Body. One resource (`text`
supports merge fields, api_meta 264 L75572), previewable in the
builder. UNVERIFIED (2026-10-20): "merge fields validated at save" is
not in the corpus.
```

**Detection hint:** Assignment chain concatenating text, producing an email/screen body.

---

## Anti-Pattern 5: Record Choice Set with no filter or limit

**What the LLM generates:** Record Choice Set on Account with no filter — returns the first accounts up to the limit (200 by default), not all accounts.

**Why it happens:** Model defaults to "get everything."

**Correct pattern:**

```
A Record Choice Set returns at most 200 choices ("Maximum and
default: 200", api_meta 264 L73017-73018), so it cannot load 5000
accounts, but 200 unfiltered rows in a picklist is still a poor UX. The
earlier text assumed 5000 rows.

Always:
- filter to a relevant subset (active, owned by current user, recent)
- sort by the label field
- set a reasonable Maximum (10–50 for UX, 200 absolute ceiling, api_meta 264 L73017-73018)

For >200 active records, switch to a lookup field or a typeahead
screen component.
```

**Detection hint:** dynamicChoiceSet element with no filter or limit child.
