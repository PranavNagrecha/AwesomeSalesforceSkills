# Gotchas - Custom Metadata Types

## Runtime Writes Are The Wrong Mental Model

**What happens:** A team designs a setup where business users change CMT records as part of daily operations and then discovers the write path does not fit normal record-edit transactions.

**When it occurs:** The metadata type is treated like a Custom Object instead of release-managed configuration.

**How to avoid:** Decide early whether the records are deployable config or business data. If the change frequency is operational rather than release-driven, pick a different storage model.

---

## Protected Visibility Only Solves Package Encapsulation

**What happens:** Architects assume protected CMT is a generic "admins cannot ever see this" feature for any org.

**When it occurs:** The design mixes packaging visibility with general-purpose data security requirements.

**How to avoid:** Use protected metadata only for managed-package boundaries. Use Named Credentials or another supported secret strategy when the concern is sensitive values.

---

## `DeveloperName` Becomes A Stable API

**What happens:** A record name is changed for readability, then Apex, Flow, or formulas that reference the old metadata key start failing or returning no match.

**When it occurs:** The implementation treats metadata names as labels instead of contracts.

**How to avoid:** Separate labels from lookup keys. Keep `DeveloperName` stable and rename only when you are also updating every consumer safely.

---

## Public CMT With Environment-Specific URLs Creates Hidden Drift

**What happens:** Sandbox and production endpoint details get copied into record values and diverge over time, even though the org already uses Named Credentials.

**When it occurs:** Teams put full hostnames or tokens into metadata because it feels convenient during development.

**How to avoid:** Put host and auth concerns in Named Credentials. Keep CMT focused on path fragments, functional flags, thresholds, and non-secret configuration.
