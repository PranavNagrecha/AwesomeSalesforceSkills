# LLM Anti-Patterns — Sales Process Mapping

Common mistakes AI coding assistants make when generating or advising on Sales Process Mapping.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Generating Stage Names Without Entry or Exit Criteria

**What the LLM generates:** A numbered or bulleted list of stage names (e.g., "1. Prospecting, 2. Qualification, 3. Proposal, 4. Negotiation, 5. Closed Won") presented as a complete stage map, with no criteria per stage.

**Why it happens:** Training data contains many "sample Salesforce stage list" articles and Trailhead content that show stage names as the primary artefact. LLMs pattern-match on this and produce a stage list rather than a stage mapping document. The names look plausible and the output appears complete.

**Correct pattern:**

```
Every stage in the output must include:
- Plain-language definition (what state is the deal in?)
- Entry criteria (what must be true before the deal enters this stage?)
- Exit criteria (what must be true before the deal can leave?)
- ForecastCategoryName (one of: Pipeline, Best Case, Commit, Closed, Omitted)
- Default probability (%)
- Primary owner role
```

**Detection hint:** If the output contains only stage names and no "entry criteria" or "exit criteria" fields, the mapping is incomplete. Reject and ask the LLM to add criteria for each stage.

---

## Anti-Pattern 2: Inventing Non-Existent ForecastCategoryName Values

**What the LLM generates:** A stage map that assigns stages to forecast categories with labels like "Upside", "Strong Upside", "Called", "At Risk", or "Best Commit". These values do not exist in the Salesforce platform.

**Why it happens:** Salesforce forecast category terminology varies across customer documentation, blog posts, and partner materials. LLMs surface diverse terminology and may generate plausible-sounding but non-existent category names, particularly when the user's prompt uses industry-specific forecasting language.

**Correct pattern:**

```
The only valid ForecastCategoryName values are (exactly, case-sensitive):
- Pipeline
- Best Case
- Commit
- Closed
- Omitted

Any stage map must assign each stage to one of these five values only.
```

**Detection hint:** Scan the stage map output for any ForecastCategoryName value that is not one of the five listed above. Flag any deviation as an error and correct it before handing off to the opportunity-management skill.

---

## Anti-Pattern 3: Conflating Stage Mapping with Salesforce Configuration Instructions

**What the LLM generates:** A response that mixes stage design decisions (which stages exist, what criteria they have) with Salesforce Setup navigation instructions (e.g., "Go to Setup > Opportunity Stages, click New, fill in the Stage Name field…"). The output teaches configuration when the user needed a design document.

**Why it happens:** "Sales process mapping" is a query that triggers both BA-style design content and admin-style how-to content in training data. LLMs conflate the two, producing a hybrid output that is a design document for half the answer and a setup tutorial for the other half.

**Correct pattern:**

```
Sales process mapping output = design artefact (stage map, transition rules, win/loss taxonomy)
Salesforce configuration instructions = separate task, handled by opportunity-management skill

When producing a sales process mapping output, do NOT include:
- Step-by-step Setup navigation instructions
- Metadata API field names (e.g., ForecastCategory, IsClosed, IsWon)
- References to record types, sales processes, or Path configuration

Those are implementation details. The mapping document must stand on its own as a business design document.
```

**Detection hint:** If the output contains phrases like "go to Setup", "click Save", "open the Object Manager", or refers to metadata fields, the LLM has crossed from mapping into configuration. Strip the configuration instructions and redirect to the opportunity-management skill for that phase.

---

## Anti-Pattern 4: Recommending a Single Stage List for Multiple Selling Motions

**What the LLM generates:** A single 8–12 stage sequence that tries to serve both a new-logo motion and a renewal motion (or direct and channel motions) within one list. Stages like "Renewal Outreach" are inserted into a list that also contains "Discovery" and "Technical Evaluation", producing a sequence that no single deal type follows cleanly.

**Why it happens:** LLMs default to producing a single comprehensive answer. When the prompt mentions multiple deal types, the LLM often tries to consolidate them into one output rather than recognising that multiple motions require separate stage sequences. This mirrors the most common real-world error in sales process design.

**Correct pattern:**

```
If the business describes more than one selling motion (new logo, renewal, upsell, channel, professional services):
- Produce a separate stage sequence for each distinct motion
- Label each sequence clearly (e.g., "New Logo Stage Sequence", "Renewal Stage Sequence")
- Note that each sequence will become a separate Salesforce Sales Process and Record Type
- Do not merge the sequences unless explicitly confirmed that a single process is intended
```

**Detection hint:** If a single stage sequence contains stages from multiple deal types (e.g., both "Technical Evaluation" and "Renewal Negotiation"), the LLM has merged motions incorrectly. Ask the LLM to separate the sequences by deal type.

---

## Anti-Pattern 5: Producing Win/Loss Taxonomy With Too Many Values or a Free-Text Fallback

**What the LLM generates:** A win/loss reason taxonomy with 15–25 values per outcome, often including a catch-all "Other" or a note that "a free-text field can be added for additional reasons not listed." The taxonomy is too granular to be completed consistently by sales reps.

**Why it happens:** LLMs optimise for completeness and comprehensiveness. A long list of reasons appears thorough. The LLM also commonly adds an "Other" escape hatch, which in practice becomes the most-used category and defeats the purpose of a constrained taxonomy.

**Correct pattern:**

```
Win/loss taxonomy constraints:
- 5–8 win reasons maximum
- 5–8 loss reasons maximum
- No "Other" category (if a reason doesn't fit, the taxonomy needs refining, not an escape hatch)
- No free-text field as a substitute for a constrained picklist
- Always include "No Decision / Status Quo" as a loss reason
- Each reason should describe a deal-specific cause, not a macro trend

Example of well-scoped loss reasons (6 values):
1. Lost to Competitor — Price
2. Lost to Competitor — Product Fit
3. No Decision / Status Quo
4. Budget Eliminated or Not Approved
5. Wrong Stakeholder — No Champion
6. Evaluation Criteria Changed Late
```

**Detection hint:** Count the win reason values and loss reason values in the output. If either exceeds 10, flag the taxonomy as too granular and ask the LLM to consolidate. If "Other" or "free-text" appears, flag it as an anti-pattern and remove it.

---

## Anti-Pattern 6: Treating Path Configuration as Stage Enforcement

**What the LLM generates:** A statement like "configure Path to enforce that reps complete key fields before advancing" or "Path will prevent reps from skipping stages". Path is recommended as the enforcement mechanism for stage transition rules.

**Why it happens:** Salesforce marketing and Trailhead content emphasises Path as a tool for "guiding reps through the sales process," which LLMs interpret as enforcement. The distinction between visual guidance (Path) and save-blocking enforcement (validation rules) is subtle and frequently blurred in secondary sources.

**Correct pattern:**

```
Path provides visual guidance and key field prompts. It does not:
- Block a rep from saving a record at any stage
- Prevent backward stage movement
- Require fields to be filled before stage advancement

Stage progression enforcement requires validation rules with ISPICKVAL() and PRIORVALUE() logic.
Example:
  ISPICKVAL(StageName, 'Proposal') && ISBLANK(CloseDate)
  -> Error: "Close Date is required before moving to Proposal stage."

For each transition rule in the mapping document, the output must specify:
- Path guidance (if advisory) OR
- Validation rule (if enforcement is required, with the condition stated explicitly)
```

**Detection hint:** If the output uses phrases like "Path enforces", "Path requires", "Path blocks", or "configure Path to prevent", the LLM has made this error. Replace Path references with validation rule requirements for any enforcement scenario.
