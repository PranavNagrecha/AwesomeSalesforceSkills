# Well-Architected Mapping: Sharing and Visibility

## Pillars Addressed

### Security

Record-level access is a core Salesforce security boundary.

- Restrictive OWD plus explicit sharing reduces accidental overexposure.
- Auditing bypass permissions prevents security models from being undermined silently.

### Reliability

Sharing design depends on ownership, hierarchy, and group structure.

- Clean ownership models make sharing predictable.
- Public groups and rule design encode real collaboration patterns into the data model.

### Operational Excellence

A sharing model that requires constant manual rescue does not scale.

- Access debugging becomes faster when the model is layered and documented.
- Reducing exception-based sharing lowers admin support load.

## Pillars Not Addressed

- **Performance** - this skill flags recalculation risk, but it is not a query-optimization guide.
- **User Experience** - page visibility issues are adjacent, not the main focus here.

## Official Sources Used

- Salesforce Well-Architected Overview — record-access and governance framing
- Object Reference — relationship semantics that affect access design reasoning
- Metadata API Developer Guide — sharing-related metadata deployment context
