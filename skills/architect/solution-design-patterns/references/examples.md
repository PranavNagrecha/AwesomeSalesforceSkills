# Examples — Solution Design Patterns

## Example 1: Lead Routing — Flow vs. Apex Decision

**Context:** A sales ops team needs to auto-assign new Leads to the correct sales rep based on the Lead's country and industry. There are 12 routing rules today, and the business expects the rules to change quarterly.

**Requirement analysis:**

- Trigger: record insert (new Lead created)
- Logic: match country + industry combination to a queue or user
- Change frequency: quarterly by a sales ops admin
- Callouts required: none
- Volume: ~500 Leads per day

**First instinct (wrong approach):** Build an Apex trigger with 12 `if/else` blocks hard-coding the routing combinations.

**Why this is wrong:**
- Hard-coded routing means every rule change requires a developer, code review, and deployment.
- 12 rules today becomes 40 rules in 18 months — the trigger becomes a maintenance hazard.
- No admin can modify the logic without a developer.

**Correct approach: Flow + Custom Metadata**

1. Create a Custom Metadata Type `Lead_Routing_Rule__mdt` with fields: `Country__c`, `Industry__c`, `Assigned_Queue_API_Name__c`.
2. Populate the CMDT records for each of the 12 rules (deployable, sandbox-safe, no IDs).
3. Build a Record-Triggered Flow on Lead (after insert):
   - Query the CMDT records using a Get Records element (CMDT queries do not count against SOQL limits after first access).
   - Loop through matching rules and set `OwnerId` using an Update Records element.
4. When routing rules change, the sales ops admin updates CMDT records in Setup — no developer, no deployment.

**When this escalates to Apex:** If routing logic requires a same-transaction callout to an external CRM to validate rep territory assignments, Flow cannot make that callout after save. At that point, move the routing logic to an Apex trigger with a `@future(callout=true)` method, keeping the routing rules themselves in CMDT so they remain admin-configurable.

**Key takeaway:** Keep the *routing rules* in CMDT (configurable) and the *routing execution* in whichever layer the callout requirement dictates. Don't let a callout requirement force all logic into Apex if only the callout itself needs to be in Apex.

---

## Example 2: Case Escalation — Layered Design Getting It Right

**Context:** A support team needs to escalate Cases that have been open for more than 48 hours without a response. On escalation: change the priority to Critical, notify the case owner's manager, and log an escalation event to an external ticketing system via REST API.

**Requirement analysis:**

- Trigger: time-based (48 hours since last modified date without owner response)
- Logic: update Priority field, send notification email, POST to external REST endpoint
- Callouts required: yes — POST to external ticketing system
- Volume: up to 200 Cases escalated per run

**Layer analysis:**

| Sub-requirement | Can Flow handle it? | Can it stay in Flow? |
|---|---|---|
| Update Priority field | Yes — Update Records action | Yes |
| Send email to manager | Yes — Send Email action | Yes |
| POST to external REST API | No — Flow cannot make callouts after record save | No — needs Apex |

**Wrong approach (common mistake):** Build everything in Apex because the callout requirement exists. This puts simple field updates and email logic in code, making it harder for admins to change notification recipients or escalation thresholds.

**Correct layered approach:**

1. **Scheduled Flow (declarative layer):** Runs every hour, finds Cases meeting the 48-hour escalation criteria. Updates Priority to Critical and sends the manager email notification. Fires a Platform Event (`Case_Escalation_Event__e`) to signal that a callout is needed.
2. **Apex Platform Event Trigger (programmatic layer):** Subscribes to `Case_Escalation_Event__e`. Receives the Case ID from the event payload and makes the REST callout to the external ticketing system.

This design keeps the declarative work in Flow (visible to admins, no code changes for threshold adjustments) and isolates the callout to Apex where it belongs. The Platform Event decouples the two layers, so a callout failure does not roll back the Priority update.

**Key takeaway:** When a requirement mixes declarative-compatible logic and callout logic, split them using Platform Events rather than collapsing everything into Apex.

---

## Example 3: Opportunity Product Configurator — LWC Justified vs. Over-Engineered

**Context — Version A (over-engineered):** A developer proposes building a custom LWC product configurator to replace the standard Opportunity Products related list because "it would look nicer."

**Why this is wrong:**
- The standard Products related list handles line item management, pricing, and quantity fields out of the box.
- A custom LWC requires JavaScript testing, wire adapter setup, and ongoing maintenance for every Salesforce release that changes related APIs.
- Migrating away from the standard component later (if CPQ is adopted) creates rework against a custom component rather than a standard one.
- No measurable user problem is being solved — "nicer" is not a design requirement.

**Anti-pattern identified:** Over-engineering a standard UI requirement. The blast radius of maintaining a custom UI component for 3–5 years exceeds the benefit.

**Context — Version B (LWC justified):** The same company needs a real-time product bundle configurator that: (a) shows live pricing from an external ERP as the rep selects options, (b) prevents invalid combinations using rules from a pricing engine, and (c) generates a PDF quote preview inline.

**Why LWC is correct here:**
- Live pricing requires real-time wire calls or imperative Apex — not achievable with the standard component.
- Invalid combination prevention requires stateful UI logic (disabling options based on prior selections) — not achievable declaratively.
- Inline PDF preview is a custom rendering requirement — no standard component exists.

**Key takeaway:** LWC is justified when the standard UI genuinely cannot meet the requirement. "Looks better" is not a requirement. Document the specific UI capability gap that forces the custom component — this becomes the long-term justification for the maintenance cost.

---

## Anti-Pattern Example: Mixing Layers for the Same Use Case

**Context:** An org has all of the following active on the Lead object for the `after insert` event:
- A Record-Triggered Flow that sets the `LeadSource` field based on UTM parameters.
- An Apex trigger that also sets `LeadSource` based on the campaign source passed via API.
- A Process Builder that sends a welcome email when `LeadSource` is set to "Web."

**What goes wrong:**
- The Flow runs before the Apex trigger in the after-save execution order. The Flow sets `LeadSource = 'Web'`. The Apex trigger then overwrites it with a different value from the API payload. The Process Builder fires on the Flow's write, not the Apex trigger's write — so the email fires for the wrong source value.
- Debugging this requires understanding three separate tools' execution timing.
- A future developer will not be able to determine which automation "owns" the `LeadSource` field.

**Correct design:**
- Designate a single owner for `LeadSource` assignment: one Record-Triggered Flow (before save, so the value is set before Apex triggers run).
- Remove the Apex trigger's `LeadSource` assignment; if the API needs to override the field, do it explicitly via a field in the API payload that the Flow reads.
- Retire the Process Builder and replace it with a Flow path that sends the email when `LeadSource = 'Web'` in the same Flow.

**Design rule:** One field, one automation layer as the canonical writer. Document the owner explicitly in the object's architecture notes.
