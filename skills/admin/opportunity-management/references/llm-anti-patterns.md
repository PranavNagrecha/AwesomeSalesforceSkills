# LLM Anti-Patterns — Opportunity Management

Common mistakes AI coding assistants make when generating or advising on Opportunity Management.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Renaming ForecastCategoryName Values

**What the LLM generates:** Instructions to rename forecast category labels such as changing "Best Case" to "Upside" or "Commit" to "Forecast" via picklist metadata or Setup > Opportunity Stages.

**Why it happens:** LLMs pattern-match on "rename picklist value" and assume all picklist fields behave the same. They do not distinguish between customer-configurable picklist fields and platform-reserved internal values. Training data likely contains admin blog posts that discuss customizing forecasting without clarifying this constraint.

**Correct pattern:**

```
ForecastCategoryName has exactly five fixed platform values:
  Pipeline | Best Case | Commit | Closed | Omitted

These cannot be renamed. They are platform-internal values, not standard picklist values.
To communicate custom terminology, use:
  - Stage picklist labels (e.g., name a stage "Upside — Proposal Sent" and map it to Best Case)
  - Path guidance text per stage
  - Training documentation
```

**Detection hint:** Look for instructions saying "rename forecast category" or metadata showing a ForecastCategoryName value not in {Pipeline, Best Case, Commit, Closed, Omitted}.

---

## Anti-Pattern 2: Configuring Path Before the Sales Process Is Assigned to the Record Type

**What the LLM generates:** Step-by-step Path configuration instructions that omit or reorder the prerequisite of assigning a Sales Process to the record type first.

**Why it happens:** LLMs treat Path as an independent configuration step. They often generate instructions based on the Path Settings UI without modeling the dependency chain (Stage picklist → Sales Process → Record Type → Path).

**Correct pattern:**

```
Correct configuration order (dependencies flow downward):
  1. Define Stage values globally in Setup > Opportunity Stages
  2. Create Sales Process, assign relevant stages
  3. Assign Sales Process to Record Type
  4. THEN configure Path Settings for that Record Type

Attempting to configure Path before Step 3 will result in no stages being available
in Path Settings, or Path referencing stages not in the active sales process.
```

**Detection hint:** Look for Path configuration steps appearing before "Assign Sales Process to Record Type" in any setup guide.

---

## Anti-Pattern 3: Treating Path Configuration as Stage Progression Enforcement

**What the LLM generates:** Advice like "configure Path to require reps to complete key fields before moving to the next stage" or "use Path Settings to enforce that Close Date is filled before Proposal Sent."

**Why it happens:** Path's visual stage-by-stage layout resembles a wizard. LLMs infer that it has wizard-like enforcement. The training corpus likely contains marketing descriptions of Path as a "guided selling" tool without clarifying that it has zero save-blocking capability.

**Correct pattern:**

```
Path = visual guidance only. It does not block saves.

To ENFORCE stage progression or required fields per stage, use Validation Rules:
  Example — require CloseDate before Proposal Sent:
    Error condition: AND(ISPICKVAL(StageName, "Proposal Sent"), ISBLANK(CloseDate))
    Error message:  "Close Date is required before moving to Proposal Sent."

  Example — block stage skipping:
    Error condition: AND(
      ISPICKVAL(StageName, "Closed Won"),
      NOT(ISPICKVAL(PRIORVALUE(StageName), "Negotiation")),
      NOT(ISPICKVAL(PRIORVALUE(StageName), "Closed Won"))
    )
```

**Detection hint:** Any instruction that says "configure Path to require" or "Path enforces" is incorrect. Path guidance text is informational only.

---

## Anti-Pattern 4: Enabling Opportunity Splits Before Team Selling

**What the LLM generates:** Splits setup instructions that jump directly to Setup > Opportunity Settings > Enable Opportunity Splits without first enabling Opportunity Teams.

**Why it happens:** LLMs retrieve the Splits setup steps from documentation but miss the prerequisite dependency. The enablement order is not always stated prominently in the top-level help article, and LLMs often omit prerequisite steps that appear in a separate article.

**Correct pattern:**

```
Mandatory enablement order:
  Step 1: Setup > Opportunity Team Settings > Enable Opportunity Teams   ← FIRST
  Step 2: Setup > Opportunity Settings > Enable Opportunity Splits        ← SECOND

Reversing this order produces a platform error. Team Selling must be active
before the Splits enablement option becomes functional.
```

**Detection hint:** Any splits setup guide that does not mention Team Selling as a prerequisite step is incomplete. Look for missing "Enable Opportunity Teams" before "Enable Opportunity Splits."

---

## Anti-Pattern 5: Assuming Revenue Splits and Overlay Splits Have the Same 100% Validation

**What the LLM generates:** Statements like "both revenue and overlay splits must total exactly 100%" or validation rule suggestions that enforce 100% totals on overlay splits.

**Why it happens:** Revenue splits have an enforced 100% total rule that is well-documented. LLMs generalize this rule to all split types without distinguishing the two. Overlay splits intentionally allow totals other than 100% (e.g., multiple SEs each getting 100% overlay credit on the same deal).

**Correct pattern:**

```
Revenue splits:  MUST total exactly 100% per opportunity (platform-enforced, save-blocking)
Overlay splits:  NO total constraint — can be any value, including >100%

Overlay splits are designed to let multiple team members each claim full credit
for their contribution without reducing each other's allocation.

If the business wants to cap overlay credit, implement a custom validation rule
or Flow — the platform does not enforce any limit on overlay split totals.
```

**Detection hint:** Look for statements that apply "must total 100%" to overlay splits, or validation rule suggestions that check overlay split totals against 100%.

---

## Anti-Pattern 6: Advising Stage Value Deletion Instead of Deactivation

**What the LLM generates:** Instructions that say "go to Setup > Opportunity Stages, find the deprecated stage, and click Delete" without first checking record counts or offering deactivation as an alternative.

**Why it happens:** "Delete the value" is the most literal interpretation of "remove this stage from the picklist." LLMs are not trained to model the downstream consequence (silent field blanking on active records) of picklist value deletion in Salesforce.

**Correct pattern:**

```
Before deleting any Stage picklist value:
  1. Query affected records:
     SELECT COUNT() FROM Opportunity WHERE StageName = 'Deprecated Stage'
  2. If count > 0: bulk-reassign records to a valid stage via Data Loader or Flow
  3. Prefer DEACTIVATION over deletion:
     Setup > Opportunity Stages > Edit > uncheck Active
     Deactivation hides the value from new record dropdowns while preserving it
     on closed historical records.
  4. Only hard-delete if COUNT() returns 0.
```

**Detection hint:** Any instruction to "delete" a Stage value without a preceding record-count check is a risk. The word "deactivate" should appear before "delete" in any stage retirement guide.
