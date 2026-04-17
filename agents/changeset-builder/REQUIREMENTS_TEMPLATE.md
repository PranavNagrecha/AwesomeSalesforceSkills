# Requirements — {{feature_summary_short}}

> Run ID: `{{run_id}}`
> Generated: `{{generated_at}}` (UTC)
> Agent: `changeset-builder` v{{agent_version}}
> Inputs packet SHA256: `{{inputs_sha256}}`

Approval anchor for the `package.xml` manifest. Everything Gate C emits is checked back against this file.

---

## 1. Feature statement

{{feature_summary}}

## 2. Manifest

- **Package name:** `{{package_name}}`
- **API version:** `{{api_version}}`
- **Target org alias (Gate C preview):** `{{target_org_alias_or_library_only}}`
- **Emitted inventory:**
{{package_inventory_bullets}}

## 3. Items

{{items_bullets}}

Every item MUST resolve against the target org at Gate C time. The live oracle is `sf project retrieve preview` (no mutations).

## 4. Grounding contract (Gate B)

{{grounding_symbols_bullets}}

## 5. Explicit non-goals

- Does not deploy the package — preview only.
- Does not touch source-format metadata on disk.
- Does not diff orgs — the caller owns the decision of what goes in.

## 6. Approval

By re-invoking `run_builder.py --stage ground --approved-requirements <this file>`, the caller affirms Sections 1–3.
