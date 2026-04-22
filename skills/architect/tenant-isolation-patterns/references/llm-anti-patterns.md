# LLM Anti-Patterns — Tenant Isolation Patterns

Common mistakes AI coding assistants make when designing multi-tenant Salesforce architecture.

## Anti-Pattern 1: Tenant-branched Apex

**What the LLM generates:** `if (tenant == 'A') { ... } else if (tenant == 'B') { ... }` in production Apex.

**Why it happens:** The model sees tenant variation and reaches for conditionals; custom-metadata-driven branching is less familiar.

**Correct pattern:**

```
Tenant-specific behavior belongs in Custom Metadata (Feature_Flag__mdt,
TenantConfig__mdt). Apex reads config and behaves generically. Adding
a new tenant is a metadata deploy, not a code change.
```

**Detection hint:** Apex classes with hard-coded tenant names in conditionals.

---

## Anti-Pattern 2: OWD Public Read/Write with a Tenant__c field and no sharing rules

**What the LLM generates:** Adds `Tenant__c` and assumes "the filter in reports will hide other tenants' data."

**Why it happens:** The model confuses display filtering with security filtering.

**Correct pattern:**

```
OWD must be Private for tenant-scoped objects. Criteria-based sharing
rules per tenant grant visibility. Display-layer filters are trivially
bypassed; the platform sharing model is not.
```

**Detection hint:** A tenant-isolated org with OWD Public on the tenant-scoped objects.

---

## Anti-Pattern 3: Same managed package namespace for multiple ISV products

**What the LLM generates:** "Add both products to the same namespace to ease the upgrade path."

**Why it happens:** The model does not appreciate that namespace ownership is a permanent commitment.

**Correct pattern:**

```
Namespace = one product line. New product lines get separate managed
packages, separate namespaces, separate release cadences. Mixing
products in one namespace locks you into coupled releases forever.
```

**Detection hint:** An ISV proposal that puts multiple distinct product lines behind one namespace prefix.

---

## Anti-Pattern 4: Role hierarchy with cross-tenant parent role

**What the LLM generates:** A "Global Admin" role placed above every tenant's root role "for support efficiency."

**Why it happens:** The model optimizes for convenience; role hierarchy bypasses sharing rules.

**Correct pattern:**

```
Support access is via permission set group + explicit manual shares, not
role hierarchy. Cross-tenant roles silently grant full visibility and
defeat the whole isolation design.
```

**Detection hint:** A role hierarchy with a non-tenant-specific root role that sits above tenant-specific roles.

---

## Anti-Pattern 5: Sharing via single Public Group containing all users

**What the LLM generates:** Creates one public group `All_Tenant_Users`, grants read across all tenant records "for collaboration."

**Why it happens:** Public Groups are the model's go-to sharing primitive for bulk access.

**Correct pattern:**

```
Per-tenant Public Group or Permission Set Group. Cross-tenant collaboration,
if needed, goes through explicitly-scoped sharing rules — not a catch-all
group. Isolation has to be the default, collaboration the explicit
exception.
```

**Detection hint:** A Public Group with every org user in it, used as the sharing target for tenant records.
