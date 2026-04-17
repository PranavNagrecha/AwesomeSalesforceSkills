# Requirements — {{feature_summary_short}}

> Run ID: `{{run_id}}`
> Generated: `{{generated_at}}` (UTC)
> Agent: `integration-catalog-builder` v{{agent_version}}
> Inputs packet SHA256: `{{inputs_sha256}}`

Approval anchor for the integration catalog JSON.

---

## 1. Feature statement

{{feature_summary}}

## 2. Catalog

- **Catalog name:** `{{catalog_name}}`
- **Target org alias (Gate C live):** `{{target_org_alias_or_library_only}}`
- **API version:** `{{api_version}}`
- **Emitted inventory:**
{{catalog_inventory_bullets}}

## 3. Referenced Named Credentials

{{named_credentials_bullets}}

Every NC above MUST exist in the target org at Gate C time. Missing NCs surface as component failures in the envelope.

## 4. Grounding contract (Gate B)

{{grounding_symbols_bullets}}

## 5. Explicit non-goals

- Does not test the integrations themselves.
- Does not store credentials — NCs are referenced by name only.
- Does not author new Named Credentials.

## 6. Approval

By re-invoking `run_builder.py --stage ground --approved-requirements <this file>`, the caller affirms Sections 1–3.
