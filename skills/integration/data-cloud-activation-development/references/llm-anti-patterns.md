# LLM Anti-Patterns — Data Cloud Activation Development

## Anti-Pattern 1: Conflating Activation Targets with Data Action Targets

**What the LLM generates:** Instructions to create a webhook under "Activation Targets" for near-real-time event-level integration with an external system.

**Why it happens:** Both terms contain "activation" and "target" and appear in the same Data Cloud Setup area. LLMs conflate segment-level Activation Targets (batch publishing) with event-level Data Action Targets (near-real-time).

**Correct pattern:** For event-level near-real-time webhooks, create a **Data Action Target** (not Activation Target) in Data Cloud Setup, then link a Streaming Insight to it.

**Detection hint:** If the instructions say "Activation Target" but describe per-event near-real-time behavior, it is using the wrong surface.

---

## Anti-Pattern 2: Creating Webhook Target Without HMAC Secret Key

**What the LLM generates:** Webhook Data Action Target configuration with no HMAC key, or instructions to add the HMAC key later after testing.

**Why it happens:** LLMs treat HMAC as an optional security enhancement rather than a required field for payload delivery. Training data may include examples where HMAC is skipped for simplicity in demos.

**Correct pattern:** Always configure the HMAC-SHA256 secret key during Data Action Target creation. A blank HMAC key silently prevents any payload from being delivered — there is no test mode that bypasses this.

**Detection hint:** Any webhook Data Action Target configuration that omits the HMAC secret key field is incorrect.

---

## Anti-Pattern 3: Using CRM Record-Triggered Flows for DMO Insert Events

**What the LLM generates:** A record-triggered Flow on the Contact or Account object designed to respond when Data Cloud creates a unified profile.

**Why it happens:** LLMs default to the familiar record-triggered Flow pattern. They are not aware that Data Cloud DMO insertions do not trigger standard Salesforce record-triggered Flows — a completely separate mechanism (Data Cloud-Triggered Flows) is required.

**Correct pattern:** Create a **Data Cloud-Triggered Flow** in Data Cloud Setup, binding an autolaunched Flow to a specific DMO. This is the correct trigger surface for DMO insert-driven automation.

**Detection hint:** Any record-triggered Flow on a standard CRM object that claims to respond to Data Cloud unified profile creation is using the wrong trigger.

---

## Anti-Pattern 4: Assuming Data Cloud-Triggered Flows Fire on Profile Updates

**What the LLM generates:** "When a customer's churn risk score is updated in Data Cloud, the triggered flow will automatically fire and create a task."

**Why it happens:** LLMs infer that "triggered" means "on any change." Data Cloud-Triggered Flows fire exclusively on DMO row **insertion**, not update. The constraint is not intuitive.

**Correct pattern:** If the use case is update-triggered, either (a) design the scoring pipeline to insert new rows into a separate event DMO on each score change, or (b) use Calculated Insights with delta detection and a separate downstream process.

**Detection hint:** Any claim that a Data Cloud-Triggered Flow fires on a record update (score change, attribute modification) is incorrect.

---

## Anti-Pattern 5: Omitting Dead-Letter Handling for Webhook Targets

**What the LLM generates:** Webhook integration design with no mention of failure handling, assuming Data Cloud will retry failed deliveries.

**Why it happens:** Many event streaming platforms (Kafka, AWS EventBridge, Azure Service Bus) offer automatic retry. LLMs apply this assumption to Data Cloud Data Action Targets, which do NOT retry.

**Correct pattern:** Design the integration with an external dead-letter queue (AWS SQS, Azure Service Bus, GCP Pub/Sub). The webhook receiver should publish failed-processing events to the dead-letter queue for independent retry. Monitor the 4-day event retention window — events lost after retention cannot be replayed.

**Detection hint:** Any Data Cloud webhook integration design that does not address delivery failure handling or dead-letter queuing is incomplete.
