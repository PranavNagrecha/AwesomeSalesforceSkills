# Well-Architected Notes — Platform Events Apex

## Relevant Pillars

### Scalability

Platform Events are a decoupling mechanism that lets producers and consumers evolve independently. They are valuable when synchronous transaction coupling would otherwise limit scale.

Tag findings as Scalability when:
- a synchronous integration should be broken into published work
- events are published one-at-a-time inside loops
- consumers are tightly coupled to publisher transaction timing

### Reliability

Event-driven systems are only reliable when publication failures, subscriber failures, and replay expectations are all visible.

Tag findings as Reliability when:
- publish results are ignored
- subscriber processing is heavy and fragile inside the trigger
- external replay requirements are undocumented

## Architectural Tradeoffs

- **Platform Events vs CDC:** CDC is lower-friction for record-change propagation; Platform Events are better for explicit business messages.
- **Thin subscriber trigger vs rich subscriber trigger:** thin triggers are easier to operate and test.
- **Immediate consistency vs eventual consistency:** events reduce coupling but require consumers to tolerate delayed processing.

## Anti-Patterns

1. **Custom event used where CDC already expresses the need** — duplication without architectural gain.
2. **Subscriber trigger doing heavyweight orchestration inline** — brittle and hard to retry.
3. **No publication monitoring** — event-driven failures become invisible until downstream systems complain.

## Official Sources Used

- Platform Events Developer Guide — publication and subscription concepts
- Apex guidance for Platform Events — Apex trigger subscriber behavior and `EventBus.publish`
- Change Data Capture Developer Guide — CDC comparison point
