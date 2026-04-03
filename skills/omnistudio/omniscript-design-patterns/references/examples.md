# Examples — OmniScript Design Patterns

## Example 1: Thin Enrollment Journey With Backend Delegation

**Context:** A benefits enrollment journey collects user choices, eligibility answers, and confirmation details.

**Problem:** The first draft tries to perform every transformation and integration step directly inside the OmniScript.

**Solution:**

```text
Step 1: Identify member and context
Step 2: Capture eligibility inputs
Step 3: Review recommended plans
Step 4: Confirm and submit
Backend work: eligibility calculation and submission orchestration moved to Integration Procedures
```

**Why it works:** The script stays focused on the guided experience while the backend handles transformation and orchestration logic.

---

## Example 2: Conditional Branching With A Stable Default Path

**Context:** A service-intake OmniScript changes later questions based on whether the user is an existing customer.

**Problem:** The design creates many divergent branches with different data structures for downstream processing.

**Solution:**

```text
Default path: standard customer intake
Branch only when user is new -> collect onboarding fields
All paths normalize into the same submission payload before final review
```

**Why it works:** The branch is meaningful to users but still converges into a predictable data shape for processing.

---

## Anti-Pattern: OmniScript As The Entire Platform Layer

**What practitioners do:** They keep adding transformations, validations, integrations, and custom widgets until the script becomes the entire solution.

**What goes wrong:** Performance, supportability, and change safety all degrade because the guided interaction layer is carrying too much responsibility.

**Correct approach:** Keep OmniScript focused on guidance and move heavy backend logic behind it.
