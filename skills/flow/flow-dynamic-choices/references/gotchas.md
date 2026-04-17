# Gotchas — Flow Dynamic Choices

## Gotcha 1: Sharing mismatch

**What happens:** User sees choices they can't open.

**When it occurs:** System context overrides sharing.

**How to avoid:** Match flow context to expected visibility.


---

## Gotcha 2: Empty state not handled

**What happens:** User sees empty dropdown; stuck.

**When it occurs:** Filter yields 0 rows.

**How to avoid:** Decision element after the Get → branch to message.


---

## Gotcha 3: Inactive picklist values

**What happens:** Historical values invisible.

**When it occurs:** Historical records display.

**How to avoid:** Mix Record Choice Set with active flag, or show inactive as read-only.

