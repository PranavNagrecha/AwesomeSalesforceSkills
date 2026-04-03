# Well-Architected Notes - Screen Flows

## Relevant Pillars

### User Experience

Screen flows are directly felt by end users. Clear sequencing, understandable validation, and thoughtful commit timing are the core UX design concerns.

### Reliability

Reliability in screen flows comes from predictable state transitions. Users should know when data is being saved and how errors or navigation affect the interview.

## Architectural Tradeoffs

- **Standard components vs custom runtime UX:** standard screens are easier to support, while custom components justify themselves only for real interaction gaps.
- **Few dense screens vs many narrow screens:** compact screens reduce navigation, but overloaded screens can become hard to complete accurately.
- **Early save vs delayed confirmation:** earlier save points can simplify downstream logic, but they make user navigation and cancellation less intuitive.

## Anti-Patterns

1. **DML before natural confirmation** - users lose confidence in Back or Cancel behavior.
2. **Custom component without validation contract** - Flow runtime and component UX drift apart.
3. **Screen count used to hide complexity** - the process is still complex, only stretched across more pages.

## Official Sources Used

- Screen Element - https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen.htm&type=5
- Screen Components - https://help.salesforce.com/s/articleView?id=sf.flow_ref_elements_screen_fields.htm&type=5
- Validate User Input for Custom Flow Screen Components - https://developer.salesforce.com/docs/platform/lwc/guide/use-flow-validate-external-internal-methods.html
