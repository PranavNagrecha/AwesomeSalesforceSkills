# Examples - Screen Flows

## Example 1: Gather, Review, Then Update The Record

**Context:** A support manager needs a guided flow to close a case with closure reason, customer impact, and final notes.

**Problem:** The original flow updates the Case after the first screen, then asks for confirmation on a second screen. Back and cancel become confusing because the record already changed.

**Solution:**

Split the flow into collection and confirmation before the final update.

```text
Screen 1: Closure inputs
- Close_Reason
- Customer_Impact
- Resolution_Notes

Screen 2: Review summary
- Display Text with chosen values
- Confirm checkbox

After Screen 2:
- Update Records: Close Case
```

**Why it works:** The user commits only after seeing the final summary, so navigation and intent stay aligned.

---

## Example 2: Custom LWC Screen Component With Flow Validation Methods

**Context:** A shipping screen needs a custom postal-code component because the business wants live formatting and external validation feedback.

**Problem:** The component renders correctly but Flow navigation does not show errors consistently.

**Solution:**

Implement the Flow validation contract methods explicitly.

```javascript
import { api, LightningElement } from 'lwc';

export default class PostalCodeInput extends LightningElement {
    @api value;
    externalError = '';

    @api validate() {
        const isValid = Boolean(this.value);
        return { isValid, errorMessage: isValid ? null : 'Postal code is required.' };
    }

    @api setCustomValidity(message) {
        this.externalError = message || '';
    }

    @api reportValidity() {
        const input = this.template.querySelector('lightning-input');
        input.setCustomValidity(this.externalError);
        input.reportValidity();
    }
}
```

**Why it works:** The component aligns its internal rules and externally supplied errors with the Flow runtime lifecycle.

---

## Anti-Pattern: DML In The Middle Of A Long Interview

**What practitioners do:** They create or update records midway through a screen flow and keep collecting information afterward.

**What goes wrong:** Users assume Back or Cancel will undo the work, but the transaction has already committed meaningful state.

**Correct approach:** Delay final mutation until the user reaches a natural confirmation or completion point whenever the business process allows it.
