# Examples — Sales Coach Agent Rollout

Concrete configuration examples, customization patterns, and measurement queries. The examples assume you have already verified Agentforce entitlement and activated Einstein Generative AI in Setup.

---

## Example 1 — Stage-prompt configuration in Agent Builder

**Goal:** Customize the Discovery-stage role-play so the buyer persona reflects your ICP (mid-market healthcare CISO) instead of the shipped generic buyer.

**Where it lives:** Setup → Agent Builder → Sales Coach (cloned or active version) → Topic: `Discovery_Coaching` → Instructions.

**Before (shipped default, paraphrased):**

```
You are a sales coach helping a rep practice a Discovery conversation.
Play the role of a prospective buyer. Push back on generic claims and
ask probing questions about how the rep's product addresses your needs.
Critique the rep's open questions and pain identification.
```

**After (customized for ICP):**

```
You are a sales coach helping a rep practice a Discovery conversation.
Play the role of a prospective buyer.

Default buyer persona (override only when the Opportunity context indicates
a different profile):
- Title: Chief Information Security Officer
- Industry: mid-market healthcare delivery (500–5000 beds)
- Top three priorities: HIPAA + state-level compliance, ransomware
  resilience, audit-cycle reduction
- Skepticism profile: incumbent vendor relationship of 7+ years, two prior
  failed POCs with newer entrants

Reference the grounded Knowledge articles tagged
`sales-methodology` and `objection-library-healthcare` for stage-appropriate
behavior and likely objections. Critique the rep against the MEDDIC
qualification dimensions documented in the `sales-methodology` article.
```

**Key moves:**
- Persona seed is *overridable* by Opportunity context — the coach still adapts when invoked from a non-healthcare opportunity.
- Methodology reference is *by tag*, not pasted — when the methodology doc is updated, the coach picks it up automatically.
- Don't paste the battle card or objection library into the instruction; reference the grounded knowledge tag.

---

## Example 2 — Custom role-play scenario for a vertical objection

**Goal:** Build a re-runnable role-play for "the data-residency question" that reps in EMEA hear constantly but the shipped coach doesn't surface.

**Approach:** Author a Knowledge article and tag it for agent grounding.

**Knowledge article structure:**

```
Title: Objection — EU Data Residency
Tags: objection-library, region-emea, agent-grounded
Body:

Common buyer concern (verbatim):
  "Where is our data physically stored? We have GDPR Schrems II commitments
   that prohibit transfer outside the EEA without specific safeguards."

Recommended rep response framework:
  1. Acknowledge the concern as legitimate (do not dismiss).
  2. Reference our EU-resident hosting region (Frankfurt) and the
     Standard Contractual Clauses included in our DPA.
  3. Distinguish data-at-rest (always EU) from operational telemetry
     (regional with EU-resident option on Premier tier).
  4. Offer to share the SOC 2 Type II report and the most recent SCC-aligned
     DPA template.

Common rep mistakes:
  - Promising "100% EU" without checking the SKU tier.
  - Conflating data residency with sovereignty.
  - Hand-waving the Schrems II reference without addressing it.

Buyer follow-up they should be ready for:
  - "Who has admin access to the underlying infrastructure?"
  - "What happens to logs in the event of a US subpoena?"
```

**Effect:** When a rep asks the coach to role-play an EMEA Discovery, the coach will surface this objection naturally and critique the rep's response against the framework. Updates to the article propagate without re-publishing the agent.

---

## Example 3 — Embedding Sales Coach in the Lightning sales console

**Goal:** Sales Coach is most effective when reps don't have to context-switch. Embed it as a console utility item so it's one click away from any Opportunity.

**Setup steps:**

1. Setup → App Manager → Sales Console (or whichever app the team uses) → Edit.
2. Utility Items → Add Utility Item → choose **Einstein** (the Agentforce surface). Some org configurations expose this as **Agentforce** directly — pick whichever is available in your edition.
3. Configure:
   - Label: `Sales Coach`
   - Icon: `einstein`
   - Panel Width: 480, Height: 600 (smaller than default; reps need to keep the Opportunity visible)
   - Default Agent: select the published Sales Coach agent
   - Start automatically: **off** (don't auto-open; reps should choose)
4. Save and assign the console app to the pilot permission set.

**What this gets you:** the coach is reachable from the utility bar at the bottom of the console without leaving the Opportunity record. Conversation context picks up the currently-viewed Opportunity automatically, so reps can ask "help me prep for the call on this deal" without restating the deal name.

**Alternative not chosen:** putting the agent on the Opportunity record page as a Lightning component is also possible, but pins one console tab to the agent and competes with Activities, Quotes, and other components for screen real estate. Utility item is the lower-friction default.

---

## Example 4 — Measurement query: win-rate by coached vs uncoached opportunities

**Goal:** Quantify whether coached opportunities win at a different rate than uncoached, controlling for segment.

**Prerequisite:** A custom field `Coach_Session_Count__c` on Opportunity, populated by a flow that increments on each coach session referencing the opportunity. Sales Coach session events surface in Agentforce session logs (Setup → Einstein → Agentforce Analytics or via Data Cloud), which a scheduled flow can join to Opportunity.

**Quarterly comparison query (run in Workbench / Developer Console):**

```sql
-- Conceptual SQL (NOT valid SOQL — SOQL does not support CASE).
-- Implement as a Reports & Dashboards bucket field on Opportunity, or as a
-- Data Cloud / CRM Analytics dataset query.

SELECT
    Segment__c,
    CASE
        WHEN Coach_Session_Count__c >= 3 THEN 'Coached (3+ sessions)'
        WHEN Coach_Session_Count__c BETWEEN 1 AND 2 THEN 'Lightly Coached'
        ELSE 'Uncoached'
    END coachingTier,
    COUNT(Id) opps,
    SUM(CASE WHEN IsWon = true THEN 1 ELSE 0 END) wins,
    AVG(CASE WHEN IsClosed = true AND IsWon = true THEN Amount ELSE NULL END) avgWonAmount
FROM Opportunity
WHERE CloseDate = THIS_QUARTER
  AND IsClosed = true
GROUP BY Segment__c, coachingTier
ORDER BY Segment__c, coachingTier
```

**Caveat to surface in any report:** Reps who use the coach self-select for engagement. A 3+-session cohort likely *also* preps more, follows up more, and has higher baseline win rates regardless of the coach. Treat the comparison as a directional signal, not a controlled experiment, unless you randomize cohort assignment.

---

## Example 5 — Privacy memo template for legal review

**Audience:** Legal / Compliance / DPO before publishing to production.

```
Subject: Sales Coach Agent — Data Flow & Retention Review

1. What data is sent to the LLM
   - Rep's typed input verbatim (the practice question, scenario, response)
   - Opportunity record fields read by the agent's actions: Name, StageName,
     Amount, CloseDate, AccountName, Account.Industry, Description
   - Knowledge article snippets retrieved by grounding (methodology, objection
     library) — only articles tagged for agent access

2. What is NOT sent (subject to Trust Layer masking)
   - Customer PII fields not in the action's read set (Contact email/phone)
   - Restricted classification data (Setup → Data Classification)
   - Fields excluded by Trust Layer policy

3. Where it goes
   - Salesforce-managed LLM gateway (Einstein Trust Layer); zero-retention
     contractual posture per the Salesforce LLM provider agreements published
     in the Einstein Trust Layer documentation
   - Trust Layer applies prompt masking, output validation, and audit logging

4. What is logged on Salesforce side
   - Agentforce session metadata: session id, user id, agent name, timestamps,
     tokens consumed
   - Conversation transcript — retained per the org's Trust Layer retention
     setting (default surfaced in Setup → Einstein → Audit Trail)

5. User-facing controls
   - Reps may opt out by not engaging the agent (no auto-launch is configured)
   - Rep can request log purge via standard data-subject-rights process
   - Manager visibility into individual rep transcripts is OFF by default;
     enabling it requires explicit permission-set assignment

6. Retention
   - Conversation logs: per Trust Layer retention setting (verify in Setup)
   - Aggregated analytics (session counts, durations): retained per
     Agentforce Analytics defaults

Sign-off needed from: DPO, Legal, Sales Operations leadership
```

Adapt to local DPIA / privacy-impact assessment templates. The point is: write it down before publishing, not after the first compliance audit.

---

## Example 6 — Adoption-friction patterns and fixes

| Symptom | Likely cause | Fix |
|---|---|---|
| Engagement spikes week 1, drops 70% by week 3 | Novelty effect; coach not actually helpful for live deals | Re-tune ICP seeds and objection library; add a "use it on this week's actual deals" enablement session |
| Reps rate coaching feedback as "generic" | Methodology source not grounded; coach defaults to general best-practices | Author/tag a methodology Knowledge article; verify it's retrieved by running a test session and asking the coach what methodology it's using |
| Top performers don't use it | Perceived as a "remediation tool"; manager surveillance fear | Frame the rollout as "practice for the hardest deals," explicit no-surveillance policy, opt-in by default |
| Coach contradicts the actual sales playbook | Methodology not grounded OR agent instructions hard-code a different methodology | Audit the agent topic instructions; remove any hard-coded methodology references; rely on grounded knowledge |
| New hires use it heavily, ramp time doesn't shift | Single-tool fallacy; coach helps without replacing real shadowing | Pair coach with structured shadowing program; measure the combined cohort |
