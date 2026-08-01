# Well-Architected Notes — OmniStudio Multi-Language

**Operational separation:** the value of routing OmniScript text through Salesforce custom
labels is that translation stops being a developer activity. The strings land in the same
store the org already translates, reviewed by the same people through the same process, and a
wording change in one language stops requiring a deployment. The alternative that generated
guidance keeps proposing — a per-script translation artefact exported and re-imported — is not
the documented mechanism here, and designing around it produces a plan whose first step does
not exist.

**Design-time decisions:** multi-language is chosen when the OmniScript is created, and the
English value of each label is created before its translations. Both are ordering constraints
rather than preferences, and both are cheap at the start and expensive to retrofit. The
practical consequence for planning is that "add translation to the existing script" and
"create a multi-language script" are materially different estimates, and which one applies has
to be established before the work is sized.

**Reuse:** custom labels are a flat, org-wide namespace and OmniStudio work generates a lot of
them. Without a convention applied before the labels exist, the same string is created several
times under several names, translated several times, and drifts apart with nothing grouping
the duplicates. A shared prefix for common text is what makes the set queryable and gives the
next developer somewhere to look before creating another one — and checking OmniStudio's own
default labels first avoids translating text that already arrived translated.

**User Experience, the whole screen:** a user's experience is the union of every surface in
front of them — script text, FlexCard text, embedded custom components, field labels, picklist
values. Each has its own translation path, and a script translated inside a page whose field
labels are not reads worse than one left alone. The enumeration belongs in the plan even
though most of it is owned elsewhere.

**User Experience, length is the defect:** translated strings are longer, and layout is where
that lands — truncated actions, headings that wrap and push content below the fold, messages
that overflow. Reviewing translations means reading strings, which cannot reveal any of it.
Layout that does not encode an assumption about English string length, plus a rendered pass per
language and a separate right-to-left pass, is the only thing that catches it before a user
does.

**Everything fails quietly:** an untranslated label falls back to English, a language that is
not enabled falls back to English, a string typed into an element instead of labelled stays
English permanently. There is no error state anywhere in this system, so the absence of errors
carries no information and the rendered screen in the target language is the only available
signal. Where a native reviewer is not available, "no English remains on this screen" catches
both real defects with one check.

## Official Sources Used

- Define Custom Label Translations in Multi-Language Omniscripts — the custom-label mechanism and the create-English-first rule — https://help.salesforce.com/s/articleView?id=sf.os_define_custom_label_translations_in_multi_language_omniscripts.htm&type=5
- Create Multi-Language Omniscripts — multi-language as a creation-time choice — https://help.salesforce.com/s/articleView?id=xcloud.os_create_multi_language_omniscripts_20695.htm&type=5
- Enable Multi-Language Omniscript Support — the org-level prerequisite — https://help.salesforce.com/s/articleView?id=sf.os_enable_multi_language_omniscript_support_20725.htm&type=5
- Omniscript Custom Label Reference — the default labels OmniStudio ships already translated — https://help.salesforce.com/s/articleView?id=xcloud.os_omniscript_custom_label_reference.htm&type=5
- Access Custom Labels in an Omniscript Custom Lightning Web Component — translating text inside an embedded component — https://help.salesforce.com/s/articleView?id=xcloud.os_access_custom_labels_in_an_omniscript_custom_lightning_web_component_20854.htm&type=5
- Custom Labels — the org-wide store these strings live in, its 5,000-label and 1,000-character ceilings — https://help.salesforce.com/s/articleView?id=platform.cl_about.htm&type=5
