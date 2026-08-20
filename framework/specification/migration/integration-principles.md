# Integration principles for the existing repository

1. Preserve the 1,034 skill packages as the knowledge corpus.
2. Preserve existing Claude/router behavior until a tested V2 adapter replaces it.
3. Keep legacy command wrappers; introduce typed specs for shipped/touched V2 products first.
4. Keep existing MCP tools; wrap or normalize where product semantics require it.
5. Treat the official Salesforce DX MCP as an upstream option, not an unquestioned security boundary.
6. Do not export all 48 runtime agents as host-native subagents.
7. Convert broad dependency lists only when the corresponding agent/product is migrated.
8. Generate host packages from canonical definitions.
9. Record every intentional baseline behavior change.
10. Delete abstractions that lack a consumer and test.
