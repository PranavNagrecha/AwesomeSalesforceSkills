# LLM Anti-Patterns — Einstein Next Best Action

Common mistakes AI coding assistants make when generating or advising on Einstein Next Best Action.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Strategy Builder Instead of Flow Builder

**What the LLM generates:** Instructions to create an NBA strategy using Strategy Builder, including references to "Strategy Builder canvas," "Load element," "Filter element," or "Sort element."

**Why it happens:** LLM training data includes pre-Spring '24 documentation and Trailhead content where Strategy Builder was the primary tool. The model defaults to the most frequently represented approach in its training corpus.

**Correct pattern:**

```text
All NBA strategies must be built as Autolaunched Flows in Flow Builder.
Strategy Builder was deprecated in Spring '24.
Use Get Records, Decision, Assignment, and Loop elements in Flow
to replicate any logic previously built in Strategy Builder.
```

**Detection hint:** Look for mentions of "Strategy Builder", "strategy canvas", "Load element", "Filter element", or "Sort element" in NBA context. Any of these terms indicate outdated guidance.

---

## Anti-Pattern 2: Defining the Flow Output Variable as a Generic SObject Collection

**What the LLM generates:** Flow instructions that create an output variable of type `List<SObject>` or a text variable, rather than a specifically typed `List<Recommendation>` collection variable.

**Why it happens:** LLMs generalize Flow variable patterns and default to generic types. The specific requirement that the Actions & Recommendations component expects a Recommendation-typed collection variable is a nuance not always emphasized in training data.

**Correct pattern:**

```text
The strategy Flow output variable must be:
  - Data type: Record
  - Object: Recommendation
  - Allow multiple values (collection): checked
  - Available for output: checked
The Actions & Recommendations component silently ignores
output variables that do not match this exact configuration.
```

**Detection hint:** Check that any Flow output variable instructions specify `Recommendation` as the sObject type and explicitly enable "collection" and "Available for output."

---

## Anti-Pattern 3: Fabricating Recommendation Object Fields That Do Not Exist

**What the LLM generates:** References to fields like `Recommendation.Priority__c`, `Recommendation.Score`, `Recommendation.Category`, or `Recommendation.TargetObject` as if they are standard fields on the Recommendation sObject.

**Why it happens:** LLMs hallucinate plausible field names based on the domain context. The Recommendation object's standard fields are limited to Name, Description, ActionReference, AcceptanceLabel, RejectionLabel, ExpirationDate, and a few system fields. Any additional fields require custom field creation.

**Correct pattern:**

```text
Standard Recommendation fields:
  - Name
  - Description
  - ActionReference
  - AcceptanceLabel
  - RejectionLabel
  - ExpirationDate
Any field beyond these (Priority, Score, Category, TargetObject)
must be created as a custom field and referenced with the __c suffix.
```

**Detection hint:** Flag any Recommendation field reference that lacks the `__c` suffix and is not in the standard field list: Name, Description, ActionReference, AcceptanceLabel, RejectionLabel, ExpirationDate.

---

## Anti-Pattern 4: Suggesting Apex to Directly Render Recommendations in the UI

**What the LLM generates:** Apex controller code that queries Recommendation records and returns them to an Aura or LWC component for custom rendering, bypassing the Actions & Recommendations standard component entirely.

**Why it happens:** LLMs default to code-first solutions. Building a custom component seems like a natural pattern, but it bypasses the platform's built-in acceptance/rejection tracking, Flow-based action execution, and standard NBA analytics.

**Correct pattern:**

```text
Use the standard Actions & Recommendations Lightning component
to display recommendations. This component handles:
  - Invoking the strategy Flow
  - Rendering recommendation cards
  - Executing acceptance actions (linked Flows or quick actions)
  - Tracking acceptance and rejection events
Custom components should only be built when the standard component
genuinely cannot meet UX requirements (rare).
```

**Detection hint:** Look for Apex controllers or LWC/Aura components that query the Recommendation object directly for display purposes. The presence of `[SELECT ... FROM Recommendation]` in a controller paired with a custom component template is a strong signal.

---

## Anti-Pattern 5: Omitting ExpirationDate Filtering in Strategy Flows

**What the LLM generates:** A strategy Flow that retrieves all active Recommendation records via Get Records but does not include any Decision or filter logic to exclude recommendations where ExpirationDate is in the past.

**Why it happens:** LLMs focus on the "happy path" of retrieving and returning recommendations. ExpirationDate filtering is a defensive measure that is easy to overlook, and many example snippets in training data omit it.

**Correct pattern:**

```text
In the strategy Flow, always add one of:
  Option A: Filter in Get Records WHERE ExpirationDate >= TODAY
            OR ExpirationDate = null
  Option B: Add a Decision element after Get Records that excludes
            recommendations with ExpirationDate < TODAY

This prevents expired promotions, seasonal offers, or
compliance-deadline recommendations from appearing to users.
```

**Detection hint:** Examine strategy Flow descriptions for any Get Records element on the Recommendation object. If there is no ExpirationDate filter condition (either in the query or in a subsequent Decision), flag as a potential issue.

---

## Anti-Pattern 6: Assuming NBA Requires Einstein AI Licensing or ML Models

**What the LLM generates:** Statements like "Einstein Next Best Action requires Einstein Analytics licenses" or "you need to train a model before using NBA," implying that AI/ML scoring is a prerequisite.

**Why it happens:** The "Einstein" branding leads LLMs to conflate NBA with Einstein Prediction Builder, Einstein Discovery, or Einstein Analytics. In reality, NBA is fundamentally a rules-based recommendation engine that optionally integrates with AI scoring but does not require it.

**Correct pattern:**

```text
Einstein Next Best Action requires the "Einstein Next Best Action"
permission set license — not Einstein Analytics, Einstein Discovery,
or Einstein Prediction Builder licenses.

NBA works with purely rule-based Flow logic. AI scoring via
prediction models or Response__c tracking is optional and additive,
not a prerequisite.
```

**Detection hint:** Flag any mention of "Einstein Analytics license," "train a model first," or "Einstein Discovery" as prerequisites for NBA. The only required license is the "Einstein Next Best Action" permission set license.
