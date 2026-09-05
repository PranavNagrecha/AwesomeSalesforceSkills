# Examples - LWC Modal And Overlay

## Example 1: Return A Selected Record From `LightningModal`

**Context:** A case-assignment component needs a compact picker for queue selection.

**Problem:** The parent component starts trying to manage custom modal markup, open state, and return values in one template.

**Solution:**

Move the focused task into a modal component and return the selected queue name when the user confirms.

```javascript
import LightningModal from 'lightning/modal'; // default import - no braces

export default class QueuePickerModal extends LightningModal {
    handleSelect(event) {
        this.close({ queueName: event.detail.value });
    }
}
```

```javascript
async openQueuePicker() {
    const result = await QueuePickerModal.open({
        label: 'Choose a queue',
        size: 'small'
    });

    if (result?.queueName) {
        this.selectedQueue = result.queueName;
    }
}
```

**Note on the handler:** `close({ queueName })` is what the caller's `await` resolves to
(`use-dialog-modal`, L10379). Closing with no argument resolves it to `undefined`, and the launcher
can no longer tell a cancel from a save. A production version of this modal tags every exit -
`{ status: 'cancelled' }` versus `{ status: 'confirmed', queueName }` - see
`references/code-examples.md` section 1 for the full component.

**Why it works:** The overlay owns the focused interaction, and the caller only handles the returned outcome.

---

## Example 2: Use A Toast Instead Of A Confirmation Modal

**Context:** A user saves a simple preference change and only needs confirmation.

**Problem:** The team opens a modal that says "Saved successfully" and forces the user to click Close.

**Solution:**

Keep the user in place and show transient feedback.

```javascript
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

handleSuccess() {
    this.dispatchEvent(
        new ShowToastEvent({
            title: 'Preference saved',
            message: 'Your notification settings were updated.',
            variant: 'success'
        })
    );
}
```

**Why it works:** The feedback is visible without forcing an unnecessary modal interaction.

---

## Anti-Pattern: Rebuilding SLDS Modal Markup Everywhere

**What practitioners do:** Each parent component copies modal HTML, local state flags, and focus cleanup logic by hand.

**What goes wrong:** Dismissal, keyboard support, and result passing become inconsistent across the app.

**What it looks like in the parent's JavaScript** - this is the tell, and it is easier to spot than
the markup, because every hand-rolled modal grows the same three members:

```javascript
// BAD: the parent is now the modal's state machine
export default class CaseReassignPanel extends LightningElement {
    isModalOpen = false;          // 1. an open flag the framework should own
    pendingQueueId;               // 2. the modal's draft state, hoisted into the parent
    launcherRef;                  // 3. hand-rolled focus bookkeeping

    handleOpen(event) {
        this.launcherRef = event.target;
        this.isModalOpen = true;
    }

    handleModalConfirm(event) {   // a custom event standing in for a resolved promise
        this.pendingQueueId = event.detail.queueId;
        this.isModalOpen = false;
        this.launcherRef?.focus();
        this.save();
    }

    handleModalCancel() {
        this.isModalOpen = false;
        this.launcherRef?.focus();   // and this is the line that gets forgotten
    }
}
```

All three members disappear with `LightningModal`: the framework owns the open state, the modal owns
its own draft, and `const result = await MyModal.open({...})` collapses the two handlers into one
branch after a single `await`.

**Correct approach:** Use `LightningModal` for supported modal workflows and centralize the interaction contract.
