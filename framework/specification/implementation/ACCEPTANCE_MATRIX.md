# V2 acceptance matrix

| Area | Release-candidate expectation |
|---|---|
| Core contracts | All schemas validate; reference behavior preserved; traceability complete |
| Cursor | Local install/uninstall, commands, bounded skills, focused subagents, restricted MCP, hooks/capability report |
| P01–P03 | Actual host fixture run, independent review, scratch known-truth where credentials available, release thresholds met |
| P04–P06 | Actual host fixture-qualified, shared architecture, explicit beta/RC status |
| P07–P12 | End-to-end beta fixture paths, typed contracts, no stable claim without behavioral evidence |
| Context | target <=8, hard <=12, <=32 KiB page, explicit overflow, checkpoint/resume tests |
| Evidence | stable IDs, valid support links, contradictions, deterministic lint, confidence rationale |
| Security | product read-only, unknown deny, target pinning, injection/bypass tests, secret scan |
| Real org | read-only product tools; separate guarded scratch setup; cleanup proof |
| Portability | Cursor verified; Claude regression; one additional adapter proof of concept |
| Release | clean local commit/tag, deterministic builds, source archive + Git bundle, exact logs, docs/limitations |
