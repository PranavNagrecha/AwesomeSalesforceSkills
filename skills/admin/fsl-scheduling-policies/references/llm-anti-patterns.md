# LLM Anti-Patterns — FSL Scheduling Policies

Common mistakes AI coding assistants make when generating or advising on FSL Scheduling Policies.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Omitting Service Resource Availability Work Rule from Custom Policy

**What the LLM generates:** A policy configuration that includes Match Skills, Hard Boundary, and custom objectives, but omits the Service Resource Availability work rule — because it is not always listed prominently in API documentation and may not appear in training data examples of custom policy XML.

**Why it happens:** LLMs synthesize policy examples from partial documentation and example orgs where the rule may be implicit. The rule name is also generic-sounding compared to more specific rule types, so it gets deprioritized when constructing "minimal viable" policy examples.

**Correct pattern:**

```
Every custom FSL__Scheduling_Policy__c must include at least one FSL__Work_Rule__c
with FSL__Type__c = 'Service Resource Availability'.

Without this rule, resource working hours, operating hours, and absence records
are completely ignored by the scheduling engine.
```

**Detection hint:** Search generated policy configurations for `Service Resource Availability`. If absent, flag the configuration before proceeding.

---

## Anti-Pattern 2: Recommending Direct Edits to Default Policies

**What the LLM generates:** Instructions like "Go to the Customer First scheduling policy and change the ASAP objective weight to 80%" — treating the default policy as the configuration target rather than a clone.

**Why it happens:** Documentation and tutorials frequently show screenshots of default policies as examples. LLMs conflate "this is where the setting lives" with "this is the object you should edit." The distinction between default policies as read-only references and custom policies as the actual configuration surface is easy to miss.

**Correct pattern:**

```
1. Clone the default policy (e.g., Customer First → "Customer First - Production")
2. Make all configuration changes on the clone
3. Assign service territories to the clone, not the default
4. Leave Customer First, High Intensity, Soft Boundaries, and Emergency untouched
```

**Detection hint:** Any instruction containing "edit the Customer First policy" or "modify the High Intensity policy" without a preceding clone step is an anti-pattern.

---

## Anti-Pattern 3: Treating Work Rule Order as a Priority Sequence

**What the LLM generates:** Advice to reorder work rules within a policy to "prioritize" certain filters — e.g., "put Match Skills before Hard Boundary so skill checking happens first," accompanied by a step-by-step guide to drag-and-drop reordering.

**Why it happens:** LLMs trained on general software engineering patterns default to ordered execution semantics (like firewall rules or conditional chains). FSL's simultaneous filter model is counterintuitive and underrepresented in training data.

**Correct pattern:**

```
All work rules in an FSL scheduling policy are applied simultaneously as a combined
filter gate — not sequentially. Rule order in the UI is display-only.

To change filtering behavior, add or remove rules, or use separate policies
for different use cases.
```

**Detection hint:** Any mention of "rule priority," "rule order affects scheduling," or instructions to reorder work rules for a functional reason.

---

## Anti-Pattern 4: Assuming Service Objective Weights Auto-Normalize to 100%

**What the LLM generates:** A policy with objective weights that do not sum to 100% (e.g., ASAP: 50%, Minimize Travel: 50%, Preferred Resource: 30%) presented as valid, on the assumption that Salesforce normalizes them automatically and the practitioner's intended proportions will be preserved.

**Why it happens:** Many systems with weighted scoring auto-normalize weights. LLMs generalize this pattern to FSL without verifying Salesforce's actual behavior. Salesforce accepts arbitrary weight totals without validation errors.

**Correct pattern:**

```
Service objective weights must be manually verified to sum to 100%.
Salesforce does not enforce this constraint and does not auto-normalize.

Example correct weighting for a cost-focused policy:
  Minimize Travel:   50%
  Minimize Overtime: 30%
  ASAP:              20%
  Total:            100%
```

**Detection hint:** Sum all objective weight values in the generated configuration. If the total is not 100%, flag it for manual review.

---

## Anti-Pattern 5: Using FSL Scheduling Policy Concepts for Salesforce Scheduler (Appointment Scheduling)

**What the LLM generates:** Guidance that mixes FSL scheduling policy objects (FSL__Scheduling_Policy__c, FSL__Work_Rule__c) with Salesforce Scheduler configuration (AppointmentTopicTimeSlot, SchedulingPolicy in the Salesforce Scheduler product) — or advises configuring FSL scheduling policies to affect Salesforce Scheduler behavior.

**Why it happens:** Both products have "scheduling" and "policy" in their names and documentation. LLMs frequently blend them, especially when queries mention "Salesforce scheduling policy" without qualifying the product. The two products are completely separate data models with no shared objects.

**Correct pattern:**

```
FSL Scheduling Policies apply ONLY to Field Service Lightning (FSL).
Objects: FSL__Scheduling_Policy__c, FSL__Work_Rule__c, FSL__Service_Objective__c

Salesforce Scheduler (Appointment Scheduling) uses a different configuration surface.
Objects: AppointmentTopicTimeSlot, OperatingHours (shared), but no FSL__ namespace

Do not reference FSL__ objects when configuring Salesforce Scheduler,
and do not reference Salesforce Scheduler documentation when configuring FSL.
```

**Detection hint:** Any configuration that references both `FSL__Scheduling_Policy__c` and Salesforce Scheduler-specific terms (e.g., "Appointment Booking," "Work Type Groups" from Scheduler context) in the same answer.

---

## Anti-Pattern 6: Claiming Yellow Triangle Violations Block Dispatch

**What the LLM generates:** Statements like "if a work rule is violated, the system will not allow the dispatcher to save the appointment" or "yellow triangles prevent scheduling" — presenting violation indicators as hard enforcement gates.

**Why it happens:** LLMs reason by analogy to validation rules, which do block saves. Work rule violations in FSL are designed to inform, not enforce, and this distinction is non-obvious. Documentation describes yellow triangles as "warnings" but does not always emphasize that dispatch proceeds regardless.

**Correct pattern:**

```
Yellow triangle icons on the FSL Gantt indicate work rule violations but do NOT
block the dispatcher from saving or dispatching the appointment.

Violations are advisory. If hard enforcement is required, implement a validation
rule or Apex trigger on ServiceAppointment to block saves that violate critical
policy constraints.
```

**Detection hint:** Any claim that a yellow triangle "prevents," "blocks," or "stops" a scheduling action.
