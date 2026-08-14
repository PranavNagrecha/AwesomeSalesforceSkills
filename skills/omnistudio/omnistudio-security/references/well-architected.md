# Well-Architected Notes — OmniStudio Security

## Relevant Pillars

- **Security** - this skill exists to reduce data exposure and unsafe extension patterns in OmniStudio.
- **Reliability** - secure boundaries also improve predictable behavior and safer error handling.
- **Operational Excellence** - narrow contracts and explicit ownership make audits and reviews easier.

## Architectural Tradeoffs

- **Reusable broad asset chain vs narrow external contract:** broad reuse saves time, but increases exposure risk in portal and guest scenarios.
- **Declarative convenience vs explicit server review:** OmniStudio moves quickly, but Apex and HTTP actions still need the same security rigor as code-first services.
- **Rich diagnostic output vs least-data response:** diagnostics help support, but should not bleed into user-facing payloads.

## Anti-Patterns

1. **OmniStudio assumed secure by default** - declarative assets still need data-contract review.
2. **Internal asset reused unchanged for external users** - user context risk changes the acceptable design.
3. **Custom Apex hidden behind OmniStudio with weak enforcement** - the riskiest part of the chain often sits off-canvas.

## Official Sources Used

- OmniStudio Developer Guide - https://developer.salesforce.com/docs/atlas.en-us.omnistudio_developer_guide.meta/omnistudio_developer_guide/omnistudio_intro.htm
- Secure Apex Classes - https://developer.salesforce.com/docs/platform/lwc/guide/apex-security
- Salesforce Security Guide - https://help.salesforce.com/s/articleView?id=sf.security_overview.htm&type=5
- Disable the Managed Package Runtime and Deploy Custom Lightning Web Components - https://help.salesforce.com/s/articleView?id=sf.os_enable_standard_omnistudio_runtime.htm&language=en_US&type=5 - confirms the standard-runtime FLS prerequisite on Omni Process Compilation (Read, Edit), Omni Data Transformation (Read) and Omniscript Saved Sessions (Read, Edit), and that the runtime switch is one-way (verified 2026-08-13)
- Security for Omnistudio Data Mappers and Integration Procedures - https://help.salesforce.com/s/articleView?id=xcloud.os_security_for_dataraptors_and_integration_procedures_56519.htm&language=en_US&type=5 - confirms the real FLS enforcement controls: "Check Field Level Security" on the Data Mapper Options tab and EnforceDMFLSAndDataEncryption in Omni Interaction Configuration (verified 2026-08-13)
- OmniInteractionConfig (Industries Metadata API Developer Guide) - https://developer.salesforce.com/docs/atlas.en-us.industries_reference.meta/industries_reference/meta_omniinteractionconfig.htm - enumerates the Omni Interaction Configuration settings and carries the notice that "During the week of February 2, 2026, Salesforce enables the AdvancedOmnistudioAccessCheck, ApexClassCheckForIP, ApexClassCheck, EnforceDMFLSAndDataEncryption, and EnableQueryWithFLS settings by default to enhance org security" (verified 2026-08-14)
