# Well-Architected Notes - Flow Testing

## Relevant Pillars

### Reliability

Reliable automation has repeatable evidence behind it. Flow tests, boundary tests, and intentional fault-path coverage reduce release risk and make changes safer.

## Architectural Tradeoffs

- **Fast debug validation vs durable regression assets:** debug is fast, while repeatable tests have far more long-term value.
- **Flow-only testing vs layered testing:** one layer is cheaper short term, but complex automations often need tests at more than one boundary.
- **Happy-path confidence vs broader path coverage:** wider coverage costs time now but avoids operational surprises later.

## Anti-Patterns

1. **Debug session treated as final proof** - no repeatable coverage exists after the investigation ends.
2. **No negative or fault-path cases** - the most operationally significant behavior remains unproven.
3. **Boundary dependencies assumed correct without their own tests** - orchestration coverage leaves custom logic gaps.

## Official Sources Used

- Flow Testing Tool - https://help.salesforce.com/s/articleView?id=sf.flow_test.htm&type=5
- FlowTest Metadata Type - https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_flowtest.htm
- Flow Reference - https://help.salesforce.com/s/articleView?id=sf.flow_ref.htm&type=5
