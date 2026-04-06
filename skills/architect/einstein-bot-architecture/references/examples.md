# Examples — Einstein Bot Architecture

## Example 1: Tiered Deflection for a Telecom Service Bot

**Context:** A telecom company receives 50,000 cases per month. The top three reasons are bill inquiry (35%), service outage status (25%), and plan change requests (15%). They want to deploy an Einstein Bot on web chat and WhatsApp to deflect the high-volume, low-complexity cases.

**Problem:** Without a tiered architecture, the bot either tries to script every scenario (unsustainable dialog maintenance) or transfers too early (no deflection benefit). The initial design had 45 intents with overlapping utterances, resulting in 40% misroute rates.

**Solution:**

```text
Architecture: 3-Tier Deflection Model

Tier 1 — Knowledge Surfacing (bill inquiry, outage status)
  Intent: billing_inquiry (52 utterances)
  Intent: outage_status (38 utterances)
  Resolution: Einstein Article Recommendations → surface top article
  Exit: customer confirms resolution OR escalate to Tier 2

Tier 2 — Guided Self-Service (plan changes)
  Intent: plan_change (44 utterances)
  Resolution: Collect account number → verify identity → invoke
             Flow "Change Service Plan" via Apex action
  Exit: confirmation message OR escalate to Tier 3

Tier 3 — Agent Handoff (everything else + failed Tier 1/2)
  Transfer variables: detected_intent, account_number, articles_shown,
                      conversation_transcript_summary
  Routing: Skills-Based → "Billing" skill for billing intents,
           "Technical" skill for outage intents
  Agent console: transferred variables displayed in sidebar component
```

**Why it works:** The intent taxonomy was consolidated from 45 to 18 intents based on actual case data. Each tier has a clear exit condition. The handoff carries enough context that the agent does not ask the customer to repeat information. Deflection rate reached 38% in the first month.

**Key architectural decisions:**
- WhatsApp dialogs are text-only; no carousels or rich cards. Article surfacing sends a plain-text summary with a link rather than an embedded card.
- Agent availability is checked before every Tier 3 transfer. If no agents are available, the bot creates a Case with all collected context and offers a callback.
- The fallback intent offers the top 3 most common intents as quick-reply suggestions before escalating, reducing the fallback-to-agent rate by 22%.

---

## Example 2: Agentforce Agent Migration from Legacy Einstein Bot

**Context:** A financial services org has a stable Einstein Bot handling account balance checks and FAQ. They want to migrate to Agentforce Agents to take advantage of the LLM-driven topic model and add new capabilities (transaction dispute filing, document upload guidance).

**Problem:** The team assumed migration meant re-creating each dialog as a topic. They tried to replicate the step-by-step scripted flow inside Agentforce topics, which produced an agent that was rigid and failed on any phrasing the old utterance set did not cover.

**Solution:**

```text
Migration Approach: Redesign, Not Replicate

Legacy Einstein Bot structure:
  Dialog: Check_Balance → 4 steps (greet, collect account, Apex callout, display)
  Dialog: FAQ → 3 steps (greet, keyword match, article display)

Agentforce Agent structure:
  Topic: Account Services
    Description: "Help customers check account balances and recent
                  transaction history. Requires account verification.
                  Does NOT handle disputes, payments, or account closure."
    Actions:
      - Verify_Customer_Identity (Flow)
      - Get_Account_Balance (Apex)
      - Get_Recent_Transactions (Apex)

  Topic: Self-Service FAQ
    Description: "Answer general questions about products, fees, hours,
                  and policies using Knowledge articles. Does NOT handle
                  account-specific requests or transactions."
    Actions:
      - Search_Knowledge_Articles (Flow)

  Topic: Dispute Filing (NEW)
    Description: "Guide customers through filing a transaction dispute.
                  Requires verified identity and transaction reference.
                  Does NOT process refunds or make account adjustments."
    Actions:
      - Verify_Customer_Identity (Flow)
      - Create_Dispute_Case (Flow)
      - Attach_Document_Instructions (Apex)
```

**Why it works:** Instead of replicating dialog steps, the team wrote precise topic descriptions that define scope boundaries. The Agentforce LLM uses these descriptions to match user input to topics, which is more flexible than utterance-based intent matching. The old utterance training data was used to validate topic coverage, not to constrain it.

**Key architectural decisions:**
- The `Verify_Customer_Identity` action is shared across topics. In Einstein Bots this was a duplicated dialog fragment; in Agentforce it is a single reusable Flow.
- Topic descriptions explicitly state what is NOT in scope. This prevents the LLM from routing dispute-related input to the Account Services topic.
- The team ran a 2-week parallel operation where both the legacy bot and the new agent received traffic in sandbox, comparing intent matching accuracy before cutover.

---

## Example 3: Multi-Language Bot for a Global Retail Brand

**Context:** A global retail company operates in 8 countries and supports English, Spanish, French, and German. They need a single Einstein Bot deployment that handles order tracking, return requests, and store locator across all four languages on web chat and WhatsApp.

**Problem:** The initial approach used machine translation to convert 800 English utterances across 16 intents into the three additional languages. The translated utterances produced intent models with low confidence scores in non-English languages because the translations preserved English sentence structure rather than reflecting natural phrasing in each language.

**Solution:**

```text
Architecture: Language-Aware Bot with Native Utterance Training

Language Detection:
  - Web chat: Browser locale detection + explicit language menu at greeting
  - WhatsApp: First message language detection via Einstein Language API
  - Fallback: Ask the customer directly with quick-reply language buttons

Per-Language Intent Model:
  English:  16 intents × 55 avg utterances = 880 utterances (from US/UK case data)
  Spanish:  16 intents × 50 avg utterances = 800 utterances (from MX/ES case data)
  French:   16 intents × 48 avg utterances = 768 utterances (from FR/CA case data)
  German:   14 intents × 45 avg utterances = 630 utterances (from DE case data)
  Note: German has 14 intents because 2 low-volume English intents had
        insufficient German case data to train reliably — they route to fallback.

Dialog Content:
  - Static messages (greetings, confirmations, error messages): Translation
    Workbench with professional translation review
  - Knowledge articles: Salesforce Knowledge with language-specific article
    versions (not machine-translated)
  - Bot variable names: language-agnostic (order_number, not numero_de_pedido)

Handoff Routing:
  - Bot variable: detected_language
  - Omni-Channel: language skill assigned per agent
  - Transfer maps detected_language to required agent skill so German-speaking
    customers route to German-speaking agents
```

**Why it works:** Each language has its own utterance training set sourced from real customer data in that language, not translations. The intent count is allowed to vary by language based on data availability rather than forcing parity. Bot variable names stay language-agnostic so the handoff architecture is identical across languages. The Translation Workbench handles static content while the NLU layer is trained natively per language.

**Key architectural decisions:**
- German launched with 14 intents instead of 16 because two intents did not have enough native German utterances. Forcing these intents with translated utterances would have degraded the model. They will be added when sufficient German case data accumulates.
- WhatsApp messages use plain text only across all languages. The web chat uses quick-reply buttons for language selection at greeting, but these degrade to numbered text options on WhatsApp.
- The team established a quarterly utterance review cycle where native-speaking agents review misrouted conversations and contribute new utterances per language.

---

## Anti-Pattern: Launching with the Full Intent Taxonomy

**What practitioners do:** Build 30+ intents with minimum utterances (20 each), train the model, and launch the bot to all customers on day one. The intent taxonomy is based on the service catalog rather than actual case volume.

**What goes wrong:** Low-volume intents have sparse training data and overlap with adjacent intents, causing misroutes. The team spends the first month triaging false matches instead of improving the high-value intents. Customer satisfaction drops because the bot confidently routes to the wrong dialog.

**Correct approach:** Launch with 3-5 high-volume intents that cover 60-70% of case volume. Each intent has 50+ utterances from real customer language. Add new intents incrementally, one or two at a time, only after the existing intents stabilize with confidence scores above 0.8. Monitor the fallback intent volume to identify which new intents to add next.
