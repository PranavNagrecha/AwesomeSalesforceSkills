# LLM Anti-Patterns — Einstein Next Best Action

Common mistakes AI coding assistants make when generating or advising on Einstein Next Best Action.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Strategy Builder Instead of Flow Builder

**What the LLM generates:** Instructions to create an NBA strategy using Strategy Builder, including references to "Strategy Builder canvas," "Load element," "Filter element," or "Sort element."

**Why it happens:** LLM training data includes pre-Spring '24 documentation and Trailhead content where Strategy Builder was the primary tool. The model defaults to the most frequently represented approach in its training corpus.

**Correct pattern:**

```text
Build new NBA strategies as flows of process type RecommendationStrategy
(Metadata API, API 54.0+) in Flow Builder.
Strategy Builder was deprecated in Spring '24 (UNVERIFIED (2026-10-03): no source
read for this revision states the date; current Trailhead units still show it).
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

**Why it happens:** LLMs hallucinate plausible field names based on the domain context. Earlier versions of this file did it too, by listing ExpirationDate as standard. Per the Object Reference, the Recommendation object's fields are AcceptanceLabel, ActionReference, Description, ExternalId, ImageId, IsActionActive, Name, NetworkId, RecommendationKey, RejectionLabel, plus system fields. Any additional fields require custom field creation.

**Correct pattern:**

```text
Standard Recommendation fields (Object Reference, Spring '26):
  - Name (80)                - Description (255)
  - ActionReference (flow)   - AcceptanceLabel (80)
  - RejectionLabel (80)      - ImageId (ContentAsset)
  - ExternalId               - RecommendationKey
  - IsActionActive (read-only)
  - NetworkId (Experience Cloud site)
Any field beyond these (ExpirationDate, Priority, Score, Category, TargetObject)
must be created as a custom field and referenced with the __c suffix.
```

**Detection hint:** Flag any Recommendation field reference that lacks the `__c` suffix and is not in the standard field list above. `ExpirationDate` without `__c` is the most common one.

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
  - Launching the acceptance flow named in ActionReference
    (and, if shouldLaunchActionOnReject is true, on reject as well)
  - Tracking acceptance and rejection events
Custom components should only be built when the standard component
genuinely cannot meet UX requirements (rare).
```

**Detection hint:** Look for Apex controllers or LWC/Aura components that query the Recommendation object directly for display purposes. The presence of `[SELECT ... FROM Recommendation]` in a controller paired with a custom component template is a strong signal.

---

## Anti-Pattern 5: Omitting Expiry and Active-Flow Filtering in Strategy Flows

**What the LLM generates:** A strategy Flow that retrieves all Recommendation records via Get Records with no filter for expired offers and no filter on `IsActionActive`, or one that filters on a nonexistent standard `ExpirationDate` field.

**Why it happens:** LLMs focus on the "happy path" of retrieving and returning recommendations. ExpirationDate filtering is a defensive measure that is easy to overlook, and many example snippets in training data omit it.

**Correct pattern:**

```text
Add a custom date field Expiration_Date__c to Recommendation, then in the strategy Flow:
  Get Records WHERE IsActionActive = true
               AND (Expiration_Date__c >= TODAY OR Expiration_Date__c = null)
IsActionActive is a standard read-only field; it is false when the
referenced acceptance flow is inactive.

This prevents expired promotions, seasonal offers, or
compliance-deadline recommendations from appearing to users.
```

**Detection hint:** A Get Records element on Recommendation with no `IsActionActive` filter, or with a filter on `ExpirationDate` (no `__c`).

---

## Anti-Pattern 6: Assuming NBA Requires Einstein AI Licensing or ML Models

**What the LLM generates:** Statements like "Einstein Next Best Action requires Einstein Analytics licenses" or "you need to train a model before using NBA," implying that AI/ML scoring is a prerequisite.

**Why it happens:** The "Einstein" branding leads LLMs to conflate NBA with Einstein Prediction Builder, Einstein Discovery, or Einstein Analytics. In reality, NBA is fundamentally a rules-based recommendation engine that optionally integrates with AI scoring but does not require it.

**Correct pattern:**

```text
Einstein Next Best Action requires the "Einstein Next Best Action"
permission set license — not Einstein Analytics, Einstein Discovery,
or Einstein Prediction Builder licenses. (UNVERIFIED (2026-10-03): the
license name; the Object Reference documents the Manage Next Best Action
Recommendations and Manage Next Best Action Strategies permissions.)

NBA works with purely rule-based Flow logic. AI scoring via
prediction models or Response__c tracking is optional and additive,
not a prerequisite.
```

**Detection hint:** Flag any mention of "Einstein Analytics license," "train a model first," or "Einstein Discovery" as prerequisites for NBA. The only required license is the "Einstein Next Best Action" permission set license.

---

## Anti-Pattern 7: Promising a Long List of Recommendations on the Page

**What the LLM generates:** "The Actions & Recommendations component can display up to 25 recommendations, so return your top 25."

**Why it happens:** A number repeated in community content (and in earlier versions of this skill) gets treated as documented. The Metadata API defines `maxDisplayRecommendations` on `RecordActionDeployment` with valid values 1–4, and Trailhead's setup steps say "You can show a maximum of 4 recommendations."

**Correct pattern:** Rank recommendations in the strategy flow, return the few that matter most, and set `maxDisplayRecommendations` between 1 and 4 in the deployment.

**Detection hint:** Any display count above 4 for the Actions & Recommendations component.
