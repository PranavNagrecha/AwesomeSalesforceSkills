# LLM Anti-Patterns — AWS Salesforce Integration Patterns

Mistakes AI coding assistants commonly make when asked about
Salesforce ↔ AWS integration. The consuming agent should self-check its
output against this list before recommending a path.

---

## Anti-Pattern 1: Recommending a custom Apex callout for event-driven sync

**What the LLM generates.** "Write a Platform Event trigger that publishes
the change to a Lambda Function URL via HTTP POST." Or worse: "Write a
PlatformEventTrigger Apex class that subscribes to the event and calls
Lambda."

**Why it happens.** LLMs default to "if Salesforce, then Apex". Most
training data examples of Salesforce → external systems are Apex
callouts because that was the only option pre-2023. Event Relay (GA
mid-2023) is under-represented.

**Correct pattern.** Event Relay → Amazon EventBridge. Zero Apex.
At-least-once + 72 h replay built in. Refer to
`skills/integration/event-relay-configuration` for the setup recipe.

**Detection hint.** Any recommendation that includes both "Platform
Event" and "callout" in the same Apex class for an outbound integration
is almost always wrong.

---

## Anti-Pattern 2: Hard-coded AWS credentials or endpoints in Apex

**What the LLM generates.**
```apex
HttpRequest req = new HttpRequest();
req.setEndpoint('https://abcd1234.execute-api.us-east-1.amazonaws.com/prod/check');
req.setHeader('x-api-key', 'AKIA...');
```

**Why it happens.** Lambda Function URL examples in AWS-side training
data show the URL inline; LLMs don't know the Salesforce side requires
Named Credential. API key in header is typical of generic-API examples.

**Correct pattern.** Named Credential storing the endpoint + auth.
`HttpRequest.setEndpoint('callout:FX_Service/convert')`. Header secrets
go in Custom Metadata or in the Named Credential's headers definition.
Use `templates/apex/HttpClient.cls`.

**Detection hint.** Any literal AWS endpoint URL (`*.amazonaws.com`,
`*.lambda-url.*.on.aws`) in Apex source is a smell. Same for `AKIA`,
`ASIA`, or other AWS access-key prefixes.

---

## Anti-Pattern 3: Conflating Data Cloud with CRM Analytics or AppFlow

**What the LLM generates.** "Use Data Cloud to build the dashboard and
sync it to Redshift." Or "AppFlow is part of Data Cloud."

**Why it happens.** All three are "Salesforce data integration" features
with overlapping vocabulary; LLMs treat them as interchangeable when
they have distinct roles. Data Cloud was previously branded "Customer
Data Platform" and "Genie", deepening the confusion.

**Correct pattern.** Data Cloud (Data 360) is the unification +
identity-resolution layer; it ingests data from S3, Salesforce, etc. and
produces Data Model Objects. CRM Analytics is a *consumer* that reads
DMOs via the Direct Data Connector. AppFlow is a separate AWS-managed
data-movement service that connects Salesforce to AWS targets — it does
not produce Data Cloud DMOs.

**Detection hint.** Any sentence pairing "Data Cloud" with "dashboard"
or "AppFlow" as if they're the same product surface is wrong. Check
the architectures don't blur the layers.

---

## Anti-Pattern 4: Recommending AppFlow for sub-minute or transaction-bound use cases

**What the LLM generates.** "Use AppFlow with a 30-second schedule to
keep the lookup cache fresh."

**Why it happens.** LLMs see "AppFlow handles Salesforce sync"
generalized too far. The minute floor on schedule-triggered flows is a
documented but easy-to-miss limit, and AppFlow can't run inside a
Salesforce transaction at all.

**Correct pattern.** Sub-minute → CDC trigger in AppFlow (event-driven,
not scheduled) or Event Relay → EventBridge → Lambda. Inside-transaction
→ Apex callout to Lambda via Named Credential. AppFlow is for
scheduled-batch, not real-time and not synchronous.

**Detection hint.** Any AppFlow recommendation with a schedule of
"every X seconds" or wording like "during the save", "before commit",
"inline" is wrong.

---

## Anti-Pattern 5: Assuming Event Relay is bidirectional

**What the LLM generates.** "Configure Event Relay so AWS Lambda can
publish events to Salesforce when DynamoDB rows change."

**Why it happens.** "Relay" sounds bidirectional. The training data
often groups Event Relay with EventBridge in a way that obscures the
direction.

**Correct pattern.** Event Relay is **Salesforce → AWS only**. For the
reverse direction (AWS → Salesforce), configure **EventBridge API
Destinations** to POST to a Salesforce REST endpoint, or use the
Pub/Sub API publish method from a Lambda. That's a separate AWS-side
feature, not part of Event Relay.

**Detection hint.** Any sentence saying "Event Relay sends events to
Salesforce" or "Event Relay is bidirectional" is incorrect. The
correct direction is consistently Salesforce → EventBridge.

---

## Anti-Pattern 6: Forgetting the Refresh Token policy in bring-your-own AppFlow connected app

**What the LLM generates.** Setup steps for AppFlow JWT auth that list
OAuth scopes but omit the Refresh Token Policy.

**Why it happens.** Most Salesforce connected-app examples online don't
mention this policy because the default is fine for interactive-user
apps. AppFlow needs a different default.

**Correct pattern.** In the connected app, set **Refresh Token Policy =
"Refresh token is valid until revoked"** before AppFlow authorizes.
Without this, the connection silently breaks 1–24 hours after the first
run.

**Detection hint.** Any "create your own connected app for AppFlow"
recipe missing the words "Refresh Token Policy" or "Valid until
revoked" is incomplete and will fail in production.
