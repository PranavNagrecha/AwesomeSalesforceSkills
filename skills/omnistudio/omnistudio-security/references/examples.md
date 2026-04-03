# OmniStudio Security — Examples

## Example 1: Narrowing A Portal OmniScript Contract

**Context:** An external-user OmniScript lets partners submit updates for a case-like process.

**Problem:** The first design reuses an internal Integration Procedure response that includes support-only fields and diagnostic text.

**Solution:**

```text
- Create a narrower external response contract
- Strip internal fields before returning to the OmniScript
- Keep support diagnostics in logs or internal-only outputs
```

**Why it works:** The portal experience receives only the data it needs.

---

## Example 2: Securing Custom Apex Behind OmniStudio

**Context:** A custom OmniStudio action calls Apex for data enrichment.

**Problem:** The Apex class was written for internal use and does not clearly enforce sharing or CRUD/FLS.

**Solution:**

```text
- Review the Apex entry point as a public service boundary
- Use explicit sharing and CRUD/FLS enforcement
- Re-check the returned shape for portal or guest suitability
```

**Why it works:** The security review follows the real data path rather than assuming OmniStudio made it safe.

---

## Anti-Pattern: Public OmniStudio Surface With Internal Contract

**What practitioners do:** Expose the same OmniStudio asset chain to guest or partner users that internal staff use.

**What goes wrong:** Broad fields, unsafe Apex assumptions, and noisy responses become external exposure risks.

**Correct approach:** Narrow the external contract and review every dependency for least privilege.
