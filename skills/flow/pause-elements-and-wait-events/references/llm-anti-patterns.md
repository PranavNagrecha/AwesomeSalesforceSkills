# LLM Anti-Patterns — Pause Elements and Wait Events

Common mistakes AI coding assistants make when generating or advising on Pause Elements and Wait Events. These patterns help the consuming agent self-check its own output before delivering guidance.

## Anti-Pattern 1: Recommending a Pause Element in a Record-Triggered Flow for Simple Time-Based Continuation

**What the LLM generates:** Advice to add a Pause element inside a record-triggered flow and set an Alarm wait event offset to "send a reminder 3 days after the record is created."

**Why it happens:** The LLM conflates auto-launched flow Pause elements with the built-in scheduled path capability that record-triggered flows expose directly in their Start element. Training data likely contains many Pause element discussions without distinguishing which flow type they apply to.

**Correct pattern:**

```text
For a single future time-based action in a record-triggered flow:
→ Use a Scheduled Path on the Start element (no Pause element required, no async interview storage consumed)

For multi-window or event-driven time-based actions:
→ Use an auto-launched flow with a Pause element
```

**Detection hint:** Look for "Pause element" appearing in the same advice as "record-triggered flow" for a single-offset time scenario. If the requirement is one future time point with no state continuity, a scheduled path is almost always correct.

---

## Anti-Pattern 2: Omitting Resume Conditions on Platform Event Wait Events

**What the LLM generates:** A Platform Event wait event configuration with no resume conditions, relying on a Decision element after the resume to check whether the event is relevant.

**Why it happens:** LLMs model resume conditions as optional (they are technically optional in the UI) and pattern-match to a "filter later" approach common in other programming contexts. The LLM does not reason about the consequence that every published event of that type resumes every subscribed interview.

**Correct pattern:**

```text
Platform Event Wait Event:
  Event: OrderCallback__e
  Resume conditions:
    OrderId__c = {!$Record.Id}   ← REQUIRED: uniquely binds event to this interview
```

**Detection hint:** Any Platform Event wait event configuration with an empty or missing resume conditions section. Flag immediately and require at least one field-filter condition that uniquely links the event to the interview's record context.

---

## Anti-Pattern 3: Suggesting Flow Builder Debug to Test Pause Element Behavior

**What the LLM generates:** Instructions to "click Debug in Flow Builder, run through the flow until the Pause element, and then verify the wait event branch logic."

**Why it happens:** LLMs correctly know that Flow Builder has a Debug mode and generalize it to all flow elements. The specific exception — that Debug skips Pause elements without evaluating resume conditions — is not widely documented in training data.

**Correct pattern:**

```text
To test an Alarm wait event:
1. Set the Alarm base date to {!$Flow.CurrentDateTime} with offset 0 Days in a sandbox.
2. Trigger the flow on a test record.
3. Confirm the interview appears in Setup > Paused and Failed Flow Interviews.
4. Wait ~15 minutes, then verify the interview has completed and downstream effects are correct.

To test a Platform Event wait event:
1. Trigger the flow and confirm the interview is paused.
2. Publish a test event via Apex anonymous: EventBus.publish(new MyEvent__e(RecordId__c = testId));
3. Confirm the interview resumes and the correct output branch executed.
```

**Detection hint:** Any mention of using Flow Builder debug to step through or verify Pause element behavior. Replace with real-world resume testing instructions.

---

## Anti-Pattern 4: Suggesting That Paused Interviews Resume Immediately When Alarm Offset Is Zero

**What the LLM generates:** "Set the alarm offset to 0 days to have the interview resume as soon as possible after the pause" — implying near-instant or same-transaction continuation.

**Why it happens:** "0" intuitively means "no delay" in most programming contexts. The LLM does not know about Salesforce's platform minimum fire time of approximately 15 minutes for Alarm wait events.

**Correct pattern:**

```text
Alarm offset of 0 Days → resumes after approximately 15 minutes minimum (platform enforced)

For immediate resume (sub-minute):
→ Use a Platform Event wait event with a matching event published immediately
→ Or restructure the flow to not require a pause at all
```

**Detection hint:** Phrases like "immediately," "right away," or "as soon as possible" paired with an Alarm wait event and an offset of 0. Flag as incorrect and clarify the ~15-minute minimum.

---

## Anti-Pattern 5: Treating User-Initiated Screen Flow Pause and Pause Element as the Same Feature

**What the LLM generates:** Instructions that mix up "users can pause a screen flow by clicking Save for Later" with "add a Pause element to your auto-launched flow to wait for an event" — treating them as interchangeable or as the same mechanism.

**Why it happens:** Both features are called "pause" in Salesforce documentation and marketing content. LLMs conflate the two because they appear in similar search results and documentation pages.

**Correct pattern:**

```text
User-initiated pause (screen flows):
- User clicks "Save for Later" in a screen flow
- Enabled via Process Automation Settings: "Let Users Pause and Resume Flows"
- Interview is private to the pausing user
- Resumed by the same user from their Paused Interviews list
- No Pause element required in the flow

Pause element (auto-launched and screen flows):
- Developer-placed element in the flow canvas
- Suspends the interview on a timed Alarm or Platform Event
- Resumes automatically when resume condition is satisfied
- Automated Process user context on platform event resume
- Requires explicit event or alarm configuration
```

**Detection hint:** Advice that conflates "Process Automation Settings" with the behavior of the Pause element, or vice versa. Or advice suggesting the Pause element can be triggered by a user clicking a button.

---

## Anti-Pattern 6: Forgetting the Timeout Watchdog on Platform Event Waits

**What the LLM generates:** A Pause element with only a Platform Event wait event and no Alarm fallback, with a comment like "the flow will wait until the event arrives."

**Why it happens:** The LLM focuses on the happy path (event arrives, interview resumes, processing continues) and does not reason about the failure case (event never arrives). Indefinitely suspended interviews are invisible operational failures.

**Correct pattern:**

```text
Pause Element:
  ├── Wait Event 1 — Platform Event: CallbackEvent__e
  │     Resume conditions: RecordId__c = {!recordId}
  │     Output: [success handling]
  │
  └── Wait Event 2 — Alarm (TIMEOUT WATCHDOG — always include)
        Base date: {!$Flow.CurrentDateTime}
        Offset: 24 Hours  (adjust to SLA)
        Output: [error handling: log, alert, compensate]
```

**Detection hint:** Any Pause element design with only a Platform Event wait event and no companion Alarm wait event. Flag as missing a required timeout and require the practitioner to define a maximum acceptable wait duration.
