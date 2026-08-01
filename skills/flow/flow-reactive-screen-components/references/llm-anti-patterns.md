# LLM Anti-Patterns — Flow Reactive Screen Components

Scope: making one screen component respond to another's value without navigation.
Building the custom component itself belongs to `flow/flow-screen-lwc-components`;
validation on screen input belongs to `flow/flow-screen-input-validation-patterns`.

## Anti-Pattern 1: Referencing the screen's output variable instead of the component

The single most common cause of "my reactive screen does not update", and it produces no
error — the flow saves, activates and runs, showing a stale or empty value. Referencing a
component's stored output resolves to the value as of when the screen was last committed,
which on a reactive screen is not what the user is currently typing. Reactivity comes from
referencing the **component** and its attribute.

**Wrong** — resolves to the committed value; nothing re-renders as the user types:

```text
Screen:  Screen_Order
  Component: Quantity_Input     (Number)
  Component: Unit_Price_Input   (Currency)

Formula: Line_Total
  {!Screen_Order.Quantity_Input} * {!Screen_Order.Unit_Price_Input}
         ^^^^^^^^^^^^ the SCREEN's stored output, committed on navigation
```

**Right** — references the components themselves, so the formula re-evaluates on change:

```text
Screen:  Screen_Order
  Component: Quantity_Input     (Number)
  Component: Unit_Price_Input   (Currency)

Formula: Line_Total
  {!Quantity_Input.value} * {!Unit_Price_Input.value}
   ^^^^^^^^^^^^^^ the COMPONENT and its attribute, re-evaluated on change
```

The distinction is easy to miss because both forms are valid references that Flow Builder
accepts. If a reactive value is not updating, check this first — it is the cause far more
often than anything else on this list.

## Anti-Pattern 2: Assuming every component is reactive

Reactivity is supported per component and per attribute, not globally. Assistants generate
a reference from any component to any other and it silently does nothing when the target
attribute does not support being driven reactively. Custom components are reactive only
when they are built for it.

❌ Assume a reference makes any attribute reactive.
✅ Check the component reference for which attributes accept a reactive value before
designing the screen around it. For a custom screen component, reactivity requires the
component to be declared for it in its metadata and to dispatch
`FlowAttributeChangeEvent` when its value changes — a component that only exposes an
`@api` property will render, receive nothing, and drive nothing.

Source: Flow screen component reference —
https://help.salesforce.com/s/articleView?id=platform.flow_ref_elements_screencmp.htm

## Anti-Pattern 3: A custom component that reads but never announces

Assistants generate the `@api` property and stop, because that is what makes the value
arrive. The return path is a separate mechanism: without a dispatched
`FlowAttributeChangeEvent`, the flow never learns the value changed, so nothing downstream
reacts and the value is not there at the next Next either.

**Wrong** — the component updates its own state and tells the flow nothing:

```javascript
import { LightningElement, api } from 'lwc';

export default class AmountEntry extends LightningElement {
    @api value;

    handleChange(event) {
        this.value = event.target.value;   // local only; the flow never hears about it
    }
}
```

**Right** — announce the change so the flow can re-evaluate dependents:

```javascript
import { LightningElement, api } from 'lwc';
import { FlowAttributeChangeEvent } from 'lightning/flowSupport';

export default class AmountEntry extends LightningElement {
    @api value;

    handleChange(event) {
        this.value = event.target.value;
        this.dispatchEvent(new FlowAttributeChangeEvent('value', this.value));
    }
}
```

The event name must match the `@api` property name exactly. A mismatch fails silently,
which is the same symptom as omitting the dispatch entirely.

## Anti-Pattern 4: Putting an action behind a reactive change

Reactive evaluation runs as the user interacts, so anything wired to it runs repeatedly —
potentially on every keystroke. Assistants attach a lookup or a callout because the
requirement says "update as they type", and the screen becomes unusable.

❌ An Apex action or an HTTP callout driven by a reactive reference.
✅ Keep reactive dependencies to formulas, visibility conditions and component-to-component
attribute bindings — evaluation that is local and cheap. Anything requiring a round trip
belongs behind an explicit user action or a Next.

## Anti-Pattern 5: Building a chain instead of a graph

Assistants make component C reference B, which references A. Each hop is another
evaluation on every change, and a long chain is both slow and hard to reason about when
one link stops updating.

❌ A → B → C → D, each depending on the last.
✅ Have dependents reference the source directly where the value permits it. A formula
that reads two inputs is clearer and cheaper than three formulas reading each other, and
it fails in one place rather than four.

## Anti-Pattern 6: Visibility conditions that query

Conditional visibility re-evaluates on every reactive change. A condition that compares
against a screen value is free; one that depends on a record retrieved earlier in the flow
is evaluated against a value fetched once, so it goes stale — and one that assistants write
to "look up the current value" is not something a visibility condition can do at all.

❌ Expect a visibility condition to reflect data that changed outside the screen.
✅ Visibility conditions compare against values already in the flow. If the decision needs
fresh data, fetch it before the screen and accept that it is a snapshot, or move the branch
to a Decision element between screens where a Get Records can run.

## Anti-Pattern 7: Testing only on desktop, only in one locale

Reactive screens re-render as the user interacts, and that work is more visible on a phone
than on a laptop. Assistants generate a screen with many reactive dependents, it feels
instant in the builder's preview, and it is sluggish for field users on a mobile
connection.

❌ Debug in Flow Builder and ship.
✅ Test on the Salesforce mobile app on a real device, and test with a user whose locale
formats numbers and dates differently, since reactive formulas that concatenate formatted
values are where locale defects surface. Keep the count of reactive dependents on a single
screen small; splitting a screen is cheap and a slow screen is not.
