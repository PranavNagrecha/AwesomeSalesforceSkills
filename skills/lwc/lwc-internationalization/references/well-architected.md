# Well-Architected Notes — LWC Internationalization

**User Experience:** the goal is not that the component is translated but that it agrees
with everything else the user sees. A date formatted from `navigator.language` and a date
in a report come from different settings and will disagree for any user whose browser and
Salesforce locale differ — which is most users in a multinational org. Reading the
platform's locale, or better, letting a base component read it, keeps one component from
being the only surface in the org that disagrees about what "03/04" means.

**Operational separation:** custom labels put translation in the hands of translators
rather than deployments. A JavaScript dictionary keyed by language works on day one and
then requires a release for every wording change in every language, which is how orgs end
up with stale translations they cannot afford to fix. Labels are the only string store the
Translation Workbench covers, and their real ceiling — 1,000 characters, 5,000 labels per
org — is high enough that reaching for a different store is almost always premature.

**Design constraint, not a limitation:** label imports resolve when the component is
compiled, so the set of translatable strings is fixed at build time. That is what makes it
possible to ship each user only their language. Attempting to defeat it with runtime name
construction does not produce a dynamic translation system; it produces a component with no
translations at all, and no error to say so.

**Silent failure everywhere:** an untranslated label falls back to English, an unenabled
language falls back to English, a missing translation import falls back to English. Nothing
in this system fails loudly, so "it looks fine" is not evidence. The only reliable check is
loading the component as a user whose language is one of the target languages — including
one right-to-left language, where a class of defect exists that no amount of code review
finds.

## Official Sources Used

- Access Labels in a Component — the `@salesforce/label` scoped module and the `namespace.labelName` reference format — https://developer.salesforce.com/docs/platform/lwc/guide/create-labels.html
- Internationalization — `@salesforce/i18n/locale`, and the recommendation to use base components that adapt to the user's language, locale and time zone — https://developer.salesforce.com/docs/platform/lwc/guide/create-i18n.html
- @salesforce Modules reference — the `@salesforce/i18n` identifiers including `lang` and `dir` — https://developer.salesforce.com/docs/platform/lwc/guide/reference-salesforce-modules.html
- Custom Labels — up to 5,000 labels per org, up to 1,000 characters each, managed-package labels excluded from the count — https://help.salesforce.com/s/articleView?id=platform.cl_about.htm&type=5
- lightning-formatted-number component reference — `format-style` and `currency-code` — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-formatted-number
