# Well-Architected Mapping: Approval Processes

## Pillars Addressed

### Reliability

Approval design controls whether business-critical decisions route consistently.

- Tight entry criteria prevent accidental submissions.
- Explicit approver sourcing reduces runtime routing failures.

### User Experience

Submitters and approvers need a process that is understandable and predictable.

- Locking rules shape whether pending records feel safe or unusable.
- Clear email and status changes reduce approval confusion and support noise.

### Operational Excellence

Approval sprawl becomes an admin burden quickly.

- Reviewable step design and routing ownership keep approval logic maintainable.
- Standard-vs-custom decision discipline prevents fragile workflow bloat.

## Pillars Not Addressed

- **Security** - approval is about decision routing, not record access architecture.
- **Performance** - approval volume is usually an operational concern, not a compute-bound pattern.

## Official Sources Used

- Salesforce Well-Architected Overview — governance and reliability framing for approval design
- Metadata API Developer Guide — approval metadata packaging and deployment behavior
