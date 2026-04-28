# LLM Anti-Patterns — MoSCoW Prioritization for Salesforce Backlog

Common mistakes AI assistants make when prioritizing a Salesforce backlog. Use these to self-check generated output.

---

## Anti-Pattern 1: Tagging MoSCoW Based on the User's Stated Importance Only

**What the LLM generates:** Every row the user described as "important" or "high priority" gets Must. The model treats stakeholder enthusiasm as the signal.

**Why it happens:** LLMs are trained to be agreeable. The user said "important", so the model picks the strongest tag. There is no internal pushback because the model has no concept of capacity, opportunity cost, or release-failure consequence.

**Correct pattern:**

```
For each row, ask: "If we ship the release WITHOUT this item, does the release fail its objective?"
- Yes (regulator fines us, contract breached, business cannot operate) → Must
- No, but stakeholders will be unhappy → Should
- No, and it's nice-to-have → Could
- No, and we are explicitly choosing not to ship it → Won't
```

**Detection hint:** Count Musts. If >60% of rows are Must, the model is rubber-stamping. Reject and re-tag.

---

## Anti-Pattern 2: Ignoring Effort When Recommending the Sprint Commit

**What the LLM generates:** A "top priorities for this sprint" list with five Must rows and zero effort tags. The list is cleanly ordered by value.

**Why it happens:** Value is the salient signal in training data ("most important" appears more often than "smallest"). The model anchors on value and skips the orthogonal effort axis.

**Correct pattern:**

```
Every recommended sprint commit row MUST carry an effort tier (S/M/L/XL).
Sum effort. Reject the commit if Sum(Must effort) > capacity.
Surface the gap to the user with the math: "Must total = 45 days; capacity = 30 days; 15 days over."
```

**Detection hint:** Search the output for any `"effort":` field that is null or missing on a Must row. That row is invalid.

---

## Anti-Pattern 3: Hallucinating Release Targets

**What the LLM generates:** `release_target: "2026-Spring-Patch-3"` or `"Q3-Release-7"` — confident-sounding identifiers the user never mentioned.

**Why it happens:** The model fills the field rather than admit ignorance. Salesforce release nomenclature is well-represented in training data, so a plausible-looking string is easy to generate.

**Correct pattern:**

```
release_target must be one of:
  - a release identifier the user supplied verbatim (e.g., "2026-Q3", "sprint-12")
  - "backlog" — for Won't-this-release rows that return to the backlog
  - "archived" — for Won't-ever rows
If the user has not supplied a release naming convention, ask before inventing one.
```

**Detection hint:** Diff the release_target values against the set of releases the user mentioned. Any value not in that set is suspect.

---

## Anti-Pattern 4: Prioritizing Only the Visible Items, Forgetting the Backlog Tail

**What the LLM generates:** A clean prioritization of the top 20 rows the user pasted. Rows 21–N (the long tail) are ignored or summarily dismissed.

**Why it happens:** Context windows favour the visible. The model anchors on what is in front of it and forgets that a real backlog has a tail of stale Won't candidates that need archive decisions.

**Correct pattern:**

```
When the user references "the backlog", ask whether stale items should be reviewed for Won't-ever archival.
The Won't-ever decision is itself prioritization output — it removes noise from future groomings.
A prioritization session that does not produce any archive decisions is suspect.
```

**Detection hint:** Count Won't-ever rows. Zero is suspicious for any backlog older than two quarters.

---

## Anti-Pattern 5: Conflating Priority with Sequencing

**What the LLM generates:** "Must items go in sprint 1, Should in sprint 2, Could in sprint 3." The model treats MoSCoW as a sprint sequence.

**Why it happens:** MoSCoW maps cleanly onto an ordered list, and ordered lists are how LLMs prefer to express decisions. The model collapses the (priority, sequence) two-axis decision into one.

**Correct pattern:**

```
MoSCoW = "what fails if we drop it from THIS release"
Sequencing = "what order do we build it in within the release"
Sequencing depends on dependencies and effort, not on MoSCoW.
A small Could item with no dependencies might ship in week 1; a large Must with three dependencies might land in week 6.
```

**Detection hint:** If the output uses MoSCoW tags as the sole sort key for sequencing, push back.

---

## Anti-Pattern 6: Treating Musts as Immutable

**What the LLM generates:** When asked "the regulator pushed the deadline back two quarters; how does the prioritization change?", the model leaves all Musts as Must.

**Why it happens:** "Must" reads as a hard constraint. The model resists demoting it because demoting feels like contradicting the user's earlier statement.

**Correct pattern:**

```
At every re-grooming, every Must row is re-evaluated against its rationale.
If the rationale's premise has changed (deadline pushed, scope cut, regulation withdrawn), re-tag.
Musts can move to Should or even Won't-this-release. The rubric is a tool, not a ratchet.
```

**Detection hint:** If the user supplies new context that invalidates a prior Must rationale and the output keeps the Must tag, the model is anchoring incorrectly.

---

## Anti-Pattern 7: Running WSJF Across the Entire Backlog

**What the LLM generates:** A 30-row backlog with WSJF scores computed for every row, ordered by WSJF descending.

**Why it happens:** WSJF is a clean numerical formula and LLMs love clean formulas. Applying it broadly looks rigorous.

**Correct pattern:**

```
WSJF is a TIE-BREAK, not a ranking method. Apply it ONLY to clusters of items at the capacity boundary
where MoSCoW + effort + value have produced ties (typically 5–15 rows).
Backlog-wide WSJF is cognitively expensive and the comparative scoring degrades quickly past ~15 items.
```

**Detection hint:** If `wsjf_score` is non-null on more than ~15 rows, the model is over-applying WSJF.
