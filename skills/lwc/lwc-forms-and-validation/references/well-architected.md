# Well-Architected Notes - LWC Forms And Validation

## Relevant Pillars

### User Experience

Forms are where Salesforce users feel friction immediately. Correct labels, predictable validation timing, and understandable save behavior reduce abandonment and support noise.

### Reliability

Reliable forms separate browser checks from server-enforced rules and keep save sequencing deterministic. A fragile submit path creates duplicate records, silent failures, or inconsistent field state.

## Architectural Tradeoffs

- **Supported LDS forms vs custom UI freedom:** record-edit-form gives a safer default, while custom forms justify themselves only when the UX cannot fit the supported model.
- **Immediate client validation vs minimal interruption:** fast feedback is valuable, but too many premature errors create noisy forms.
- **One-click everything vs staged save and upload:** combining record save and file handling feels simpler at first, but staged flows are usually easier to reason about.

## Anti-Patterns

1. **Manual forms for standard CRUD only** - the team gives up built-in behavior without a real UX reason.
2. **Custom messages without validity reporting** - the validation logic exists in code but never appears to the user.
3. **Mixed form ownership models** - record-edit and manual inputs compete for control of one save path.

## Official Sources Used

- Data Edit Record - https://developer.salesforce.com/docs/platform/lwc/guide/data-edit-record.html
- lightning-record-edit-form - https://developer.salesforce.com/docs/platform/lightning-component-reference/guide/lightning-record-edit-form.html
- Best Practices for Development with Lightning Web Components - https://developer.salesforce.com/docs/platform/lwc/guide/get-started-best-practices.html
