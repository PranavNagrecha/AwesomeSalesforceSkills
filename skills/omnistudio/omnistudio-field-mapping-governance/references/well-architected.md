# Well-Architected Notes — OmniStudio Field Mapping Governance

**Reliability:** the governing fact is that a broken mapping is quiet. A missing source field
produces an absent node rather than an exception, so the consuming OmniScript renders a blank
and the defect is discovered by a user noticing a wrong total. Every control in this area
exists because the platform's own signal for this failure is nothing at all — which means
the absence of errors cannot be treated as evidence, and the checks have to run at build
time, where something is still watching.

**Reliability, dependency visibility:** field references inside a data mapper are strings
naming an object and a field, not the kind of relationship an impact analysis in Setup
enumerates. A clean "what uses this field" answer is truthful about what it tracks and silent
about OmniStudio. Maintaining that inventory yourself is not defensive over-engineering; it is
the only place the information exists.

**Operational Excellence, both directions:** the forward index — mapper to fields — tells you
what a schema change breaks. The reverse index — mapper to callers — tells you what a mapper
change breaks and which mappers are pure maintenance cost. Neither can be derived from the
other, and a cleanup driven by only one of them deletes components whose callers live in Apex
or a custom LWC rather than in an OmniScript.

**Operational Excellence, naming as a one-way door:** because callers hold a mapper's name as
a string, a rename saves cleanly and updates nothing downstream. That makes rename a staged
migration rather than an edit, and it makes a naming standard most valuable applied to new
components — a retrospective rename campaign costs more than the inconsistency it removes,
and it fails against exactly the callers nobody enumerated.

**Performance, with its trade stated:** Turbo Extract is faster and simpler because it does
less — a single object plus related-object fields, with no formulas, custom JSON, default
values or transformations. Adopting it on speed alone tends to push the missing transformation
into an Integration Procedure or a component, where this governance process cannot see it.
Mapping logic concentrated in one governable place is worth more than the runtime difference
in most cases; split mapping is the outcome that makes an audit unable to answer its own
question.

## Official Sources Used

- Omnistudio Data Mappers — the current component name and the Extract / Turbo Extract / Transform / Load types — https://help.salesforce.com/s/articleView?id=xcloud.os_omnistudio_dataraptors_45587.htm&type=5
- Omnistudio Data Mapper Turbo Extract Overview — single-object scope and the exclusion of formulas, custom JSON, default values and transformations — https://help.salesforce.com/s/articleView?id=xcloud.os_dataraptor_turbo_extract_overview.htm&type=5
- Omnistudio Data Mapper Extract Overview — the capabilities Turbo Extract trades away — https://help.salesforce.com/s/articleView?id=sf.os_dataraptor_extract_overview.htm&type=5
- Related Object Fields in Omnistudio Data Mapper Turbo Extracts — the relationship paths that a schema change can invalidate — https://help.salesforce.com/s/articleView?id=sf.os_related_object_fields_in_dataraptor_turbo_extracts.htm&type=5
- Omnistudio Data Mapper Transform Data Mappings — where transformation logic belongs when it cannot live in a Turbo Extract — https://help.salesforce.com/s/articleView?id=sf.os_dataraptor_transform_data_mappings.htm&type=5
