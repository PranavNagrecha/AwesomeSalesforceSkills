# Well-Architected Notes — OmniStudio LWC OmniScript Migration

**Grounding, stated first because it is the dominant risk in this skill:** release timing and
deprecation windows are the facts most likely to be stale in any recalled answer, and a
confident wrong date propagates into a programme plan where it is defended rather than
re-checked. The durable claim is the supportability one — Omnistudio no longer supports
OmniScripts built on AngularJS, and the documented remedy is migration to the OmniScript
Lightning Web Component framework. Everything about *when* comes from the current release
notes, fetched rather than remembered.

**Operational Excellence:** the migration's cost is concentrated in embedded custom
components, not in the number of scripts. From inside the designer an embedded component looks
like a configuration item, which is why plans get sized by script count and then overrun. Each
one is a rebuild against a different contract — data in through public properties, results out
through events — with its own build, QA and behavioural risk. Counting components rather than
scripts is what makes an estimate survive.

**Operational Excellence, rollback at the granularity the platform offers:** the runtime is
governed by org-level settings rather than a per-script switch. A plan whose safety depends on
reverting one script has assumed a granularity that does not exist, and the assumption
surfaces during the cutover. Establish what the setting controls before the sequence is
designed, not after.

**Reliability:** sequence by risk — embedded components, branch count, business criticality —
so the irreducible work happens while there is the most time to react. A uniform per-script
schedule spreads attention evenly across a distribution that is heavily skewed, and reliably
places some of the hardest work in the final week.

**User Experience:** styling and layout differ between runtimes, so parity is not only
functional. A visual comparison of high-traffic screens is cheap to schedule inside the
migration and expensive to discover afterwards, when it arrives as a stream of individually
small defects that collectively read as a regression.

**Sustainability:** the migration is not finished when the scripts render. The superseded
Visualforce pages and Angular-era components remain in the org, unexercised and unnoticed,
where every future audit has to classify them and every future migration has to consider
them. Removing them while the team still remembers their purpose is a fraction of the cost of
identifying them later from a filename.

**Avoided deliberately:** no performance percentage appears in these notes. The circulating
figures are attributable to nobody, and quoting one sets an expectation the migration is then
measured against. Supportability is a sufficient justification and does not decay; if a number
is required, measure the org's own scripts before and after.

## Official Sources Used

- Lightning Web Component OmniScripts — the LWC runtime and the statement that OmniScripts built on AngularJS are no longer supported — https://help.salesforce.com/s/articleView?id=sf.os_lwc_omniscripts.htm&type=5
- Disable the Managed Package Runtime and Deploy Custom Lightning Web Components — the org-level runtime settings — https://help.salesforce.com/s/articleView?id=xcloud.os_enable_standard_omnistudio_runtime.htm&type=5
- Create a Custom Lightning Web Component for Omniscript — the contract a replacement component must satisfy — https://help.salesforce.com/s/articleView?id=sf.os_create_a_custom_lightning_web_component_for_omniscript_17512.htm&type=5
- Add Custom Lightning Web Components to an Omniscript — wiring the rebuilt component into the script — https://help.salesforce.com/s/articleView?id=sf.os_add_custom_lightning_web_components_to_an_omniscript.htm&type=5
- Omnistudio Lightning Web Components — the component set the migrated scripts render with — https://help.salesforce.com/s/articleView?id=sf.os_omnistudio_lightning_web_components_58153.htm&type=5
- lightning-omnistudio-omniscript — the wrapper for surfacing an OmniScript in Lightning App Builder and Experience Builder — https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-omnistudio-omniscript.html
- Omnistudio release notes — the only acceptable source for release timing and deprecation dates; check the current release rather than recalling one — https://help.salesforce.com/s/articleView?id=release-notes.rn_omnistudio.htm&type=5
