# Examples — OmniStudio Multi-Language

## Example 1: Four languages, with the strings in the store the org already translates

**Context:** A retail onboarding OmniScript rolled out to an org with English, French, German
and Japanese enabled. Field labels and picklist values were already being translated through
the Translation Workbench.

**Problem:** The script's text was typed directly into the elements, so translators had
nothing to work with. The first plan was to export a per-script translation file, send it out
and re-import it — a workflow that exists in most frameworks and not in this one. OmniStudio's
documented mechanism is Salesforce custom labels, which meant the plan's first step did not
exist and the rest of it followed from a false premise.

**Solution:** A multi-language OmniScript whose text comes from custom labels, named so the
set is queryable and reusable.

```text
OS_<Domain>_<Component>_<Purpose>

OS_Onboarding_AddressStep_Heading        "Where should we send your order?"
OS_Onboarding_AddressStep_HelpText       "We'll only use this for delivery."
OS_Onboarding_Validation_PostcodeInvalid "Enter a valid postcode."
OS_Common_Action_Save                    "Save"
OS_Common_Action_Cancel                  "Cancel"
```

```json
{
  "creation_order_matters": [
    "1. Create the OmniScript as Multi-Language — this is chosen at creation, not switched on later.",
    "2. Create each custom label in ENGLISH first; the documentation calls this out explicitly.",
    "3. Add the translation for each other active language.",
    "4. Check the OmniScript custom label reference BEFORE creating anything — OmniStudio ships default labels, already translated, for its own standard UI text."
  ],
  "why_OS_Common_exists": "It is where the second developer looks before creating a duplicate, and it makes the shared set queryable when a wording change must be applied consistently.",
  "what_this_does_not_cover": [
    "Field labels and picklist values — Translation Workbench, see admin/multi-language-and-translation",
    "Text inside an embedded custom LWC — imported labels in that component, see lwc/lwc-internationalization",
    "FlexCard text — labels, not typed strings"
  ]
}
```

**Why it works:** the strings are now in the same store as the rest of the org's translatable
text, so translating the script is a translator task inside an existing process rather than a
developer task inside a deployment. It also means the labels are reusable — `OS_Common_Action_Save`
is translated once for every script that needs the word.

**Why the English-first rule is not a style preference:** the documented flow is to create the
English value first, then the translations. Skipping it is a category of problem that produces
a label which does not resolve properly, diagnosed as a translation bug rather than a creation
order bug.

**Why checking the reference first saves a language pass:** OmniStudio provides default custom
labels with translations for its own standard UI text. Duplicating one means translating into
four languages something that arrived translated, and then maintaining two values that drift.
It is also the explanation for the most confusing symptom in this area — one button already in
French next to one that is not.

---

## Example 2: The layout regression that reading the labels could not have caught

**Context:** The same script after all four languages were in place. Every label had a value
in every language.

**Problem:** In German the primary action button truncated its text, the step heading wrapped
to two lines and pushed the form below the fold, and one validation message overflowed its
container. None of this was visible from the translation review, because reviewing
translations means reading strings, and the defect is about how long those strings are once
rendered. It surfaced from a customer complaint.

**Solution:** Make the layout tolerate length variance, and test by rendering rather than by
reading.

```css
/* Do not size controls to the English string. Give text room to grow and wrap. */
.action-bar {
    display: flex;
    flex-wrap: wrap;               /* buttons move to a second row before they truncate */
    gap: var(--lwc-spacingXSmall, 0.5rem);
}

.action-bar lightning-button {
    flex: 0 1 auto;
    min-width: 8rem;               /* room beyond the English width */
}

.step-heading {
    /* Reserve for two lines so a longer language does not reflow everything below it. */
    min-height: 3.25rem;
    overflow-wrap: break-word;
}

.validation-message {
    /* Logical properties so the platform's direction handling works in an RTL language. */
    margin-inline-start: var(--lwc-spacingXSmall, 0.5rem);
    overflow-wrap: break-word;
}
```

```json
{
  "qa_unit": "language, not label",
  "per_language_pass": [
    "Render the script end to end as a user set to that language.",
    "Check every action control for truncation.",
    "Check headings and validation messages for wrap and overflow.",
    "Confirm NO English remains on the rendered screen."
  ],
  "rtl_pass": "One right-to-left language, separately. Direction affects layout and directional icons in ways no left-to-right pass reveals.",
  "why_no_english_is_the_assertion": "Every failure here falls back to English silently — an untranslated label, a language not enabled, a hard-coded string. There is no error state, so surviving English is the only signal available."
}
```

**Why it works:** the layout no longer encodes an assumption about string length, and the test
exercises the thing that actually breaks. `min-width` plus `flex-wrap` means a longer label
moves a button to a second row rather than cutting its text; reserving two lines for the
heading stops a wrap from reflowing everything beneath it.

**Why the QA is budgeted by language:** the effort scales with the number of languages, not
the number of labels — each language is one full pass through the script by someone who can
tell a translation from the original. Planning it as "check the labels have values" is what
produces the customer complaint.

**Why "no English remains" is the assertion of last resort:** if a native reviewer is not
available for every language, this still catches both real defects. An English string on a
Japanese screen is either a label with no translation or a string that was typed in rather
than labelled — and both need the same fix.

**Logical properties, not left and right:** `margin-inline-start` rather than `margin-left`
means the platform's direction handling does the work in a right-to-left language. This is the
same discipline as the plain-LWC case in `lwc/lwc-internationalization`; the difference here is
only that more of the surface is configured rather than coded.
