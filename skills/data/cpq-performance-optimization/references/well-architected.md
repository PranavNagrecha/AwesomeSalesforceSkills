# Well-Architected Notes — CPQ Performance Optimization

## Relevant Pillars

- **Performance** — CPQ quote calculation performance is the dominant constraint in this skill. The synchronous QLE calculation engine has a practical ceiling of 200–300 quote lines before governor pressure produces timeouts. Large Quote Mode is the primary architectural lever; QCP field declaration discipline is the secondary lever. Both must be addressed together for reliable performance at scale.
- **Reliability** — Quote calculation failures (timeouts, governor errors) result in lost rep work and deal delays. Large Quote Mode trades synchronous immediacy for reliable server-side completion. The async job queue must be monitored — failed calculation jobs leave quotes in an indeterminate state.
- **Operational Excellence** — QCP field declarations drift over time as plugin logic evolves. Undeclared fields produce silent pricing errors that are difficult to diagnose in production. A disciplined code review and audit process for the declaration arrays is an operational requirement, not a one-time fix. Static Resource architecture for large plugins requires deployment coordination as an operational habit.
- **Security** — The QCP `eval()` pattern for loading Static Resources is an intentional CPQ architecture. It should not be treated as a security vulnerability in this context. However, the Static Resource must be protected from unauthorized modification — only authorized developers should be able to update the plugin resource in production.
- **Scalability** — The 131,072-character limit on `SBQQ__Code__c` is a hard platform constraint, not a soft guideline. Plugin design must account for long-term growth. Static Resource architecture enables horizontal scaling of plugin complexity without hitting field limits.

## Architectural Tradeoffs

**Synchronous vs Async Calculation:**
Synchronous calculation gives reps immediate feedback and a familiar save experience. It fails at scale. Async calculation (Large Quote Mode) is reliable at scale but changes the rep UX in ways that require change management. The decision point is the quote line count distribution: if P95 quote size is under 100 lines, synchronous is fine. If P50 is above 150 lines, Large Quote Mode is mandatory.

**Inline QCP vs Static Resource:**
Inline `SBQQ__Code__c` is simple to deploy (no separate resource management) and suitable for plugins under 80,000 characters. Static Resource architecture removes the size ceiling and enables standard tooling but adds deployment coordination. Orgs should migrate proactively when the inline file crosses 100,000 characters — doing it at 130,000 is a crisis migration.

**Global Threshold vs Account-Level Flag:**
The global Large Quote Mode threshold applies org-wide. The Account-level `SBQQ__LargeQuote__c` flag offers finer targeting. Using only the Account flag (leaving the global threshold high) scopes the UX change to known high-volume accounts, reducing the blast radius of the change management requirement.

## Anti-Patterns

1. **Enabling Large Quote Mode without user communication** — The async calculation UX is a breaking change for reps. Enabling in production without advance notice generates immediate support load and risks reps refreshing mid-calculation, losing line edits. This is the most frequently cited implementation failure mode for Large Quote Mode.

2. **Declaring all available fields in QCP "to be safe"** — Over-declaration inflates the JSON calculation payload. On quotes with 200+ lines, each extra declared field multiplies the payload overhead. The correct pattern is to declare only fields that the plugin explicitly reads or writes. Over-declaration also obscures the plugin's actual field dependencies, making future audits harder.

3. **Using Calculate Quote API as a governor limit bypass** — The API is not a high-performance alternative to the UI calculation path. It runs the same engine under the same constraints. Teams that route repricing through the API without enabling Large Quote Mode experience the same failures as the UI path, just in a batch context where the failure mode is harder to detect in real time.

## Official Sources Used

- Large Quote Performance Settings — https://help.salesforce.com/s/articleView?id=sf.cpq_large_quote.htm&type=5
- CPQ Quote Calculation Stages — https://help.salesforce.com/s/articleView?id=sf.cpq_calculation_stages.htm&type=5
- JavaScript Quote Calculator Plugin (QCP) — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_jsqcp_parent.htm
- Salesforce CPQ Developer Guide: Calculate Quote API — https://developer.salesforce.com/docs/atlas.en-us.cpq_dev_guide.meta/cpq_dev_guide/cpq_dev_quote_calculator.htm
- Salesforce Well-Architected Framework — https://architect.salesforce.com/well-architected/overview
