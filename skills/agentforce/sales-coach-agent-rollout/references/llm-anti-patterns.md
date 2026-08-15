# LLM Anti-Patterns — Sales Coach Agent Rollout

Common mistakes AI assistants make when generating Sales Coach rollout plans, configuration recommendations, or measurement designs. Avoid these when producing guidance.

---

## Anti-Pattern 1: Recommending bespoke-agent build instead of customizing the shipped template

**What the LLM generates:** "Open Agent Builder and create a new agent. Add subagents for each opportunity stage. Define actions for reading the Opportunity record. Add prompt templates for each role-play scenario..."

**Why it's wrong:** The shipped Sales Coach template already covers 80% of this. Re-building from scratch loses upstream Salesforce-released improvements, adds maintenance burden, and ignores the platform-managed behavior on which the template's reliability rests.

**What to do instead:** Recommend cloning or activating the shipped Sales Coach template, then customizing through (a) grounded Knowledge articles for methodology and objections and (b) additions to the subagent instructions (called topics before April 2026) for ICP seeds. Bespoke build only if the methodology is genuinely incompatible with opportunity-stage role-play.

---

## Anti-Pattern 2: Over-customizing role-play scenarios with hard-coded objection lists

**What the LLM generates:**

```
Subagent instructions:
You are a buyer. When the rep mentions pricing, raise these objections:
1. "Your competitor X is 30% cheaper"
2. "We have budget approval through Q3 only"
3. "Our procurement team requires three quotes"
... (50 more objections enumerated in the instruction body)
```

**Why it's wrong:** Hard-coded objection lists in subagent instructions inflate prompt-token budget on every session, can't be updated without re-publishing the agent, and bleed into every role-play regardless of relevance. Reps perceive the coach as scripted/canned rather than adaptive.

**What to do instead:** Put objections in Knowledge articles tagged for grounding (e.g., `objection-library-healthcare`, `objection-library-finserv`). Reference the tag in subagent instructions: "Reference the objection-library-{industry} grounded source for industry-appropriate objections." The retrieval layer surfaces the relevant 3–5 objections based on context, not all 50.

---

## Anti-Pattern 3: Recommending deployment without a measurement plan

**What the LLM generates:** "Step 1: configure Sales Coach. Step 2: assign permission set. Step 3: train reps. Done — they should start using it."

**Why it's wrong:** A Sales Coach rollout without a measurement plan can't tell you in 12 weeks whether to expand, hold, or sunset. Rollouts that don't measure get cut by the next budget review with no defensible signal either way. The skill exists to produce a *measurable* rollout, not a *deployed* one.

**What to do instead:** Require a measurement design upfront — leading indicators (engagement frequency, session length, stage distribution) plus lagging indicators (win-rate delta within segment, ramp-time delta for new hires) — and the instrumentation to capture them. Frame "what does success look like at week 12?" before "let's configure Agent Builder."

---

## Anti-Pattern 4: Confusing Sales Coach with Einstein Conversation Insights or Sales Cloud Einstein

**What the LLM generates:** "Sales Coach analyzes your call recordings and identifies coaching opportunities" or "Sales Coach predicts which deals are at risk based on the Einstein Opportunity Scoring."

**Why it's wrong:** These are different products. Sales Coach is a role-play / practice agent that the rep initiates a conversation with. Einstein Conversation Insights analyzes recorded calls. Sales Cloud Einstein Opportunity Scoring predicts deal outcomes. Conflating them produces guidance that promises capabilities Sales Coach doesn't have and confuses procurement when the org realizes the licensed feature doesn't do what the AI said it does.

**What to do instead:** Be specific. Sales Coach = role-play and methodology critique, rep-initiated, Opportunity-context-aware. If the user wants call-recording analysis, route them to Einstein Conversation Insights. If they want predictive deal scoring, route them to Sales Cloud Einstein.

---

## Anti-Pattern 5: Recommending "auto-launch on console open" for engagement

**What the LLM generates:** "To boost adoption, set the utility item to Start Automatically so reps see Sales Coach the moment they open the console."

**Why it's wrong:** Reps experience auto-launch as surveillance — "the company is forcing me to use this; what's it logging?" Trust craters, reps work around it, and the practice-tool framing collapses. Engagement metrics initially look better (because the panel is open) but session quality (length, depth) is worse.

**What to do instead:** Recommend Start Automatically OFF. Drive engagement through (a) ICP-seed and grounded-knowledge customization that makes the coach actually useful, (b) explicit no-surveillance framing in the rollout communication, and (c) enablement that ties the coach to specific weekly use cases ("use it before your two hardest meetings this week").

---

## Anti-Pattern 6: Treating coached-vs-uncoached win rate as causal evidence

**What the LLM generates:** "Coached opportunities win at 42% vs uncoached at 31% — Sales Coach is driving an 11-point lift."

**Why it's wrong:** Reps who choose to engage with a coaching tool also tend to prep more, follow up more, and have higher baseline win rates regardless of whether the coach added anything. The 11-point lift is overwhelmingly selection effect, not causal effect. Reporting it as causal misleads leadership and exposes the rollout when the next-quarter trend doesn't hold.

**What to do instead:** Frame coached-vs-uncoached comparison as a *directional indicator* with explicit acknowledgment of selection bias. For causal evidence, recommend a randomized opt-in cohort (e.g., 50% of new hires get coach access at hire, 50% don't, all else equal) and compare ramp time at 90 days. Even then, segment-control the comparison.

---

## Anti-Pattern 7: Hard-coding sales methodology in subagent instructions

**What the LLM generates:**

```
Subagent instructions:
Always evaluate the rep against the MEDDIC framework:
- Metrics: did the rep quantify the buyer's pain?
- Economic Buyer: did the rep identify who controls the budget?
- Decision Criteria: did the rep extract the buyer's decision criteria?
... (full MEDDIC definition pasted into instructions)
```

**Why it's wrong:** The methodology is now buried in Agent Builder, invisible to anyone outside that tool, can't be referenced by Reports or dashboards, and requires re-publishing the agent every time the methodology evolves. Worse: if the org runs more than one methodology (e.g., MEDDIC for enterprise, BANT for SMB), you end up with multiple agents diverging from the canonical methodology document.

**What to do instead:** Author the methodology as a Knowledge article tagged for grounding. Subagent instructions reference the tag: "Critique the rep against the methodology documented in the `sales-methodology` grounded source." Methodology updates propagate without touching the agent.
