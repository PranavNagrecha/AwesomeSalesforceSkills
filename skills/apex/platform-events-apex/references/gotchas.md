# Gotchas — Platform Events Apex

Non-obvious Salesforce platform behaviors that cause real production problems in this domain.

## `EventBus.publish` Needs Result Handling

**What happens:** The publish call is made and nobody checks the returned result, so failures disappear into the background.

**When it occurs:** Teams treat event publication like `System.enqueueJob()` with no follow-up.

**How to avoid:** Inspect the returned save results and route failures into a real logging or alerting path.

---

## Apex Event Triggers Are Not Replay Managers

**What happens:** Architects try to solve external consumer replay recovery inside Apex trigger code.

**When it occurs:** Platform Events and Pub/Sub API responsibilities are blurred.

**How to avoid:** Keep replay ID management in external subscribers or middleware. Apex event triggers consume delivered events; they do not own subscriber replay state.

---

## Publishing In Loops Creates Operational Noise

**What happens:** One event is published per record inside a loop.

**When it occurs:** Developers port synchronous trigger habits directly into event publication code.

**How to avoid:** Build a list of events and publish once. It is simpler to monitor and safer at scale.

---

## CDC And Platform Events Sound Similar But Drive Different Contracts

**What happens:** Consumers are built against a custom event when they really need row-change semantics, or vice versa.

**When it occurs:** There is no explicit decision about business event versus data-change event.

**How to avoid:** Make the decision rule explicit during design and document why CDC or Platform Events was chosen.
