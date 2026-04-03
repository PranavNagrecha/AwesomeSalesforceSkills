# Well-Architected Notes — Process Automation Selection

## Relevant Pillars

- **Scalability** - the wrong automation surface becomes a limit problem under real volume.
- **Reliability** - clear boundaries reduce recursion, overlap, and unpredictable order-of-execution behavior.
- **Operational Excellence** - migration off legacy automation and clearer tool ownership reduce support cost.

## Architectural Tradeoffs

- **Declarative default vs code control:** Flow is easier to own, but Apex provides stronger control for complex or high-volume transaction behavior.
- **Single surface purity vs mixed boundary design:** keeping everything in one tool is simpler, but a deliberate Flow-plus-Apex split can be safer when responsibilities differ.
- **Legacy preservation vs migration:** preserving old automation lowers immediate effort, but increases long-term risk and confusion.

## Anti-Patterns

1. **Apex by reflex** - using code for simple same-record automation that Flow already handles better.
2. **Flow by ideology** - forcing complex transaction or service logic into declarative automation that cannot hold it cleanly.
3. **Legacy logic as architecture baseline** - keeping Workflow Rule or Process Builder as the model for new design.

## Official Sources Used

- Flow Reference - https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
- Flow Builder - https://help.salesforce.com/s/articleView?id=sf.flow.htm&type=5
- Apex Triggers - https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_triggers.htm
- Automate This! Migrate Workflow Rules and Processes to Flow - https://admin.salesforce.com/blog/2022/automate-this-migrate-workflow-rules-and-processes-to-flow
