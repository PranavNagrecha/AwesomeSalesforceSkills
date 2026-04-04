# LLM Anti-Patterns — Einstein Bots to Agentforce Migration

Common mistakes AI coding assistants make when generating or advising on Einstein Bots to Agentforce Migration. These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Claiming the Migration Tool Works for Classic/Legacy Bots

**What the LLM generates:** Instructions telling the user to navigate to Setup > Einstein Bots > [their bot] > "Create AI Agent" — without verifying whether the bot is Classic or Enhanced.

**Why it happens:** Training data treats Agentforce migration tooling as universally available. The Classic vs Enhanced bot distinction is a platform infrastructure difference that LLMs conflate.

**Correct pattern:**

```
Before recommending the migration tool, confirm the bot type.
- Check Setup > Einstein Bots. The type column shows "Classic" or "Enhanced".
- The "Create AI Agent from Bot" tool is only available for Enhanced Bots.
- Classic/Legacy Bots have no automated migration path — manual scaffolding is required.
```

**Detection hint:** Flag any migration guidance that recommends "Create AI Agent from Bot" without first confirming the bot is Enhanced.

---

## Anti-Pattern 2: Treating Utterance Volume as a Routing Quality Signal

**What the LLM generates:** Advice to add more utterances to Topic instructions when routing mismatches occur after migration, replicating the NLU training loop pattern from legacy bots.

**Why it happens:** The NLU utterance-training model is deeply represented in training data. LLMs default to it when they encounter routing failure patterns, even when the underlying platform has changed.

**Correct pattern:**

```
Agentforce uses LLM semantic routing — utterances are not a training input.
When routing is incorrect:
1. Open the failing Topic in Agentforce Builder.
2. Rewrite the Topic description as a clear scope statement: what it covers,
   what it does not cover, and example intents in sentence form.
3. Add negative scope boundaries between Topics with overlapping vocabulary.
4. Test in Conversation Preview after each description change.
Do NOT add utterance lists. They do not affect LLM routing accuracy.
```

**Detection hint:** Flag any advice that suggests adding utterances to fix Agentforce routing mismatches.

---

## Anti-Pattern 3: Omitting GenAiPlannerBundle from Deployment Packages

**What the LLM generates:** A `package.xml` or deployment manifest that includes `Bot` and `BotVersion` but omits `GenAiPlannerBundle`, `GenAiPlugin`, and `GenAiFunction`.

**Why it happens:** LLMs have strong prior knowledge of classic Einstein Bot deployment which requires only Bot and BotVersion. The additional Agentforce metadata components are underrepresented in training data.

**Correct pattern:**

```xml
<!-- Agentforce agent deployment — all five component types required -->
<types>
    <members>YourAgentName</members>
    <name>Bot</name>
</types>
<types>
    <members>YourAgentName.v1</members>
    <name>BotVersion</name>
</types>
<types>
    <members>YourPlannerBundleName</members>
    <name>GenAiPlannerBundle</name>
</types>
<types>
    <members>YourTopicName</members>
    <name>GenAiPlugin</name>
</types>
<types>
    <members>YourActionName</members>
    <name>GenAiFunction</name>
</types>
```

**Detection hint:** Flag any Agentforce agent deployment manifest that is missing `GenAiPlannerBundle`.

---

## Anti-Pattern 4: Assuming Context Passes Automatically in the Hybrid Handoff

**What the LLM generates:** Hybrid architecture instructions that say "the bot hands off to Agentforce" without specifying how context (authenticated user, collected slot values, conversation stage) is transferred between the two systems.

**Why it happens:** LLMs describe handoff at the routing layer but omit the data layer. Context persistence between bot sessions and Agentforce sessions requires explicit plumbing that is not intuitive from high-level architecture descriptions.

**Correct pattern:**

```
Hybrid context handoff requires three explicit steps:
1. CREATE MessagingSession custom fields for each context value to transfer
   (e.g., Bot_Authenticated_User__c, Collected_Account_Number__c).
2. WRITE: In the Enhanced Bot dialog, add a step that invokes a Flow.
   The Flow writes context values to the MessagingSession record before
   the session transitions to Agentforce.
3. READ: In the Agentforce agent, implement a "Get Session Context" Action
   that queries the MessagingSession record for these custom fields at the
   start of the session.
Without both the write (bot) and the read (agent), context is not available
to the Agentforce agent.
```

**Detection hint:** Flag hybrid architecture guidance that describes a bot-to-Agentforce handoff without specifying `MessagingSession` custom field population and an explicit read Action.

---

## Anti-Pattern 5: Ignoring the Feb 14 2026 Legacy Chat Retirement Deadline

**What the LLM generates:** Migration plans with no urgency framing, or migration plans that treat the channel cutover as a post-migration cleanup step rather than a hard deadline.

**Why it happens:** LLMs are trained on documentation that may predate the retirement announcement. They do not have inherent urgency awareness about platform retirement dates unless explicitly prompted.

**Correct pattern:**

```
Always surface the Legacy Chat retirement deadline when advising on bot migration:
- Legacy Chat is retiring February 14, 2026.
- Any bot on Legacy Chat that has not migrated to Messaging for In-App and Web
  (or Agentforce) by that date will stop serving users.
- The cutover to a supported channel must be treated as a hard deadline, not
  a post-migration cleanup step.
- Classic bot teams should begin manual migration immediately — the tool-assisted
  path is unavailable to them and manual migration takes longer.
```

**Detection hint:** Flag any bot migration plan that does not mention February 14, 2026 or Legacy Chat retirement when the current scope includes a bot on Legacy Chat.

---

## Anti-Pattern 6: Activating the Migration Tool Output as a Production Agent Without Review

**What the LLM generates:** Instructions that frame the "Create AI Agent from Bot" tool output as a complete migration, suggesting the practitioner activate the generated agent and route live traffic to it.

**Why it happens:** LLMs describe the tool's output optimistically. The tool is in Beta and its output is explicitly a draft — but "generates a draft agent" sounds close enough to "ready to activate" that LLMs elide the review step.

**Correct pattern:**

```
The "Create AI Agent from Bot" tool output is a DRAFT that requires:
1. Topic description rewrites — generated descriptions are dialog names, not
   LLM-routing instructions. Rewrite every Topic before testing.
2. Action implementation — generated Actions are placeholders with no logic.
   Every Action must be backed by a Flow, Apex, or service connection.
3. Routing validation — test every Topic boundary in Conversation Preview
   with real user input samples before activating.
4. Latency validation — measure LLM planning response time against the
   experience SLA before committing to a go-live date.
Do not treat tool output as production-ready. It reduces scaffolding time,
not validation time.
```

**Detection hint:** Flag any instruction that says "run Create AI Agent from Bot, then activate" without a review and validation step in between.
