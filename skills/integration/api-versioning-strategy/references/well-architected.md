# Well-Architected Notes — API Versioning Strategy

**Reliability:** Apex REST is served from `/services/apexrest/` plus your own
`urlMapping`, and the platform contributes no version segment. Versioning is therefore
something you build, not something you inherit — and the cheapest moment to build it is
before the first consumer connects. Because `urlMapping` must be unique across the org,
two versions coexist as independent routes with no dispatcher to maintain.

**Operational Excellence:** a sunset date creates urgency; only per-caller instrumentation
creates safety. Retire in two steps — `410 Gone` with a successor link on the announced
date, deletion only after the log shows zero distinct callers across a window longer than
the slowest consumer's cadence.

## Official Sources Used

- Apex REST — @RestResource, urlMapping uniqueness, and the /services/apexrest/ base URI — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest_intro.htm
- Apex REST annotations — @HttpGet, @HttpPost, @HttpPatch, @HttpDelete — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_rest_methods.htm
- RestContext, RestRequest and RestResponse — reading the request URI and setting response headers and status — https://developer.salesforce.com/docs/atlas.en-us.apexref.meta/apexref/apex_class_System_RestContext.htm
- ApexClass metadata — the apiVersion element in .cls-meta.xml, which governs platform semantics and is independent of your URL version — https://developer.salesforce.com/docs/atlas.en-us.api_meta.meta/api_meta/meta_classes.htm
- Salesforce API versioning and retirement of legacy API versions — https://help.salesforce.com/s/articleView?id=000389108&type=1
