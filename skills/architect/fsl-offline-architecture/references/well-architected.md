# Well-Architected Notes — FSL Offline Architecture

## Relevant Pillars

- **Reliability** — The 1,000 page reference limit causes silent data gaps that only manifest in the field. Design with explicit page reference calculations and test with production-representative data. Ghost record cleanup must be automated — relying on manual cleanup creates inconsistent technician experience.
- **Performance** — Priming volume affects sync duration. Oversized priming hierarchies (near the 1,000 page reference limit) create long sync times that consume the mobile work day. Design for a target sync time under 60 seconds.
- **Security** — MERGE_ACCEPT_YOURS gives the field device precedence over server-side changes. For regulated industries where server-side (office-side) data is authoritative, evaluate MERGE_FAIL_IF_CONFLICT or field-restricted edit permissions to prevent offline overwrites from erasing compliance-critical data.

## Architectural Tradeoffs

**MERGE_ACCEPT_YOURS vs. MERGE_FAIL_IF_CONFLICT:** MERGE_ACCEPT_YOURS provides the simplest sync experience (no conflict dialogs) but can discard dispatcher changes silently. MERGE_FAIL_IF_CONFLICT surfaces every conflict for human review, which is accurate but adds friction for technicians. Choose based on how often dispatchers and technicians edit the same records concurrently.

**Deep priming vs. on-demand data access:** Priming all necessary data upfront provides the best offline experience but increases sync time and risks the page reference limit. An alternative is "lite priming" (only high-frequency required fields) combined with on-demand data access when connectivity allows. This is more complex to implement but scales better for deep data hierarchies.

**Server-side validation vs. app-layer validation:** Server-side (VRs, triggers) is the standard Salesforce quality gate but fires at sync time, not at job execution time. App-layer validation (custom LWC, OmniScript checks) fires in real-time during the work but requires custom development. Both are needed: app-layer for immediate field quality, server-side as the final backstop at sync.

## Anti-Patterns

1. **Relying on validation rules for offline data quality** — VRs fire at sync, not during offline work. Technicians can bypass them completely during the field work period. Design app-layer checks for offline quality enforcement.
2. **Not calculating page references before go-live** — Silent priming failure at 1,000+ page references is only discovered in the field, not in testing (unless testing with production-representative data volume).
3. **Not automating ghost record cleanup** — Ghost records that persist create incorrect appointment data on technician devices. Cleanup must be triggered automatically post-sync.

## Official Sources Used

- Offline Priming in FSL Mobile App (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_priming.htm
- Offline Considerations (help.salesforce.com) — https://help.salesforce.com/s/articleView?id=sf.fs_mobile_offline_considerations.htm
- Briefcase Sync Down Target (Mobile SDK Developer Guide) — https://developer.salesforce.com/docs/atlas.en-us.mobile_sdk.meta/mobile_sdk/briefcase_sync_down_target.htm
- Salesforce Well-Architected Overview — https://architect.salesforce.com/docs/architect/well-architected/guide/overview.html
