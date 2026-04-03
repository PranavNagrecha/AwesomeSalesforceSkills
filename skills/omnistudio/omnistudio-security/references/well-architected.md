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
