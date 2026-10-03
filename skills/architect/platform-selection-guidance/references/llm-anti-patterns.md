# LLM Anti-Patterns — Platform Selection Guidance

Common mistakes AI coding assistants make when generating or advising on Salesforce platform capability selection.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Recommending Custom Settings When Custom Metadata Types Are the Correct Choice

**What the LLM generates:** "Store your configuration in a Custom Setting so you can query it without SOQL limits" when the use case is org-wide configuration that should be deployable between environments, versioned in source control, and accessible in formula fields.

**Why it happens:** Custom Settings were the standard Salesforce configuration store for years before Custom Metadata Types were introduced. Training data is heavily skewed toward Custom Settings patterns. LLMs default to the older, more represented option.

**Correct pattern:**

```text
Custom Metadata Types (CMDT) vs Custom Settings decision:

Use CMDT when:
- Configuration must be deployable via change sets, packages, or CI/CD
- Values should be version-controlled in source
- Access is needed in formula fields, validation rules, or Flow
- Data is org-wide configuration (not user-specific)

Use Custom Settings (Hierarchy) when:
- Per-user or per-profile override is required
- Runtime reads must not count toward SOQL limits (getInstance() is cached)
- Values change frequently and deployment is not needed

Use Custom Settings (List) rarely — CMDT replaces most List Custom Setting use cases.
```

**Detection hint:** Flag recommendations of Custom Settings that do not mention deployability or compare against Custom Metadata Types. Look for `__c` custom setting references where `__mdt` would be more appropriate.

---

## Anti-Pattern 2: Recommending Aura Components for New Development

**What the LLM generates:** Aura component code or recommendations like "Create an Aura component with a controller and helper" for new feature development, without noting that Lightning Web Components (LWC) is the current standard framework and Aura is in maintenance mode.

**Why it happens:** Aura components dominated Salesforce frontend development from 2015-2019, producing massive amounts of training data. LLMs default to Aura patterns unless explicitly prompted for LWC.

**Correct pattern:**

```text
For all new Lightning component development, use LWC (Lightning Web Components).

Use Aura ONLY when:
1. Extending an existing Aura-heavy codebase where LWC interop would be complex
2. Using Aura-only features not yet available in LWC (e.g., certain
   Lightning Out scenarios, some overlay library patterns)
3. Wrapping an LWC inside an Aura container for backward compatibility

Aura is not deprecated but is in maintenance mode — no new features.
LWC provides better performance, standard web component APIs, and is
Salesforce's strategic investment direction.
```

**Detection hint:** Flag any `<aura:component>`, `component.get()`, `$A.enqueueAction`, or `helper.` references in new component recommendations. Check for Aura controller/helper patterns when LWC would suffice.

---

## Anti-Pattern 3: Conflating Platform Events and Change Data Capture

**What the LLM generates:** "Use Platform Events to track field changes on Account" or "Use Change Data Capture to publish custom business events" — confusing the two event mechanisms and their intended use cases.

**Why it happens:** Both Platform Events and Change Data Capture (CDC) use the event bus and CometD/Pub/Sub API for delivery. Training data discusses them in similar contexts, leading LLMs to treat them as interchangeable.

**Correct pattern:**

```text
Platform Events vs Change Data Capture:

Platform Events:
- Custom-defined event schema (you design the fields)
- Published explicitly via Apex, Flow, or REST API
- Use case: business events, integration triggers, decoupled messaging
- You control when and what to publish

Change Data Capture (CDC):
- Auto-generated events when records are created, updated, deleted, or undeleted
- Schema mirrors the object's field structure
- Use case: real-time replication, external system sync on data changes
- You subscribe, not publish — Salesforce publishes automatically

Do NOT use CDC for custom business events. Do NOT use Platform Events
as a replacement for CDC when the goal is tracking record mutations.
```

**Detection hint:** Flag "Platform Event" recommendations where the goal is tracking record changes (should be CDC), or "Change Data Capture" recommendations where custom business event payloads are needed (should be Platform Events).

---

## Anti-Pattern 4: Recommending OmniStudio Without Checking License Availability

**What the LLM generates:** "Use OmniStudio OmniScripts for this guided process" or "Build this with a FlexCard" without verifying that the org has an OmniStudio license (Industries Cloud, Health Cloud, Financial Services Cloud, or standalone OmniStudio SKU).

**Why it happens:** OmniStudio is increasingly represented in training data, especially for Industries Cloud implementations. LLMs recommend it based on feature fit without checking that it requires a specific license that is not part of standard Sales or Service Cloud.

**Correct pattern:**

```text
Before recommending OmniStudio:
1. Verify the org has an OmniStudio license:
   - Included with: Health Cloud, Financial Services Cloud, Industries Cloud,
     Communications Cloud, Education Cloud
   - Available as: standalone OmniStudio add-on SKU
   - NOT included with: standard Sales Cloud or Service Cloud

2. If no OmniStudio license, recommend alternatives:
   - Screen Flows for guided processes
   - LWC for custom UI experiences
   - Dynamic Forms for record page customization
```

**Detection hint:** Flag OmniStudio recommendations (OmniScript, FlexCard, DataRaptor, Integration Procedure) that do not verify license availability.

---

## Anti-Pattern 5: Choosing Between Flow and Apex Based on Complexity Alone

**What the LLM generates:** "This logic is too complex for Flow, use Apex instead" based solely on the number of conditions or branches, without evaluating the actual technical constraints that require Apex (callouts in the same transaction, complex error handling, unit testing requirements, multi-object DML in a specific order).

**Why it happens:** LLMs apply a subjective complexity threshold ("if it has more than X conditions, use Apex") rather than evaluating the specific Salesforce platform constraints that determine when Flow is insufficient.

**Correct pattern:**

```text
Choose Apex over Flow when the requirement involves:
1. HTTP callouts within a record-triggered context (Flow callouts are async)
2. Complex error handling with try-catch and partial rollback
3. Operations requiring Apex-specific APIs (Queueable chaining, EventBus,
   Crypto class, custom Metadata API calls)
4. Unit test coverage requirements for ISV packaging
5. Performance-critical logic where Flow overhead is measurable

Choose Flow when:
1. The team is admin-heavy and Apex expertise is limited
2. The logic is CRUD + conditions + email/notification
3. Salesforce explicitly supports the pattern in Flow (e.g., before-save updates)
4. Ongoing maintenance should not require a developer

Complexity alone is NOT the deciding factor. A 20-condition Flow may be
perfectly appropriate if it only does field updates and notifications.
```

**Detection hint:** Flag Flow-vs-Apex recommendations that cite "complexity" or "too many steps" without identifying a specific technical constraint that requires Apex.

---

## Anti-Pattern 6: Promising a Longer CDC Retention Window With Shield

**What the LLM generates:** "Turn on Shield Event Monitoring to extend Change Data Capture retention to seven days so the ERP can catch up after long outages."

**Why it happens:** The model mixes CDC retention with the seven-day rotation interval for event bus tenant secrets that appears in the same Shield section of the CDC guide.

**Correct pattern:** The Change Data Capture Developer Guide stores change events for up to three days. High-volume platform events keep 72 hours and legacy standard-volume events 24 hours (Platform Events Developer Guide). Design a reconciliation extract for outages longer than the window instead of buying a licence that does not change it.

**Detection hint:** Any design that cites a seven-day CDC or platform event replay window.

---

## Anti-Pattern 7: Storing Secrets in Custom Settings Because "It's Configuration"

**What the LLM generates:** "Create a hierarchy custom setting `Partner_API__c` with a field for the API key and read it in Apex with `getOrgDefaults()`."

**Why it happens:** Custom settings are the model's default answer for org-wide configuration.

**Correct pattern:** The Apex Developer Guide ("Custom Settings") says custom settings are readable by all profiles, including the guest user, unless they are protected and installed in a managed package, and tells you to use named credentials or encrypted fields for secrets. Put the key in a named credential with an external credential.

**Detection hint:** A custom setting or custom metadata field named like `*_Key__c`, `*_Secret__c`, `*_Password__c`, or `*_Token__c`.

---

## Anti-Pattern 8: Sizing Event Integrations Per Feature Instead of Per Org

**What the LLM generates:** "CDC for the data lake and platform events for the fraud service each have their own 50,000-event daily allocation."

**Why it happens:** The model assumes each feature carries its own quota.

**Correct pattern:** The Platform Events Developer Guide says the default event delivery allocation (50,000 per 24 hours in Performance and Unlimited, 25,000 in Enterprise) is counted per subscribed client and shared between high-volume platform events and CDC, and excludes Apex triggers, flows, and processes. The CDC guide caps entity selection at five without an add-on. Add up every external subscriber's daily events across both features.

**Detection hint:** An integration design that sizes CDC and platform events against separate allocations, or selects more than five CDC entities without mentioning the add-on.
