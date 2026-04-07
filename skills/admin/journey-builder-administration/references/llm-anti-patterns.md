# LLM Anti-Patterns — Journey Builder Administration

Common mistakes AI coding assistants make when generating or advising on Journey Builder Administration.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Treating Exit Criteria as Real-Time

**What the LLM generates:** Advice like "configure exit criteria so that when a contact unsubscribes, they are immediately removed from the journey" — implying instant removal.

**Why it happens:** LLMs generalize from "exit criteria removes contacts" to "therefore it removes them when the condition is met," which implies real-time behavior. The scheduled evaluation cycle is a non-obvious platform constraint not surfaced in high-level documentation.

**Correct pattern:**
```
Exit Criteria evaluate on a scheduled cycle — every 15 minutes by default.
When a contact meets an exit condition, they are removed in the next evaluation window,
not at the moment their data changes.

For compliance-sensitive removals (unsubscribes), rely on Marketing Cloud's
All Subscribers suppression at send time — that is real-time.

Use Exit Criteria as a cleanup mechanism, not an instant gate.
```

**Detection hint:** Flag any response that uses the words "immediately removed," "instantly exits," or "real-time removal" in the context of Exit Criteria.

---

## Anti-Pattern 2: Assuming Contacts Can Re-Enter a Journey by Default

**What the LLM generates:** Instructions that assume a refreshed entry Data Extension will naturally re-enqueue contacts who have already been through the journey — as if journeys are stateless subscribers to a DE.

**Why it happens:** LLMs reason from a general automation model where re-triggering a process is the default. Journey Builder's one-entry-per-version constraint is a specific design decision that contradicts this assumption.

**Correct pattern:**
```
By default, a contact can enter a journey version exactly once.
If re-entry is needed, it must be explicitly enabled in journey settings,
with a minimum re-entry interval (e.g., 30 days, 90 days).

A contact whose entry attempt is blocked by this rule receives no error or notification.
The attempt is silently ignored.

Always verify re-entry configuration when building journeys expected
to run on a recurring or refresh-based schedule.
```

**Detection hint:** Flag responses that say "contacts will re-enter when the automation refreshes" or that describe repeated entry without mentioning the re-entry setting.

---

## Anti-Pattern 3: Recommending In-Place Edits to a Published Journey

**What the LLM generates:** Instructions like "open the journey, edit the email activity, and save" — implying that a published, active journey can be modified in place.

**Why it happens:** LLMs generalize from standard CRUD operations. The concept of immutable versioning (publish = lock) is a domain-specific constraint that is not obvious from the UI description alone.

**Correct pattern:**
```
A published journey version cannot be edited.
To make changes to an active journey:
1. Open the journey in Journey Builder.
2. Click "New Version" to create an editable copy.
3. Make changes in the new version.
4. Publish the new version.
5. Allow in-flight contacts in the original version to complete.
6. Stop the original version once it has drained.

Do NOT stop and recreate the original version — this loses in-flight contact state
and corrupts analytics continuity.
```

**Detection hint:** Flag any response that suggests editing, saving, or updating an active journey's activities without mentioning "new version."

---

## Anti-Pattern 4: Confusing Journey Builder Goals With Salesforce Flow Goals or Campaign Goals

**What the LLM generates:** Advice that conflates Journey Builder Goals (conversion event tracking that exits contacts early) with Salesforce core Campaign Member status, Salesforce Flow decision elements, or other goal-tracking constructs outside of Marketing Cloud.

**Why it happens:** The word "goal" is heavily overloaded across Salesforce products. LLMs trained on broad Salesforce content often pull in Campaign Member status updates or Flow decision outputs when answering Journey Builder goal questions.

**Correct pattern:**
```
Journey Builder Goals are Marketing Cloud-native constructs configured on the journey canvas.
They define a data condition (e.g., field on a Data Extension IS NOT NULL) that,
when met, immediately exits the contact from the journey via the goal path.

Goals evaluate at each activity step as contacts progress.
They contribute to Goal Conversion metrics in Journey Analytics.

Goals are NOT:
- Salesforce Campaign Member status updates
- Flow decision elements
- Einstein Analytics goal metrics
- Pardot completion actions
```

**Detection hint:** Flag any response that recommends updating Campaign Member status as a journey goal mechanism, or that references Flow goals in a Journey Builder context.

---

## Anti-Pattern 5: Advising That All Decision Split Types Are Interchangeable

**What the LLM generates:** Generic advice to "add a decision split" without distinguishing between attribute splits, engagement splits, random splits, and Einstein STO splits — treating them as equivalent options for any routing scenario.

**Why it happens:** LLMs summarize decision splits as a single "branching" concept without encoding the distinct data requirements and use cases of each type.

**Correct pattern:**
```
Decision split types in Journey Builder are NOT interchangeable:

Attribute Split:
  - Routes based on contact data extension field values
  - Requires the attribute field to exist and be populated on the contact
  - Contacts with null attribute values route to the Default arm silently

Engagement Split:
  - Routes based on email interaction history (opened, clicked, not opened, etc.)
  - Only valid after an Email activity in the same journey
  - Cannot route on SMS or push engagement

Random Split:
  - Distributes contacts by percentage (e.g., 50/50, 60/40)
  - No data dependency
  - Correct tool for A/B testing message variants

Einstein STO Split:
  - Routes each contact to the send time most likely to drive engagement,
    based on Einstein's predictive model
  - Requires Einstein Engagement Scoring to be enabled in the Business Unit
  - Test Mode cannot accurately simulate Einstein routing

Choose the split type based on the routing logic required, not on
whichever type comes first in the UI.
```

**Detection hint:** Flag responses that recommend an Engagement Split for routing contacts by demographic attributes, or that recommend an Attribute Split for A/B testing without a specific data-driven rationale.

---

## Anti-Pattern 6: Ignoring Business Unit Scope for Data Extensions and Activities

**What the LLM generates:** Instructions for setting up a journey entry source or Update Contact activity that reference a Data Extension or Salesforce connected app without noting that these must exist within the same Marketing Cloud Business Unit as the journey.

**Why it happens:** LLMs frequently omit Business Unit scoping because it is an organizational context layer not present in simplified examples or documentation excerpts.

**Correct pattern:**
```
Journey Builder is scoped to a Marketing Cloud Business Unit (BU).
The following must all exist within the same BU as the journey:
- Entry source Data Extensions
- Email sends referenced in Email activities
- Data extensions used in Update Contact write-back activities
- API Event definitions

Data Extensions from a parent BU or a different child BU are not accessible
in the journey canvas unless they have been shared to the active BU.

Salesforce Data entry sources require the Marketing Cloud Connect
integration to be configured in the correct BU.

Always verify BU context before building entry sources or activities.
```

**Detection hint:** Flag responses that reference Data Extensions or journeys without mentioning Business Unit context, especially in multi-BU enterprise Marketing Cloud orgs.
