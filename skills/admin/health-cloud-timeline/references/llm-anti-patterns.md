# LLM Anti-Patterns — Health Cloud Timeline

Common mistakes AI coding assistants make when generating or advising on Health Cloud Timeline.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Confusing Enhanced Timeline with Standard Activity Timeline

**What the LLM generates:** Instructions to customize the standard Salesforce Activity Timeline (tasks, events, emails) when the user asks about "Health Cloud timeline" — for example, advising the user to modify Activity Settings or the standard `c-timeline` component.

**Why it happens:** "Timeline" is a generic term in Salesforce. Most training data covers the standard Activity Timeline. LLMs default to the more common concept when the Health Cloud context is not explicit.

**Correct pattern:**

```
Health Cloud uses the Industries Enhanced Timeline component (industries:timeline),
configured via TimelineObjectDefinition metadata. This is separate from the standard
Activity Timeline that displays Tasks, Events, and Emails. They coexist on a page
but are configured entirely differently.
```

**Detection hint:** If the response mentions "Activity Settings", "Open Activities", "Activity Timeline" settings, or the standard `c-timeline` component without also referencing `TimelineObjectDefinition`, it has likely conflated the two.

---

## Anti-Pattern 2: Assuming Any Object Can Be Surfaced Without an Account Relationship

**What the LLM generates:** A `TimelineObjectDefinition` for a custom object that has only a `ContactId` lookup (not an `AccountId` or Account lookup), claiming the definition will display records on the timeline.

**Why it happens:** LLMs understand that contacts are related to patients in Health Cloud and may infer that a Contact relationship is sufficient. The specific architectural constraint that Enhanced Timeline anchors exclusively to Account is not widely documented in general Salesforce content.

**Correct pattern:**

```xml
<!-- WRONG: Object only has Contact lookup -->
<baseObject>Clinical_Note__c</baseObject>  <!-- has Contact__c but no Account__c -->

<!-- CORRECT: Verify Account relationship exists first -->
<!-- Clinical_Note__c must have an AccountId or Account__c lookup field -->
<!-- If not, add the lookup and migrate data before creating the definition -->
```

**Detection hint:** If the generated `TimelineObjectDefinition` is for an object whose schema the LLM hasn't verified, or if the response doesn't mention confirming the Account relationship path, treat the output as unvalidated.

---

## Anti-Pattern 3: Recommending the Legacy HealthCloud.Timeline Component for New Configuration

**What the LLM generates:** Setup instructions for the legacy `HealthCloud.Timeline` managed-package component, including references to Health Cloud Custom Settings or the legacy timeline configuration UI, for a requirement that should be implemented using the Industries Timeline + `TimelineObjectDefinition`.

**Why it happens:** The legacy component has more coverage in older Salesforce documentation and community content. LLMs trained before Summer '22 have more exposure to the legacy component than to the Industries Timeline. The deprecation is not widely reflected in training data.

**Correct pattern:**

```
Use the Industries Timeline component (industries:timeline) and configure it via
TimelineObjectDefinition metadata (API v55.0+). The legacy HealthCloud.Timeline
managed-package component is deprecated as of Health Cloud v236 and should not
be used for new configuration.
```

**Detection hint:** If the response references "Health Cloud Custom Settings" for timeline configuration, mentions the namespace `HealthCloud.Timeline`, or instructs the user to modify legacy timeline settings in the managed package, it is directing the user toward the deprecated path.

---

## Anti-Pattern 4: Treating Timeline Category Creation as a Metadata Deployment Step

**What the LLM generates:** A deployment script or metadata file claiming to create timeline categories, or instructions to add categories to a `package.xml` or metadata folder, as if categories are deployable metadata artifacts.

**Why it happens:** LLMs correctly recognize that `TimelineObjectDefinition` is a deployable metadata type and may extrapolate that all timeline configuration is metadata-deployable. Timeline categories are actually configured in Setup and are not part of the Metadata API.

**Correct pattern:**

```
Timeline categories must be created manually in Setup > Timeline > Categories
(or via a post-install script if automating org setup). They are NOT deployable
via the Metadata API or SFDX. Document category values in your deployment runbook
as a manual post-deployment step.
```

**Detection hint:** If the response includes a `timelineCategories/` folder, a `TimelineCategory` metadata type in `package.xml`, or any claim that categories are metadata-deployable, the information is incorrect.

---

## Anti-Pattern 5: Running Both Legacy and Industries Timeline Components Simultaneously for Validation

**What the LLM generates:** A "parallel run" recommendation where both the legacy `HealthCloud.Timeline` and the Industries Timeline component are placed on the same page layout during a migration validation period, reasoning that this allows comparison before cutover.

**Why it happens:** Parallel run is a standard migration pattern in many domains. LLMs apply it here without recognizing that both components query the same underlying data independently, causing duplicate entries rather than a side-by-side comparison.

**Correct pattern:**

```
Do NOT place both components on the same page layout simultaneously. Both components
will query independently and render duplicate entries for any object that appears in
both configurations. For migration validation, use a separate sandbox environment or
a separate page layout assigned to a dedicated validation user profile.
```

**Detection hint:** If the response suggests adding the Industries Timeline to the same page that already has `HealthCloud.Timeline` without removing the legacy component, warn the user of the duplicate-entry risk.

---

## Anti-Pattern 6: Using a Formula Field or Cross-Object Field as the Timeline Date Field

**What the LLM generates:** A `TimelineObjectDefinition` where `dateField` is set to a formula field (e.g., `Effective_Date_Formula__c`) that derives its value from a related object's field.

**Why it happens:** Formula fields are commonly used to surface related-object dates in Salesforce and appear frequently in object schemas. LLMs may recommend them when the canonical date value lives on a parent record.

**Correct pattern:**

```xml
<!-- WRONG: Formula field as dateField -->
<dateField>Encounter_Date_Formula__c</dateField>  <!-- formula from related object -->

<!-- CORRECT: Real date/datetime field on the base object -->
<dateField>Encounter_Date__c</dateField>  <!-- actual date field -->
<!-- If the date lives on a related object, materialize it via Flow or trigger -->
```

**Detection hint:** If the `dateField` value ends in `_Formula__c` or the explanation mentions "cross-object formula" or "formula field that pulls from", the date field choice is likely unsupported for timeline ordering.
