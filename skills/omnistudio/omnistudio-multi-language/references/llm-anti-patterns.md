# LLM Anti-Patterns — OmniStudio Multi-Language

Scope: making an OmniScript render in the user's language. Platform translation as a whole —
enabling languages, running the Translation Workbench, translating field labels and picklist
values — belongs to `admin/multi-language-and-translation`, and the component-side equivalent
for plain LWC belongs to `lwc/lwc-internationalization`. This file covers only what is
specific to OmniStudio.

## Anti-Pattern 1: Inventing a per-script translation file

The single most common wrong answer here, and it sounds right because every other framework
works that way. Assistants describe exporting a "language data JSON" per script, sending it to
translators and re-importing it. The documented mechanism is **Salesforce custom labels**: an
OmniScript is created as multi-language, its text comes from custom labels, and the labels are
translated through the same platform machinery as everything else.

❌ Build a workflow around exporting and re-importing a per-script translation artefact.
✅ Use custom labels, which means the OmniScript's strings live in the same store as the rest
of the org's translatable text and go through the same review process. The concrete steps the
documentation describes are: choose Multi-Language when creating the OmniScript, create each
custom label in **English first**, then add translations for the other languages. Creating the
English value first is called out explicitly — it is what makes the label resolve properly.

Source: Define Custom Label Translations in Multi-Language Omniscripts — https://help.salesforce.com/s/articleView?id=sf.os_define_custom_label_translations_in_multi_language_omniscripts.htm&type=5

## Anti-Pattern 2: Retrofitting multi-language onto a single-language script

Multi-language is a property chosen when the OmniScript is created — the documented flow is to
remove English from the language dropdown and select Multi-Language at that point. Assistants
describe adding translation to an existing script as if it were a setting to switch on later,
which produces a plan whose first step does not exist.

❌ "Enable multi-language on the existing script and import translations."
✅ Establish how the script was created before planning the work. If it was not created as
multi-language, the work includes producing a multi-language script and moving the
configuration across — which is a materially different estimate from "extract the strings",
and finding that out during the sprint rather than during planning is the avoidable cost.

Source: Create Multi-Language Omniscripts — https://help.salesforce.com/s/articleView?id=xcloud.os_create_multi_language_omniscripts_20695.htm&type=5

## Anti-Pattern 3: Recreating labels OmniStudio already ships

OmniStudio provides default custom labels with translations for its own standard UI text —
navigation, standard validation messaging and similar. Teams that do not know this create
their own duplicates, then translate into every language something that already arrived
translated, and end up with two labels whose values drift.

❌ Create `MyOrg_Next_Button` and translate it into six languages.
✅ Check the OmniScript custom label reference for an existing default before creating one.
Create labels for your own domain text; inherit the framework's. This is also the answer to
"why is one button already in French and the one next to it is not" — the framework's label
was translated and the custom one was not.

Source: Omniscript Custom Label Reference — https://help.salesforce.com/s/articleView?id=xcloud.os_omniscript_custom_label_reference.htm&type=5

## Anti-Pattern 4: Naming labels so that nobody can find or reuse them

Custom labels are a flat, org-wide namespace shared by every developer, and OmniStudio work
generates a lot of them. Without a convention the same string gets created three times under
three names, translated three times, and drifts — and the duplicates are undetectable because
nothing groups them. The documentation calls out naming conventions explicitly, to avoid
duplication and to make querying possible.

❌ `Label1`, `SaveBtn`, `omni_save_button` for the same word, created by three people.
✅ A convention with enough structure to query, applied before the labels exist rather than
after:

```text
OS_<Domain>_<Component>_<Purpose>
OS_Onboarding_AddressStep_Heading
OS_Onboarding_AddressStep_HelpText
OS_Common_Action_Save
```

The `OS_Common_` prefix is the part that pays for itself: it is where the second person looks
before creating a duplicate, and it makes the shared set queryable as a group when a wording
change has to be applied consistently.

## Anti-Pattern 5: Translating only the OmniScript

An OmniScript is one surface among several. FlexCard text, data mapper output that includes
labels, custom LWCs embedded in the script, and the underlying field labels and picklist
values are all separately translatable — and a user's experience is the union of them. A
script that is fully translated inside a page whose field labels are not produces a screen
that is half in each language, which reads worse than untranslated.

❌ Declare the work done when the OmniScript renders in the target language.
✅ Enumerate every surface on the screen and confirm each has a translation path: script text
via custom labels, embedded custom LWC text via labels imported in the component, field labels
and picklist values via the Translation Workbench. The embedded-component half is ordinary
LWC label importing, and it is the one that gets forgotten because it lives in a different
repository folder from the script:

```javascript
// A custom LWC embedded in an OmniScript translates its own text. The script's
// multi-language configuration does not reach inside the component.
import { LightningElement, api } from 'lwc';
import HELP_TEXT from '@salesforce/label/c.OS_Onboarding_AddressStep_HelpText';
import ERROR_POSTCODE from '@salesforce/label/c.OS_Onboarding_Validation_PostcodeInvalid';

export default class AddressLookup extends LightningElement {
    @api omniJsonData;

    label = {
        help: HELP_TEXT,
        postcodeInvalid: ERROR_POSTCODE
    };
}
```

The Translation Workbench half belongs to `admin/multi-language-and-translation` —
cross-reference it rather than reimplementing it, but do not omit it from the plan.

## Anti-Pattern 6: Testing translation by reading the label values

The failure everyone hits and few plan for: translated strings are longer. Reading a
translation file tells you nothing about whether the layout survives it. Buttons truncate,
headings wrap into two lines and push content below the fold, and validation messages overflow
their containers — none of which is visible until the script is rendered in that language.

❌ Verify by checking that each label has a value in each language.
✅ Load the script as a user in each target language and look at it. Budget the QA by
language, not by label — this is where the time actually goes. Right-to-left languages need
their own pass, because direction affects layout and directional icons in ways no
left-to-right test can reveal.

## Anti-Pattern 7: Silent fallback treated as a passing test

Every failure mode in this system falls back to English without an error. A label with no
translation renders English; a language not enabled in the org renders English; a hard-coded
string in a FlexCard renders English forever. So a screen that looks correct in English is
evidence of nothing at all.

❌ Read "no errors" as "translated".
✅ Test in the target language, by a person who can tell a translation from the original.
Where that is not available, at minimum confirm that no English remains on the rendered screen
— any English string surviving in a Japanese session is either an untranslated label or a
hard-coded one, and both need fixing. There is no error state to alert on, so the rendered
screen is the only signal.
