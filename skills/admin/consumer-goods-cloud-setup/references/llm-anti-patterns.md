# LLM Anti-Patterns — Consumer Goods Cloud Setup

Common mistakes AI coding assistants make when configuring Consumer Goods Cloud.

## Anti-Pattern 1: Treating visits as generic Tasks or Events

**What the LLM generates:** Suggests creating custom `Task` records for each store visit with manual assignment.

**Why it happens:** Standard Task/Event is the obvious CRM scheduling primitive; CG Cloud's `Visit` object is industry-specific.

**Correct pattern:**

```
Use the Visit object with VisitTemplate-driven task lists. Visits auto-
generate from RoutePlans. Standard Task/Event is for one-off activities,
not the core merchandising workflow.
```

**Detection hint:** A CG Cloud org where `Task` volume dwarfs `Visit` volume.

---

## Anti-Pattern 2: Skipping RoutePlan and assigning Visits manually

**What the LLM generates:** A Flow that loops through stores and creates Visit records one at a time.

**Why it happens:** The model does not know the shipped RoutePlan regeneration handles cadence, territory, and exceptions automatically.

**Correct pattern:**

```
Create RoutePlan + RoutePlanEntry records. Schedule RoutePlan execution
per week/cycle. Visits are generated in bulk by the shipped engine.
```

**Detection hint:** Any Flow or Apex job named like `GenerateVisits` or `WeeklyVisitCreation` in a CG Cloud org.

---

## Anti-Pattern 3: Using the standard Salesforce mobile app for reps

**What the LLM generates:** "Deploy Salesforce Mobile; configure Lightning pages for Visit; done."

**Why it happens:** The standard Salesforce Mobile app is the most common mobile surface; the CG-specific mobile offline app is industry-proprietary.

**Correct pattern:**

```
Reps use the CG Cloud mobile app (separate install). It has offline
visit cache, image capture optimized for IR, and the shipped Visit
execution UI.
```

**Detection hint:** CG Cloud rollout plans that reference only "Salesforce Mobile" without naming the CG Cloud app.

---

## Anti-Pattern 4: Rolling a custom image recognition pipeline

**What the LLM generates:** A Flow that sends photos to an external AWS Rekognition or Google Vision API, then updates SKU facings.

**Why it happens:** The model knows mainstream vision APIs; Salesforce's shipped Image Recognition for CG Cloud is less well-known.

**Correct pattern:**

```
Use Salesforce Image Recognition (IR). Models are trained per product
line and scored inside the platform. Avoids PII data egress and matches
the shipped IR scoring schema that CG Cloud dashboards expect.
```

**Detection hint:** External callouts to rekognition.amazonaws.com or vision.googleapis.com in a CG Cloud org.

---

## Anti-Pattern 5: Denormalizing retail hierarchy into flat fields

**What the LLM generates:** Fields like `Retailer_Name__c`, `Banner_Name__c`, `Region__c` on `Account` with no parent relationships.

**Why it happens:** Flat denormalization is easier to import; the model does not see the reporting rollup cost.

**Correct pattern:**

```
Use Account hierarchies (ParentId). Retailer → Banner → Store as three
levels. Reports and territory management traverse the hierarchy; flat
fields break the moment you need 'sales by banner'.
```

**Detection hint:** An Account object in a CG org with denormalized retailer fields but no ParentId values set.
