# Start here — SfSkills Salesforce AI Engineering Framework

This package is the implementation-grade product specification for turning the existing SfSkills repository into a Salesforce AI engineering framework.

It is designed to answer four questions before Cursor changes the repository:

1. **What product are we building?** A portable, evidence-grounded engineering intelligence and assurance layer for Salesforce—not another prompt archive, generic code generator, or replacement for mature DevOps platforms.
2. **How must it behave?** Through numbered requirements, typed products, agent contracts, evidence schemas, context budgets, security policies, honest terminal states, and replayable run bundles.
3. **How will we know it works?** Through deterministic tests, actual host smoke tests, live read-only checks, disposable scratch-org known truth, baseline comparisons, and strict release thresholds.
4. **What must Cursor return for review?** A reconstructable local Git bundle, exact source and test evidence, host runs, Salesforce QA artifacts, traceability, checksums, and a secret scan.

## The one implementation prompt

Give Cursor:

```text
implementation/CURSOR_BUILD_SFSAEF_V2.md
```

Give it this entire specification directory at the same time. Do not paste individual product files and ask Cursor to improvise the missing contracts.

Cursor must work on a local-only branch, make milestone commits and tags, run the required gates, and return the ZIP specified in:

```text
implementation/REVIEW_RETURN_CONTRACT.md
```

## Product outcome

A practitioner opens Cursor in any workspace, installs SfSkills locally, and invokes a product such as:

```text
/triage-deployment
/triage-apex-tests
/why-cant-user
/plan-metadata-change
```

The framework then:

1. validates the request and target identity;
2. creates a typed run and authority profile;
3. selects a small, measured Salesforce context;
4. gathers bounded read-only evidence from fixtures, an optional external Salesforce project, and/or an explicitly selected org;
5. creates material claims with stable evidence links;
6. challenges the draft independently;
7. returns `completed`, `partial`, `refused`, or `failed` honestly;
8. saves a redacted, replayable run bundle.

## Package reading path

Read in this order:

1. `research/010-executive-product-thesis.md`
2. `strategy/000-category-and-positioning.md`
3. `spec/020-design-principles.md`
4. `architecture/000-system-map.md`
5. `SPEC_INDEX.md`
6. `products/README.md`
7. `implementation/IMPLEMENTATION_SEQUENCE.md`
8. `implementation/CURSOR_BUILD_SFSAEF_V2.md`
9. `migration/catalogs/V2_DISPOSITION_LEDGER.md`
10. `implementation/REVIEW_RETURN_CONTRACT.md`

## Validate this package

From this directory:

```bash
python3 scripts/run_all_checks.py --write-generated
python3 scripts/run_all_checks.py
```

The first command refreshes deterministic catalogs and the manifest. The second proves they are current and runs package and reference-kernel tests.

## What “80% built here” means

This package fully specifies the product behavior, portfolio, architecture, control contracts, context design, evidence model, safety boundary, QA truth, market position, implementation order, and review evidence. It also provides a tested deterministic reference kernel.

Cursor still must implement and integrate repository code, native host packages, MCP adapters, Salesforce CLI behavior, scratch-org scenarios, and real host runs. It must return one `sfskills-v2-cursor-return-YYYYMMDD-HHMMSS.zip` containing a reconstructable Git bundle, exact tests, actual host evidence, run bundles, QA, security, and traceability. Real product quality cannot be authored in a document; it must be demonstrated in the return ZIP.
