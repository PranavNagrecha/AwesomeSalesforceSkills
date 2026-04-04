# Examples — Einstein Bots to Agentforce Migration

## Example 1: Enhanced Bot Migration Using the "Create AI Agent from Bot" Tool

**Context:** A retail company has an Enhanced Einstein Bot handling three dialogs: Order Status, Return Request, and Password Reset. The bot runs on Legacy Chat. The team has until Feb 14 2026 to migrate off Legacy Chat. They want to use the migration tool to get a structural head start.

**Problem:** After running "Create AI Agent from Bot", the generated Agentforce agent routes "I want to return something" to the Order Status topic instead of Return Request. Additionally, the Return Request Action placeholder has no logic implemented — the Flow it should call does not exist yet in the new agent.

**Solution:**

1. Open the generated agent in Agentforce Builder. Navigate to the Return Request Topic.
2. The generated Topic description reads: `Return Request`. Rewrite it as a routing instruction:
   ```
   Use this topic when a customer wants to initiate, track, or cancel a return or refund
   for an order they have already received. This includes requests to return items,
   exchange products, or receive a store credit.
   ```
3. Review the Order Status Topic description and narrow it to tracking only:
   ```
   Use this topic when a customer asks about the current location, shipping progress,
   or estimated delivery date of an order they have placed. Do not use for return or
   refund requests.
   ```
4. For the Return Request Action placeholder, create a new Flow named `Initiate_Return_Request_Flow` that queries the Order object, validates the return window, and creates a Case with RecordType = Return. Wire the Flow to the Action in Agentforce Builder.
5. Test in Conversation Preview with 10+ return-intent phrasings. Confirm routing is correct.
6. Verify the Legacy Chat channel cutover is planned before Feb 14 2026.

**Why it works:** Agentforce routes semantically against Topic descriptions, not against trained utterances. Two Topics with similar names but vague descriptions produce ambiguous routing. Specific, scope-bounded descriptions — including negative scope ("do not use for") — let the LLM make a clear routing decision without any NLU training.

---

## Example 2: Classic Bot Manual Migration with Hybrid Handoff

**Context:** A financial services firm has a Classic (Legacy) Einstein Bot with 12 dialogs. Six dialogs are deterministic compliance disclosures that must be delivered verbatim per legal requirement. Six dialogs handle open-ended queries (account inquiries, product questions). The compliance dialogs must not be re-implemented in Agentforce because legal requires exact script delivery, not LLM paraphrase.

**Problem:** The team assumed the migration tool would handle their bot. They discover it is Classic (not Enhanced), so the tool is unavailable. They also cannot move the compliance dialogs to Agentforce reasoning control.

**Solution — Hybrid architecture:**

1. Upgrade the Classic Bot to Enhanced (required prerequisite for the hybrid handoff pattern). The six compliance dialogs remain as Enhanced Bot Dialogs.
2. Create a new Agentforce agent manually via Setup > Agentforce Agents > New Agent. Add Topics for each of the six open-ended query categories with LLM-routing descriptions.
3. Add two custom fields to the `MessagingSession` object: `Bot_Authenticated_User__c` (Text) and `Disclosure_Completed__c` (Checkbox).
4. In the Enhanced Bot, add a step at the end of each compliance dialog that invokes a Flow. The Flow sets `Bot_Authenticated_User__c` to the session user Id and `Disclosure_Completed__c` to true, then hands off to the Agentforce agent.
5. Implement a "Get Session Context" Action in the Agentforce agent that queries the `MessagingSession` record and exposes these fields to the reasoning engine. The agent can then confirm the user is authenticated and disclosures are complete before proceeding.
6. Test the full path: compliance dialog completes → bot populates `MessagingSession` fields → handoff → Agentforce reads context → open-ended query resolved without re-prompting for authentication.

**Why it works:** The hybrid pattern is explicitly endorsed by Salesforce for this scenario — deterministic script delivery in the bot, LLM reasoning in Agentforce. `MessagingSession` custom fields are the correct context bridge because they persist across the session boundary and are accessible to both the bot (write) and the Agentforce agent (read). The compliance team retains exact control of disclosure language while the product team gains Agentforce reasoning for open-ended queries.

---

## Anti-Pattern: Treating Utterance Lists as the Primary Routing Mechanism After Migration

**What practitioners do:** After running the migration tool, they find utterance lists imported into the Topic instructions. When routing mismatches occur, they add more utterances — treating the Topic instructions as a training dataset the way they treated utterances in the old NLU-based bot.

**What goes wrong:** Adding utterances to Topic instructions does not improve routing accuracy. Agentforce does not train an NLU classifier from utterances. The LLM reads the full Topic description and matches user intent semantically. A Topic description that is a list of 50 utterances is harder for the LLM to interpret than a single paragraph describing the Topic's scope. Routing ambiguity increases as the description becomes less coherent.

**Correct approach:** Replace utterance lists with a clear, natural-language paragraph describing when this Topic applies. Include positive scope (what it covers), negative scope (what it does not cover), and 2-3 example intents in sentence form. Write the description for a language model to interpret, not for a human to skim.
