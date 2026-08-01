# Examples — OmniStudio LWC OmniScript Migration

Neither example states a release number or a cutoff date. Those are the facts most likely to
be stale, and a wrong one propagates into a programme plan and is defended long after it
could have been checked. Fetch timing from the current release notes; use these for
sequencing and parity.

## Example 1: Sequencing 80 scripts by risk rather than by count

**Context:** An org with roughly eighty OmniScripts, some trivial and some carrying the main
customer-facing journey.

**Problem:** The first plan was "ten scripts a week for eight weeks", which spread attention
evenly across a distribution that is not even. Most of the eighty were short and linear. Six
embedded custom components, and those six carried nearly all the effort and nearly all the
risk — but under an alphabetical schedule two of them landed in the final week, with no room
to react.

**Solution:** Inventory what actually determines effort, and sequence by it.

```apex
// Effort is driven by embedded custom components and branching, not by script count.
// This produces the ranking input; a human decides the order from it.
public class MigrationInventory {

    public class ScriptRisk {
        @AuraEnabled public String  scriptName;
        @AuraEnabled public Integer customComponents;   // the real cost driver
        @AuraEnabled public Integer branchCount;        // the real QA driver
        @AuraEnabled public Boolean businessCritical;   // set by a human, not derived
    }

    // Rank: custom components dominate, branches next, criticality breaks ties.
    public static Integer score(ScriptRisk r) {
        return (r.customComponents * 10)
             + (r.branchCount * 2)
             + (r.businessCritical ? 25 : 0);
    }
}
```

```json
{
  "sequencing_rule": "highest score first, while there is the most time to react",
  "example_ranking": [
    { "script": "Customer_Onboarding",  "customComponents": 3, "branches": 14, "critical": true,  "note": "signature capture + two Angular-era widgets" },
    { "script": "Claim_Submission",     "customComponents": 2, "branches": 9,  "critical": true },
    { "script": "Address_Change",       "customComponents": 0, "branches": 3,  "critical": false, "note": "linear; low risk; batch these late" }
  ],
  "what_this_is_not": "a per-script runtime toggle. The runtime setting is org-level — see anti-pattern 3 — so the rollback plan cannot assume per-script reversal."
}
```

**Why it works:** it puts the irreducible work at the front of the schedule instead of the
end. The six scripts with embedded components are development projects; the rest are
verification. Discovering that in week eight is the difference between a delayed migration and
a failed one.

**The constraint that shapes the rollback plan:** the runtime is governed by org-level
settings — documented as **Disable the Managed Package Runtime** and **Deploy Custom Lightning
Web Components in Standard Runtime** — not by a per-script switch. Confirm what those control
in your org before designing a sequence whose safety depends on reverting one script.

**What belongs in the plan that is not functional:** styling and layout differ between the
runtimes. A visual comparison of the high-traffic screens belongs in the migration plan
rather than in the bug backlog after go-live, because it is cheap to schedule and expensive to
discover.

**Why the business case does not carry a percentage:** the supportability argument is
sufficient and does not decay — Omnistudio no longer supports OmniScripts built on AngularJS,
and the documented remedy is migration to the OmniScript Lightning Web Component framework. A
borrowed "30–60% faster" figure sets an expectation the migration is then measured against.
Measure your own scripts if a number is wanted.

---

## Example 2: Replacing an embedded component rather than porting it

**Context:** A signature-capture element embedded inside the onboarding script, originally
built against the Angular-era runtime.

**Problem:** The component reached into the surrounding runtime for the script's data and to
push its result back. That is not how a Lightning Web Component participates in an OmniScript:
data arrives through public properties and results go back through dispatched events. There
was no porting path — the component had to be rebuilt against the documented contract.

**Solution:** A custom LWC added to the OmniScript through the documented custom-component
path.

```javascript
// signatureCapture.js — rebuilt for the OmniScript LWC framework.
// Verify the exact property and event names against the current custom-LWC documentation
// for your runtime before building; they are documented and not worth reciting from memory.
import { LightningElement, api } from 'lwc';

export default class SignatureCapture extends LightningElement {
    @api omniJsonData;      // data from the OmniScript
    @api omniJsonDef;       // this element's own definition
    @api omniApplyCallResp; // response plumbing supplied by the framework

    captured = false;

    handleSignatureComplete(dataUrl) {
        this.captured = true;
        // Results go back through an event, not by mutating shared runtime state.
        this.dispatchEvent(new CustomEvent('omniapply', {
            bubbles: true,
            composed: true,
            detail: { signature: dataUrl }
        }));
    }

    @api
    checkValidity() {
        return this.captured;   // participate in the script's own validation
    }
}
```

```html
<!-- signatureCapture.html — no dependency on the surrounding runtime's internals -->
<template>
    <div class="slds-box slds-var-p-around_small">
        <canvas class="signature-pad" lwc:dom="manual"></canvas>
        <template lwc:if={captured}>
            <p class="slds-text-color_success">Signature captured.</p>
        </template>
        <lightning-button label="Clear" onclick={handleClear}></lightning-button>
    </div>
</template>
```

**Why it works:** the component now communicates the way the framework expects, which means it
also participates in the script's validation and navigation instead of working around them.
Rebuilding rather than porting was faster in this case precisely because the old component's
design depended on a runtime that is gone.

**Why this drove the estimate:** from inside the designer an embedded component looks like a
configuration item, which is why migrations get sized by script count. Each one is a build, a
QA pass and a risk of subtly different behaviour. Counting them — not counting scripts — is
what makes the estimate survive contact with the work.

**Finishing the job:** once the script renders on the new runtime, the Visualforce page and
the Angular-era component it replaced stop being exercised and stop being noticed. Removing
them belongs inside the migration, with a check that nothing still references them. Retiring
them while the team remembers what they did costs a fraction of identifying them in two years
from a filename.
