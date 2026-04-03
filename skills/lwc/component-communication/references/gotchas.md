# Gotchas - Component Communication

## Default Event Propagation Is Narrower Than Many Teams Expect

**What happens:** A child dispatches a custom event, but the parent or ancestor never receives it.

**When it occurs:** The event needs to bubble or cross a shadow boundary, but `bubbles` and `composed` were not set intentionally.

**How to avoid:** Decide the propagation scope up front and set event options explicitly rather than assuming the default is enough.

---

## Event Names Are Public API

**What happens:** A component ships event names with uppercase letters, spaces, or `on` prefixes, and consumers struggle to wire listeners consistently.

**When it occurs:** Teams treat event names like arbitrary strings instead of markup-facing API contracts.

**How to avoid:** Use lowercase, intention-revealing event names and keep them stable once consumers depend on them.

---

## LMS Without Cleanup Creates Sticky Behavior

**What happens:** Components continue reacting to messages after the user has navigated away or changed workspace context.

**When it occurs:** A subscription is created but not released at the right lifecycle boundary.

**How to avoid:** Subscribe intentionally, keep the subscription handle, and unsubscribe when the component scope ends.

---

## Mutable Shared Objects Make Ownership Ambiguous

**What happens:** A parent and child both mutate the same object reference, and rerender behavior becomes confusing.

**When it occurs:** Teams pass rich objects down and treat them like shared state rather than input plus event-driven updates.

**How to avoid:** Keep data flow directional. Clone or reconstruct state in the owner component and pass only what the child needs.
