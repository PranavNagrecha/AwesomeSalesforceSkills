# /audit-record-types — LEGACY ALIAS (Wave 3b-1)

> **Deprecation notice:** this command is now an alias. It invokes the
> [`audit-router`](../agents/audit-router/AGENT.md) with
> `--domain=record_type_layout` and emits this deprecation notice. Switch
> to the canonical `/audit-router` form at your convenience. The alias
> still ships (redirect table: `agents/_shared/RUNTIME_VS_BUILD.md`).

## Canonical form

```
/audit-router --domain record_type_layout --object <ApiName> --target-org <alias>
```

## Alias behavior

Running `/audit-record-types <args>` is equivalent to:

```
/audit-router --domain record_type_layout <args>
```

The RT + Layout rule table (proliferation, Master Layout as primary,
orphan RTs, inactive RT still referenced by flows or VRs, Lightning
Record Page mapping gaps, Business Process attachments) is preserved
verbatim in
[`classifiers/record_type_layout.md`](../agents/_shared/harnesses/audit_harness/classifiers/record_type_layout.md).

## Why the change

Wave 3b-1 of the redesign consolidated 5 auditors into one router.
See [`agents/_shared/harnesses/audit_harness/README.md`](../agents/_shared/harnesses/audit_harness/README.md)
for the rationale.

## See also

- [`/audit-router`](./audit-router.md) — canonical router entry point
- [`agents/audit-router/AGENT.md`](../agents/audit-router/AGENT.md) — router contract
- [`agents/_shared/RUNTIME_VS_BUILD.md`](../agents/_shared/RUNTIME_VS_BUILD.md#deprecated-slash-command-redirects) — deprecated-command redirect table
