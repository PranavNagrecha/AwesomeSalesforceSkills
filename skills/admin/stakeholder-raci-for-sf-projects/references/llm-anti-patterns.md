# LLM Anti-Patterns — Stakeholder RACI for Salesforce Projects

Common mistakes AI assistants make when generating or advising on a RACI matrix for a Salesforce project. Each entry describes the wrong output, the underlying cause, the correct pattern, and a detection hint.

## Anti-Pattern 1: Hallucinating roles not present in the project

**What the LLM generates:** A matrix that includes "Solution Architect," "Lead Developer," "QA Lead," "Scrum Master," and other roles that exist in generic SDLC literature but were not named in the project's actual stakeholder roster. The LLM fills cells for roles the customer never staffed.

**Why it happens:** The training set is heavy on generic project-management RACI templates from non-Salesforce contexts. The model defaults to PMI / Scrum / SAFe role names rather than the canonical Salesforce stakeholder roster.

**Correct pattern:**

```
Use only the canonical Salesforce roster from SKILL.md:
Business sponsor, Process owner, Data steward, Security architect,
Integration architect, CRM admin lead, Release manager,
AppExchange owner, Compliance officer, End-user representative.

If the project staffs additional roles, add them as new columns AFTER
confirming with the user that a named individual fills each.
Do not invent roles to fill empty cells.
```

**Detection hint:** Search the matrix columns for roles not in the canonical roster. Flag any role the user did not explicitly name.

---

## Anti-Pattern 2: Mass-assigning A to the sponsor

**What the LLM generates:** A matrix with "A" in the sponsor column on every row — data model, automation, security, integration, deployment, license. The LLM treats "the sponsor is accountable for the project" as "the sponsor is A on every decision."

**Why it happens:** Generic project-management training data conflates project-level accountability (which is the sponsor's) with decision-level accountability (which flows to the role with proximate domain expertise). The LLM also wants to look safe by deferring to the most senior name.

**Correct pattern:**

```
Sponsor's A is bounded:
- Scope (what is in/out of the project)
- Budget (what gets funded)
- License + edition tier (what gets bought)
- Go/no-go gate (does the project ship)

Operational A flows to the proximate-expertise role:
- Data model -> Process owner (or Data steward on regulated data)
- Automation tier -> CRM admin lead (with escalation to Integration architect when the decision tree picks Apex/Platform Events)
- Security model -> Security architect (or Compliance officer on regulated data)
- Integration boundary -> Integration architect
- Deployment -> Release manager
```

**Detection hint:** Count the number of rows where the sponsor holds A. If >2, the matrix is broken.

---

## Anti-Pattern 3: Omitting the data steward on data-model rows

**What the LLM generates:** A data-model row with the process owner as A and no entry (or "I") for the data steward. The data steward column may be missing entirely.

**Why it happens:** Data steward is a Salesforce-native role that doesn't appear prominently in generic RACI literature. The LLM defaults to a process owner / sponsor / admin pattern and forgets the steward.

**Correct pattern:**

```
Every data-model row must have the data steward as at least C
(consulted) — and on regulated data the data steward may hold A
on data classification while the compliance officer holds A on
the access controls.
```

**Detection hint:** Check every data-model row. If the data steward column is blank or "I", flag it.

---

## Anti-Pattern 4: Treating "Architecture" as a single role

**What the LLM generates:** A single "Architect" or "Solution Architect" column that holds A on security, integration, automation, AND data model. The LLM collapses security and integration architecture into one accountability.

**Why it happens:** "Architecture" is a single profession in many tech-org structures. The LLM defaults to "the architect decides architecture things." Salesforce projects in practice need security architecture and integration architecture as distinct accountabilities — they require different expertise and the decisions intersect different stakeholders.

**Correct pattern:**

```
Two columns: Security architect (SA) and Integration architect (IA).
- SA is A on the security-model row.
- IA is A on the integration-boundary row.
- Both are C on data-model rows that affect their domain.
- If one person fills both roles in practice, document that as a
  staffing risk, not as a column collapse.
```

**Detection hint:** Search for "Architect" or "Architecture" as a column header without a qualifier. Flag and split.

---

## Anti-Pattern 5: Failing to map RACI rows to refusal codes

**What the LLM generates:** A RACI matrix with rows and cells, but no refusal-code-to-stakeholder map at the bottom. When asked who handles `REFUSAL_NEEDS_HUMAN_REVIEW`, the LLM says "the project manager" or "the sponsor" instead of looking up the refusal map.

**Why it happens:** The refusal-code routing is repo-specific (`agents/_shared/REFUSAL_CODES.md`) and not in the LLM's prior training. Without explicit instruction it skips the routing table entirely.

**Correct pattern:**

```
Every RACI for this repo MUST end with a refusal-code map of the form:

| Refusal code | Decision category | Named A |
|---|---|---|
| REFUSAL_NEEDS_HUMAN_REVIEW (data model) | Data model | <named PO or DS> |
| REFUSAL_SECURITY_GUARD | Security model | <named SA> |
| REFUSAL_DATA_QUALITY_UNSAFE | Data model (data quality) | <named DS> |
| REFUSAL_MANAGED_PACKAGE | License + edition (package scope) | <named AX> |
... (cover every code that involves human review)
```

**Detection hint:** Search the output for "REFUSAL_". If absent, the matrix is incomplete for this repo.

---

## Anti-Pattern 6: Over-RACI — every cell filled

**What the LLM generates:** A matrix where every cell has a value (R, A, C, or I) — no blanks, no dashes. Every stakeholder is involved in every decision.

**Why it happens:** The LLM treats blank cells as "incomplete work" and tries to fill them. In practice, leaving cells blank ("not involved") is the correct answer for many stakeholder/decision pairs.

**Correct pattern:**

```
Cells may legitimately be blank or "—" when the stakeholder has
no role on that decision. A matrix where every cell is filled
either has too few rows (decisions are too coarse) or signals
that nobody is being deliberately excluded — which itself is a
governance smell.

Rule of thumb: each stakeholder column should have R/A/C/I on
roughly 30-70% of rows. Below 30%, the role probably shouldn't
be on the matrix; above 70%, the role is over-involved.
```

**Detection hint:** Count filled cells per column. If any column is >70% filled, audit for over-involvement.

---

## Anti-Pattern 7: Escalation rule with no time-box

**What the LLM generates:** Escalation rules of the form "Escalates to sponsor if blocked." Trigger and target named, time-box absent.

**Why it happens:** Time-boxes are a project-governance discipline that doesn't appear in generic RACI training data. The LLM treats the escalation rule as a routing label, not a clock.

**Correct pattern:**

```
Every escalation rule has three parts:
- Trigger: the condition that fires escalation.
- Target: the role/person the decision goes to next.
- Time-box: how long the A has to decide before escalation auto-fires.

Default time-boxes:
- Deployment: 1 business day
- Security, Automation tier: 3 business days
- Data model, Integration boundary: 5 business days
- License + edition: 10 business days
```

**Detection hint:** Search escalation rules for a number of days. If absent, the rule is incomplete.
