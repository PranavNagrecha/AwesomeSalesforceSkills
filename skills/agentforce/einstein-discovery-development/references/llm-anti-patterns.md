# LLM Anti-Patterns — Einstein Discovery Development

Common mistakes AI coding assistants make when generating or advising on Einstein Discovery Development.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Prediction Scores as Real-Time/Event-Driven

**What the LLM generates:** Statements like "the Einstein Discovery prediction score on the record will update automatically when the Opportunity Stage changes" or Apex trigger code that reads a prediction score field expecting it to have just refreshed.

**Why it happens:** LLMs associate "prediction" with real-time inference (as in ML inference APIs) and do not distinguish between synchronous inference and batch scoring. Training data conflates Einstein Platform Services (real-time) with Einstein Discovery (batch/job-based).

**Correct pattern:**

```
Einstein Discovery scores are written to record fields by bulk predict jobs or explicit
POST /smartdatadiscovery/predict calls. Field value changes do not trigger re-scoring.
To get a current score after a field edit, you must explicitly call the predict endpoint
or schedule a bulk predict job to run.
```

**Detection hint:** Look for claims that score fields "update automatically," "trigger on save," or phrases like "real-time prediction" when discussing Einstein Discovery field values on CRM objects.

---

## Anti-Pattern 2: Omitting the `settings` Object in Predict Requests for v50.0+

**What the LLM generates:** A predict request body that includes only `predictionDefinition`, `type`, and `records`—no `settings` block—while the user expects top predictors and prescriptions in the response.

**Why it happens:** LLMs often use pre-v50.0 examples from documentation or training data where factors were returned by default. They do not incorporate the v50.0 breaking change that made factors opt-in.

**Correct pattern:**

```json
{
  "predictionDefinition": "1ORB000000000bOOAQ",
  "type": "Records",
  "records": ["006RM000002bEfiYAE"],
  "settings": {
    "maxPrescriptions": 3,
    "maxMiddleValues": 3,
    "prescriptionImpactPercentage": 75
  }
}
```

**Detection hint:** Any predict request body that lacks a `settings` key when the user asks for "top factors," "what's driving the prediction," or "improvement suggestions" is missing this field. Flag all predict bodies that have no `settings` property.

---

## Anti-Pattern 3: Treating Bulk Job `Paused` Status as an Error

**What the LLM generates:** Polling logic that raises an exception or alerts on `Paused` status, or code that attempts to delete and recreate the job when it enters `Paused` state.

**Why it happens:** LLMs trained on generic job-processing patterns assume that a non-terminal, non-`Completed` status indicates a recoverable error requiring retry. The Einstein Discovery-specific behavior—that `Paused` means daily limit reached and auto-resumes—is not common enough in training data to override this default pattern.

**Correct pattern:**

```python
if status == "Completed":
    # Success — scores have been written to records
    pass
elif status == "Paused":
    # Daily predictions limit reached — job resumes automatically tomorrow
    # DO NOT delete or recreate the job
    log("Bulk job paused: daily limit reached. Will auto-resume.")
elif status == "Failed":
    raise RuntimeError("Bulk predict job failed — investigate logs")
```

**Detection hint:** Look for `raise`, `throw`, or `alert` on `Paused` status in bulk job polling code, or any code calling DELETE on the job URL when status is `Paused`.

---

## Anti-Pattern 4: Assuming Model Refresh Automatically Activates the New Model

**What the LLM generates:** A pipeline that triggers a refresh job and then immediately starts a bulk scoring job, assuming the refreshed model is now active.

**Why it happens:** LLMs reason by analogy: most ML platforms automatically promote the best model after training. Einstein Discovery does not do this—it requires an explicit activation step. This behavior is counterintuitive and not heavily documented in general ML resources.

**Correct pattern:**

```
Correct pipeline sequence:
1. POST /smartdatadiscovery/refreshjobs — start model retraining
2. Poll GET /smartdatadiscovery/refreshjobs/{jobId} until status = Completed
3. GET /smartdatadiscovery/predictiondefinitions/{predDefId}/models — identify new model version
4. PUT /smartdatadiscovery/models/{newModelId} — activate the new model (set isActive: true)
5. POST /smartdatadiscovery/predictjobs — THEN run bulk scoring
```

**Detection hint:** Any pipeline that moves from refresh job to bulk scoring without an intermediate model activation step is missing step 4. Check for the model activation API call between refresh and scoring.

---

## Anti-Pattern 5: Confusing Einstein Discovery with Einstein Prediction Builder

**What the LLM generates:** Guidance that mixes the two products—e.g., telling a user with a regression use case to use Einstein Prediction Builder, or claiming Einstein Discovery works without a CRM Analytics license, or describing both products as having identical capabilities.

**Why it happens:** Both products share the "Einstein" branding and both deal with predictions on Salesforce objects. LLMs often conflate them, especially when training data includes content about "Einstein predictions" generically.

**Correct pattern:**

```
Einstein Prediction Builder:
- Binary (yes/no) classification only
- No CRM Analytics license required
- Point-and-click setup on any Salesforce object
- API: EinsteinModelFactor SOQL object for reading scores

Einstein Discovery (this skill):
- Regression, multi-class classification, time series
- Requires CRM Analytics (Tableau CRM) license
- Story-based authoring in CRM Analytics Studio
- API: /smartdatadiscovery/ Connect REST endpoints
```

**Detection hint:** Any advice that recommends "Einstein Prediction Builder" for a continuous-value outcome (revenue, score, amount), or that recommends "Einstein Discovery" without mentioning the CRM Analytics license requirement, is exhibiting this anti-pattern.

---

## Anti-Pattern 6: Using Raw Column Names Instead of Story-Trained Field Names

**What the LLM generates:** A `RawData` predict request that populates `columnNames` with Salesforce API field names (e.g., `"Amount"`, `"StageName"`) without confirming that these match the exact column names the story was trained on.

**Why it happens:** The column names used during story training may differ from the raw Salesforce field API names—particularly for related object fields or custom transformations applied during story creation. LLMs default to the most obvious field name convention.

**Correct pattern:**

```
1. Retrieve the model's field configuration:
   GET /services/data/v66.0/smartdatadiscovery/models/{modelId}

2. Inspect the `fields` array in the response to get exact column names.

3. Use those exact names verbatim in the `columnNames` array of the RawData request.

4. After every predict call, check importWarnings.missingColumns in the response.
   If non-empty, the score is degraded and the column mapping must be corrected.
```

**Detection hint:** Any `RawData` predict request constructed without first retrieving the model's field list is potentially using incorrect column names. Also look for responses where `importWarnings.missingColumns` is non-empty but the code does not handle or log it.
