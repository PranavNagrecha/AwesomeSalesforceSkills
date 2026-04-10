# Well-Architected Notes — FSL Mobile App Extensions

## Relevant Pillars

- **Security** — LWC extensions run with the current user's sharing context. Custom Object caches for offline CMT data must enforce object-level security (use `with sharing` on all Apex controllers). The "Enable Lightning SDK for FSL Mobile" permission set should be granted only to users who need FSL Mobile extensions, not added to a broad permission set group. Deep link URIs should not embed sensitive field values in the URI payload.
- **Performance** — Priming volume directly impacts offline sync time. Over-priming (too many objects, no date/status filters) slows the sync and risks hitting the 1,000 page-reference limit. Use Briefcase Builder filters aggressively. LDS wire adapters are preferred over imperative Apex calls because they serve from cache on repeat requests.
- **Reliability** — Extensions that work online but fail offline are a reliability failure for field technicians who depend on the app to do their jobs. The offline availability checklist (permission set + page layout placement) must be treated as a reliability gate, not an optional step. CMT cache patterns exist specifically to avoid silent data unavailability.
- **Operational Excellence** — Priming configuration must be documented alongside extension configuration. When a new extension adds a related object (e.g., custom child object of WorkOrder), Briefcase Builder must be updated to prime that object. Omitting this step produces a working online extension that silently fails offline — an operational blind spot.

## Architectural Tradeoffs

**LWC Actions vs HTML5 Toolkit:** LWC actions are maintainable, testable, and benefit from LDS offline caching. HTML5 toolkit extensions have no LWC capabilities and require REST-based Apex calls that fail offline. The only reason to choose HTML5 Toolkit today is maintaining existing legacy extensions where a full rebuild is not justified. All new work should use LWC.

**Priming breadth vs sync performance:** Priming more objects and more records gives technicians richer offline access but increases sync time, battery use, and the risk of hitting the 1,000 page-reference limit. The right balance depends on territory size and the technician's typical work window. Start with narrow filters (7-day window, scheduled/dispatched status) and widen only if technicians report missing data.

**Wire adapter for CMTs vs hard-coded constants:** The wire + cache pattern is flexible but adds schema (Custom Object, Apex class, LWC glue). For configuration that changes rarely and is not sensitive, embedding values as constants in the LWC is simpler and has no offline failure mode. Reserve the cache pattern for configuration that operations teams update without a deployment.

## Anti-Patterns

1. **App Builder-only action placement** — Configuring a Quick Action only in App Builder and relying on that for offline availability. App Builder drives the dynamic layout (online). The page layout drives the static layout (offline). An extension that only appears online is a reliability failure for mobile workers.

2. **Querying Custom Metadata Types imperatively at button click** — Calling `getFailureCodes()` (imperative Apex) inside a button handler assumes connectivity. This pattern works in the desktop browser during development, passes QA when testers are online, and then fails silently for technicians in the field. Always use the wire adapter with an offline fallback for any CMT-backed configuration data.

3. **Unbounded Briefcase Builder priming** — Configuring Briefcase Builder to prime all appointments for all technicians without date or status filters. This hits the 1,000 page-reference limit silently and produces inconsistent data availability that is difficult to diagnose because no error is surfaced.

## Official Sources Used

- Customize FSL Mobile with LWC — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_extension_lwc.htm
- Deep Linking Schema — Field Service Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.field_service_dev.meta/field_service_dev/fsl_mobile_deep_linking.htm
- FSL Mobile Extension Overview — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_extensions.htm
- Offline Priming and Briefcase Builder — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_priming.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
- Apex Developer Guide — https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_dev_guide.htm
