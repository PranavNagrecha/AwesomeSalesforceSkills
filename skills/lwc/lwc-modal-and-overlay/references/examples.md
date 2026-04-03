# Examples - LWC Modal And Overlay

## Example 1: Return A Selected Record From `LightningModal`

**Context:** A case-assignment component needs a compact picker for queue selection.

**Problem:** The parent component starts trying to manage custom modal markup, open state, and return values in one template.

**Solution:**

Move the focused task into a modal component and return the selected queue name when the user confirms.

```javascript
import { LightningModal } from 'lightning/modal';

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

**Correct approach:** Use `LightningModal` for supported modal workflows and centralize the interaction contract.
