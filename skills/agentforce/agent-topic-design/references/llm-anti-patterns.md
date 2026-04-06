# LLM Anti-Patterns — Agent Topic Design

Common mistakes AI coding assistants make when generating or advising on Agentforce topic design.
These patterns help the consuming agent self-check its own output.

## Anti-Pattern 1: Creating One Giant Topic That Covers Everything

**What the LLM generates:** A single topic ("Customer Support") with 15+ actions and broad instructions like "Help the customer with anything related to their account," causing the agent to attempt tasks outside its reliable capability and making debugging impossible.

**Why it happens:** LLMs default to broad categorization. A single topic is simpler to describe. However, the Agentforce topic selector uses topic scope and instructions to route conversations. An overly broad topic accepts every utterance, bypasses scope boundaries, and prevents the agent from gracefully declining out-of-scope requests.

**Correct pattern:**

```text
Topic decomposition strategy:

Bad: 1 topic with 15 actions
  "Customer Support" — handles billing, technical issues,
  returns, account changes, product questions

Good: 3-5 focused topics with 3-5 actions each
  "Billing Inquiries" — check balance, explain charges, payment status
  "Technical Troubleshooting" — diagnose issue, check service status, create case
  "Returns and Exchanges" — check eligibility, initiate return, track return

Sizing guideline:
- 3-5 actions per topic (max 7)
- Each topic maps to one business capability domain
- If a topic needs 10+ actions, it should be split
- Total topics per agent: 5-15 is typical
```

**Detection hint:** Flag topics with more than 7 actions assigned. Check for topics whose instructions contain more than 3 distinct business domains. Flag agents with only 1 topic.

---

## Anti-Pattern 2: Writing Vague Topic Instructions That Do Not Constrain Behavior

**What the LLM generates:** Topic instructions like "Help the customer with billing questions" without specifying what the agent should do, what it should NOT do, what data it can access, and when to escalate.

**Why it happens:** LLMs produce instructions that would work for a human agent who has common sense and organizational knowledge. The Agentforce planner interprets instructions literally. Vague instructions lead to hallucinated answers, unauthorized actions, and failure to escalate.

**Correct pattern:**

```text
Topic instruction template:

You handle [specific domain] for [specific user type].

You CAN:
- [Action 1]: when the user asks [trigger phrase]
- [Action 2]: when the user needs [specific outcome]

You CANNOT:
- Process refunds over $500 (escalate to human agent)
- Access or discuss account balances for other customers
- Make promises about delivery dates not confirmed in the system

When the user asks about [out-of-scope topic], say:
"I can help with [your domain]. For [their request],
please contact [specific channel or team]."

Always confirm [specific data point] before executing [action].

Instruction quality checklist:
- Explicit CAN and CANNOT boundaries
- Named escalation triggers with thresholds
- Out-of-scope response template
- Required confirmations before destructive actions
```

**Detection hint:** Flag topic instructions shorter than 50 words. Check for instructions missing CANNOT or escalation clauses. Flag instructions that do not mention any specific action names.

---

## Anti-Pattern 3: Not Defining Handoff and Escalation Rules

**What the LLM generates:** Topics with no escalation path — the agent either answers everything (even when it should not) or responds with a generic "I cannot help with that" without routing to a human agent or another topic.

**Why it happens:** Handoff configuration requires understanding Omni-Channel routing, transfer-to-agent actions, and topic-to-topic transitions. LLMs focus on the happy path and do not build escalation into the topic design.

**Correct pattern:**

```text
Escalation design patterns:

1. Sentiment-based escalation:
   - Detect frustration (repeated requests, negative language)
   - Transfer to human agent with conversation context
   - Instruction: "If the customer expresses frustration twice
     or requests a human, immediately transfer."

2. Capability-based escalation:
   - Agent cannot perform the requested action
   - Instruction: "If the customer needs to cancel their account,
     transfer to the Account Retention queue."

3. Threshold-based escalation:
   - Business rules require human approval
   - Instruction: "If the refund amount exceeds $200,
     transfer to a supervisor with the case details."

4. Topic-to-topic transition:
   - User's question belongs to a different topic
   - Topic selector should route automatically
   - But if it does not, instructions should say:
     "If the user asks about billing, let me know
     this is outside my Technical Support scope."

Every topic MUST have at least one escalation condition.
```

**Detection hint:** Flag topics with no escalation instruction or transfer-to-agent action. Check for agents with no Omni-Channel transfer action configured. Flag topics whose instructions contain no "transfer", "escalate", or "human" keywords.

---

## Anti-Pattern 4: Overlapping Topic Scopes Without a Topic Selector Strategy

**What the LLM generates:** Multiple topics with overlapping scopes (e.g., "Order Management" and "Returns Processing" both claim to handle "order issues") without configuring the topic selector to disambiguate.

**Why it happens:** LLMs create topics based on business process names without checking for overlap. The Agentforce topic selector uses each topic's scope and classification to route the user's utterance. Overlapping scopes cause unpredictable routing and inconsistent agent behavior.

**Correct pattern:**

```text
Topic boundary management:

Overlap detection:
- List every user utterance each topic claims to handle
- Flag utterances that match 2+ topics
- Resolve by narrowing one topic or merging

Resolution strategies:
1. Sharpen scope language:
   Bad: "Order Management" — handles order questions
   Bad: "Returns Processing" — handles order return questions
   Good: "Order Status and Tracking" — order lookup, shipping status
   Good: "Returns and Refunds" — return eligibility, initiate return

2. Use classification examples in each topic:
   - Add 5-10 example utterances per topic
   - Include near-miss examples that should NOT match

3. Topic selector configuration:
   - Review the topic selector's routing decisions in Agent Builder
   - Test with ambiguous utterances and verify correct routing
   - Adjust topic instructions until routing is deterministic

Testing protocol:
- Create 20 test utterances covering all topics
- Include 5 ambiguous utterances that could go either way
- Verify each routes to the intended topic
```

**Detection hint:** Flag agents with 3+ topics where topic descriptions share more than 50% of the same keywords. Check for topics missing classification examples. Flag agents where testing shows ambiguous routing.

---

## Anti-Pattern 5: Ignoring the Topic's Data Access Scope in Instructions

**What the LLM generates:** Topic instructions that assume the agent can access any Salesforce data without noting that the agent operates under the agent user's permissions and can only query objects and fields the agent user profile can see.

**Why it happens:** LLMs assume system-level data access. In Agentforce, the agent user is a real Salesforce user with a specific profile and permission sets. If the agent user does not have access to a field or object, the agent action will fail silently or return no data, and the agent will respond with "I don't have that information" without explaining why.

**Correct pattern:**

```text
Topic data access design:

For each topic, document:
1. Objects the topic's actions query or modify
2. Fields the topic's actions read or write
3. Record access: OWD, sharing rules, role hierarchy

Then verify:
- Agent user profile has READ on all queried objects and fields
- Agent user profile has CREATE/EDIT/DELETE as needed
- Sharing rules grant the agent user access to relevant records
- If the agent serves multiple customer segments, test with
  records the agent user might NOT be able to see

Topic instruction integration:
- If the agent cannot find a record, instruct it to say:
  "I was not able to find that record. Let me transfer you
  to a team member who can look into this further."
- Do NOT instruct the agent to say "the record does not exist"
  when the real issue may be insufficient access
```

**Detection hint:** Flag topic instructions that reference objects or fields not accessible by the agent user profile. Check for agent users with overly broad "System Administrator" profile assignment. Flag agents where test conversations return "no data found" for records that exist.

---
