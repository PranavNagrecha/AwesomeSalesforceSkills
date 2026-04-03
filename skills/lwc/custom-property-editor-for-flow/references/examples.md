# Examples - Custom Property Editor For Flow

## Example 1: Metadata Hook To The Editor

**Context:** A reusable Flow screen component needs a guided design-time configuration experience.

**Problem:** The runtime component exists, but Flow Builder still shows only the default property pane.

**Solution:** Register the editor through the component metadata using the `configurationEditor` relationship on the Flow target configuration.

**Why it works:** Flow Builder can only load the custom editor when the metadata contract points to it.

---

## Example 2: Value-Change Event From The Editor

**Context:** The custom editor renders inputs, but changes do not persist back into Flow Builder.

**Problem:** The editor UI updates itself without notifying the builder contract.

**Solution:**

```javascript
this.dispatchEvent(
  new CustomEvent('configuration_editor_input_value_changed', {
    detail: {
      name: 'label',
      newValue: event.target.value,
      newValueDataType: 'String'
    }
  })
);
```

**Why it works:** The editor now communicates the updated design-time value through the expected event contract.

---

## Anti-Pattern: One LWC Doing Everything

**What practitioners do:** They blur runtime behavior and builder-only editing behavior into one mental model.

**What goes wrong:** The component becomes harder to reason about and Flow Builder integration breaks in subtle ways.

**Correct approach:** Keep runtime and design-time concerns separate and connected by a clear contract.
