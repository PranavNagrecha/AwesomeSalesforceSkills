# LLM Anti-Patterns — Revenue Intelligence Setup

Common mistakes AI coding assistants make when configuring Revenue Intelligence.

## Anti-Pattern 1: Confusing RI with CRM Analytics Studio

**What the LLM generates:** Walks the user through building a CRM Analytics dashboard from scratch when the user asks for "pipeline inspection."

**Why it happens:** RI's shipped UI is less familiar to LLMs than generic CRM Analytics.

**Correct pattern:**

```
Turn on the Revenue Intelligence license and app. Pipeline Inspection
and the shipped dashboards appear automatically. Customize, don't
rebuild.
```

**Detection hint:** Step-by-step instructions for "recipe + dataset + dashboard" when the user wanted the shipped RI experience.

---

## Anti-Pattern 2: Skipping Opportunity Field History

**What the LLM generates:** RI activation plan that does not explicitly enable Field History tracking on Amount, Close Date, Stage, Forecast Category.

**Why it happens:** Field History is a small toggle; the model omits it. RI waterfalls are empty without it.

**Correct pattern:**

```
Enable Field History tracking on Amount, Close Date, Stage, Forecast
Category BEFORE deploying RI. Waterfall needs the historical deltas.
History starts from the moment you enable it; pre-existing changes are
not reconstructable.
```

**Detection hint:** An RI rollout plan with no Field History step.

---

## Anti-Pattern 3: Hand-building a deal-slippage report

**What the LLM generates:** A custom report comparing `Opportunity.CloseDate` now vs 30 days ago via date-stamped snapshots in a custom object.

**Why it happens:** The model knows Opportunity reports; Pipeline Inspection is less well-known.

**Correct pattern:**

```
Pipeline Inspection's "Deals Slipped" filter does this natively off
OpportunityFieldHistory. No custom snapshot object required.
```

**Detection hint:** A scheduled Apex or Flow that snapshots Opportunity fields into a custom history table in an RI-licensed org.

---

## Anti-Pattern 4: Deploying Einstein Activity Capture org-wide on day one

**What the LLM generates:** "Enable EAC for all users" as step one.

**Why it happens:** The model optimizes for "turn everything on" and misses the migration cost of EAC's email storage model.

**Correct pattern:**

```
Pilot EAC with a single sales team first. Confirm email sync behavior,
Exchange integration, and privacy posture. Once validated, roll out in
waves.
```

**Detection hint:** An EAC rollout plan with no pilot phase.

---

## Anti-Pattern 5: Ignoring divergence between forecast and role hierarchy

**What the LLM generates:** An RI rollout plan that assumes role hierarchy == forecast hierarchy.

**Why it happens:** In many orgs they diverge (matrix management, overlay sales). The model does not check.

**Correct pattern:**

```
Audit the forecast hierarchy against the role hierarchy before rollout.
Resolve gaps — override forecast managers, restructure forecast users,
or accept partial visibility. Document the model.
```

**Detection hint:** Managers reporting they cannot see their team's data in Pipeline Inspection after go-live.
