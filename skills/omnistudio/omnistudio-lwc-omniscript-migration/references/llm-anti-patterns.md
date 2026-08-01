# LLM Anti-Patterns — OmniStudio LWC OmniScript Migration

Scope: moving OmniScripts off the AngularJS-based runtime onto the OmniScript Lightning Web
Component framework, and the runtime setting that governs which one is used. Designing a new
OmniScript belongs elsewhere; this file covers the migration and — deliberately — where its
factual claims run out.

**Grounding rule for this skill, stated first because it is the highest risk here.** Release
and deprecation facts move faster than any model's training data, and a confident wrong date
in a migration plan is expensive. This file states only what current documentation says and
names what it does not. Anything about a specific release, a cutoff date or a support window
must be read from the current release notes, not recalled.

## Anti-Pattern 1: Presenting the AngularJS runtime as a choice that still exists

The documentation is unambiguous: **Omnistudio no longer supports Omniscripts built on
AngularJS**, and the stated remedy is to migrate all AngularJS-based OmniScripts to the
OmniScript Lightning Web Component framework. Assistants trained on older material present
this as a modernisation option with a trade-off, which produces plans that treat "stay on
Angular" as a valid branch.

❌ Frame the LWC framework as the faster option and Angular as the compatible one.
✅ Frame it as migration work with a known destination. The planning question is sequencing
and parity, not whether to go. Where a script cannot move yet, that is an exception to
document with an owner, not an architecture position.

Source: Lightning Web Component OmniScripts — https://help.salesforce.com/s/articleView?id=sf.os_lwc_omniscripts.htm&type=5

## Anti-Pattern 2: Inventing a deprecation date to make the plan look decisive

The most damaging thing a model does in this domain. A specific release number attached to a
cutoff reads as authoritative, gets copied into a programme plan, and is then defended in
meetings — long after anyone could have checked it. Release timing is exactly the class of
fact that ages badly between a model's training cut-off and the day it is asked.

❌ "This must be complete before the '26 release" stated without a citation.
✅ Sequence the work by risk and dependency, and treat the date as an input the team fetches
from the current release notes rather than one the plan asserts. If a date is needed for
funding, cite where it came from and when it was checked, so the claim can be re-verified
instead of inherited.

## Anti-Pattern 3: Treating the runtime as a per-script toggle

It is an org-level configuration, not a property of each script, and generated plans assume
per-script switching because that is what a safe migration would want. The relevant settings
are documented as **Disable the Managed Package Runtime** and **Deploy Custom Lightning Web
Components in Standard Runtime** — org-wide, affecting how FlexCards and OmniScripts are
deployed and rendered.

❌ Plan a migration whose rollback step is "switch this one script back".
✅ Establish what the setting actually controls in your org before designing the sequence,
and design a rollback at the level the setting operates at. A plan whose safety depends on a
granularity the platform does not offer is not a plan; it is an assumption that will be
discovered during the cutover.

Source: Disable the Managed Package Runtime and Deploy Custom Lightning Web Components — https://help.salesforce.com/s/articleView?id=xcloud.os_enable_standard_omnistudio_runtime.htm&type=5

## Anti-Pattern 4: Assuming embedded custom components survive the move

The parity gaps concentrate here. A script that embeds custom Visualforce, or a custom
component written against the Angular runtime, does not carry across — the replacement is a
Lightning Web Component added to the OmniScript through the documented custom-LWC path. This
is real development work, and it is systematically underestimated because from the designer
the element looks like a configuration item.

❌ Inventory OmniScripts and size the migration from that count.
✅ Inventory the **embedded custom components**, because they are what determines the effort.
Find them before estimating — an element that embeds a component looks like configuration
from inside the designer, which is exactly why it gets counted as one:

```bash
#!/usr/bin/env bash
# Which OmniScripts embed a custom component, and which component. This — not the
# script count — is the estimate. Each hit is a build, a QA pass and a behavioural risk.
set -euo pipefail

grep -rlE '"(lwcName|customLwcName|vlocityLwcName)"' force-app --include='*.json' \
  | while IFS= read -r f; do
      printf '%s\t' "$f"
      grep -oE '"(lwcName|customLwcName|vlocityLwcName)"[[:space:]]*:[[:space:]]*"[^"]+"' "$f" \
        | sort -u | tr '\n' ' '
      echo
    done
```

The replacement path is documented — create the LWC, then add it to the OmniScript — and each
one carries its own build, its own QA and its own risk of behaving differently:

```javascript
// A custom LWC used inside an OmniScript receives the script's data through public
// properties and communicates back by dispatching events, rather than by reaching into
// a shared runtime the way an Angular-era component could.
import { LightningElement, api } from 'lwc';

export default class SignatureCapture extends LightningElement {
    @api omniJsonData;          // data from the OmniScript
    @api omniJsonDef;           // this element's definition

    handleCaptured(dataUrl) {
        this.dispatchEvent(new CustomEvent('omniapply', {
            bubbles: true,
            composed: true,
            detail: { signature: dataUrl }
        }));
    }
}
```

Verify the exact contract — property names and event names — against the current
custom-LWC documentation for your runtime before building. It is documented, and it is not
worth reciting from memory.

Source: Create a Custom Lightning Web Component for Omniscript — https://help.salesforce.com/s/articleView?id=sf.os_create_a_custom_lightning_web_component_for_omniscript_17512.htm&type=5

## Anti-Pattern 5: Quoting a performance improvement figure

"30–60% faster" and similar numbers circulate widely and are attributable to nobody. They end
up in business cases, where they set an expectation the migration is then measured against —
and a migration that delivers correctness but not a specific percentage is recorded as having
underdelivered.

❌ Justify the work with an invented percentage.
✅ Justify it on supportability: the AngularJS runtime is no longer supported, which is a
sufficient reason on its own and does not decay. If a performance claim is wanted, measure
the org's own scripts before and after — the result will be specific to the scripts, and it
will be true.

## Anti-Pattern 6: Sizing the QA by counting scripts rather than by counting paths

A migration plan that says "80 OmniScripts, ten per week" is measuring the wrong unit. What
has to be tested is the paths through each script — branches, validation, conditional
visibility, every embedded component — and those are distributed very unevenly. A handful of
scripts carry most of the risk, and a per-script schedule spreads attention evenly across a
distribution that is not.

❌ Schedule uniformly by script count.
✅ Rank by embedded custom components, branch count and business criticality, then take the
riskiest first while there is the most time to react. Include the parts of the experience
that are not functional: styling and layout differ between runtimes, so a visual comparison
belongs in the plan rather than in the bug backlog after go-live.

## Anti-Pattern 7: Leaving the superseded assets in place

Once the scripts render on the new runtime, the old Visualforce pages, the Angular-era
components and the wrapper pages that hosted them stop being exercised — and stop being
noticed. They remain in the org as metadata that every future audit has to classify and every
future migration has to consider.

❌ Declare the migration complete when the scripts work.
✅ Make removal of the superseded assets part of the migration, with its own verification
that nothing still references them. Retiring them while the team still remembers what they
were for costs a fraction of what it costs to identify them in two years, when the only
evidence of their purpose is a filename.
