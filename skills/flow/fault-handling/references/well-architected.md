# Flow Fault Handling — Well-Architected Mapping

## Reliability

- Fault connectors prevent silent or generic failures from reaching production unchanged.
- Logging and deliberate error routing make failed interviews diagnosable.
- User-safe and support-safe error paths reduce repeat failures during live operations.

## Scalability

- Bulk review of record-triggered paths reduces load-time rollback surprises.
- Explicit review of repeated reads and related-record fan-out keeps flow designs safer under volume.

## Operational Excellence

- Consistent error logging and notification create supportable automation.
- Review checklists turn Flow failure handling into a repeatable release discipline.

## Pillars Not Addressed

- **Security** - this skill focuses on failure behavior and observability, not access design.
- **User Experience** - UX matters for screen flows, but the main goal is predictable automation failure handling.

## Official Sources Used

- Salesforce Well-Architected Overview — reliability and operational-quality framing for automation design
- Metadata API Developer Guide — Flow metadata and deployment semantics used to keep the guidance grounded in platform configuration behavior
- Integration Patterns — error-handling tradeoffs when Flow interacts with external systems or async boundaries
