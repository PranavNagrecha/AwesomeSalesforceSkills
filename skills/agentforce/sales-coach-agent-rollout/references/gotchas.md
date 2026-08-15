# Gotchas — Sales Coach Agent Rollout

Non-obvious platform behaviors and configuration traps that bite teams during a Sales Coach rollout.

---

## Gotcha 1: Renamed Opportunity stages break shipped stage triggers

**Symptom:** Sales Coach is published, reps invoke it from an Opportunity, but it never picks the stage-specific role-play. Generic coaching only.

**Why:** Sales Coach subagent instructions (subagents were called topics before April 2026) reference stage names like `Discovery`, `Needs Analysis`, `Proposal/Price Quote` literally. If your `OpportunityStage` picklist values are `02 — Discover`, `03 — Validate`, `04 — Propose`, the agent's natural-language stage matching can't reliably tie them to the shipped behaviors. The agent is keyed on labels, not the underlying `IsClosed` / `ForecastCategory` semantics.

**Fix:** Two options. (1) Align local stage labels back to the standard names — usually low-risk if the only variant is a numeric prefix. (2) Edit the agent's subagent instructions in Agent Builder to map your local labels to the coached behaviors, e.g., "When the Opportunity stage is `02 — Discover` or `Discovery`, use the Discovery coaching behavior." Document the mapping so it survives stage-list churn.

---

## Gotcha 2: Conversation transcripts persist longer than reps expect

**Symptom:** A rep practices a sensitive deal scenario and assumes "it's just practice, nothing's logged." Months later, an audit pulls the transcript.

**Why:** Agentforce conversation transcripts are written to Salesforce-side audit logs subject to your Trust Layer retention setting (typically defaults to a multi-month retention window unless an admin explicitly shortens it). Reps treating the coach as ephemeral is a common misconception.

**Fix:** Decide retention policy *before* publishing. Setup → Einstein → Audit Trail → set the retention window appropriate to your compliance posture (shorter is generally better for a coaching tool). Communicate the policy to reps in the rollout announcement so there are no surprises. For regulated industries, document the retention setting in the privacy memo.

---

## Gotcha 3: Multi-currency orgs confuse the coach about Amount

**Symptom:** In a multi-currency org, the coach gives ROI advice citing dollar figures even when the Opportunity is in EUR or GBP. Reps lose confidence in the coach.

**Why:** When the agent reads `Opportunity.Amount`, it gets the value in the record's currency, but the coach's LLM context doesn't always carry the `CurrencyIsoCode` reliably. The model defaults to USD-flavored framing because that's the dominant training data.

**Fix:** Ensure the agent's Opportunity-read action explicitly includes `CurrencyIsoCode` in its read field set. In the subagent instructions, add a directive: "When discussing Opportunity Amount, always state the currency code from the record. Do not assume USD." Test with EUR and GBP opportunities before publishing.

---

## Gotcha 4: Per-rep role-play caps and concurrent-session limits

**Symptom:** A region runs an enablement day, all 50 reps fire up Sales Coach simultaneously, and some reps get `Service unavailable` or rate-limit errors.

**Why:** Agentforce enforces per-org concurrency caps and per-user rate limits that vary by SKU tier and Einstein consumption credit balance. The shipped Sales Coach is not exempt from these limits. A high-concurrency enablement event can saturate the entitlement.

**Fix:** Stagger high-concurrency enablement events (e.g., split the cohort across three time windows). Monitor Einstein consumption in Setup → Einstein → Usage to catch credit-burn surprises early. If your org consistently hits caps, file a usage review with the account team — concurrency limits are negotiable at the SKU level.

---

## Gotcha 5: Knowledge grounding requires explicit Agent-accessible flag

**Symptom:** Admin authors a Knowledge article with the methodology and tags it `sales-methodology`. Rep asks the coach what methodology it's using; coach gives a generic MEDDIC summary that doesn't match the article.

**Why:** Tagging a Knowledge article does not automatically make it accessible to the agent. The article must be in a Knowledge data category / data type that is exposed to the Agent's grounding layer, AND the agent's subagent instructions must reference the tag. If either step is missing, the coach falls back to LLM general knowledge.

**Fix:** (1) In Setup → Einstein → Agent Builder → the agent's grounding configuration, verify the Knowledge data source includes the article's data category. (2) In the subagent instructions, reference the tag explicitly. (3) Test by asking the coach a methodology-specific question and checking whether the article's specifics surface — if you get generic answers, grounding is broken.

---

## Gotcha 6: Auto-launch behavior surprises reps and erodes trust

**Symptom:** Admin enables "Start automatically" on the utility item. Reps open the sales console; the coach panel pops open uninvited. Reps feel surveilled, adoption craters.

**Why:** The "Start automatically" toggle on a utility item opens the panel on every console load. For a tool framed as practice/optional, auto-opening reads as mandatory or surveillance, regardless of intent.

**Fix:** Leave Start Automatically OFF. Position the icon prominently (utility bar) but let reps choose to open it. Re-evaluate after 4 weeks of pilot — if engagement is too low, the answer is improving the coach (more relevant ICP seeds, better grounding) not auto-opening.

---

## Gotcha 7: Permission-set assignment alone doesn't grant access — entitlement also matters

**Symptom:** Admin creates a permission set with the Agentforce user license / permission, assigns it to a rep, but the rep can't see the agent in the utility bar.

**Why:** Sales Coach access requires (a) the user to be on a license type compatible with Agentforce (typically Sales Cloud or Service Cloud user, not Chatter Free, not Customer Community), (b) the permission set to grant the relevant Agentforce permission(s), and (c) sufficient Agentforce entitlement on the org. Missing any of the three blocks access without a clear error.

**Fix:** Verify license type → permission set assignment → Agentforce entitlement in that order when troubleshooting "I can't see the agent." Check Setup → Company Information → Used Licenses for entitlement consumption before adding more pilot users.
