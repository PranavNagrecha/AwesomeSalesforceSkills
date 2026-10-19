# Well-Architected Notes — SFDX Monorepo Patterns

**Operational Excellence:** the directory layout is the deployment boundary. Anything under
a `packageDirectories` path is package content and reaches every org that installs it, so
the decision about where a file lives is a decision about what ships — not an organisational
preference. Seed data and one-off scripts kept inside a package become permanent metadata in
a subscriber org that nobody can later account for; the same files in a sibling directory
outside every package path are equally accessible to CI and invisible to the artefact.

**Operational Excellence, the default directory:** exactly one path can be the default, and
its real function is to catch components a retrieve can't match to an existing local file. Pointing
it at the base package makes an accidental retrieve land somewhere reviewers are already
looking, instead of quietly inside a feature team's package where it will be shipped by the
next version create. This is cheap insurance against a mistake that is otherwise silent.

**Scalability:** teams scale independently only if the shared surface has an owner. A field
can live in a different directory from its custom object; two directories both believing they
define the object is a defect that development scratch orgs cannot detect, because everything
is pushed into them. Give every shared object one owning package and make the extensions depend on it — the
dependency is what makes install order deterministic instead of incidental.

**Scalability, CI economics:** validating everything on every push is correct and
unaffordable, and a gate slow enough to be ignored is worse than no gate, because it still
consumes the time. The affordable version scopes both the *set* and the *depth*: build the
packages affected by the change — expanded through the dependency graph, since a base change
breaks consumers whose files did not move — and choose the test level by risk, with specified
tests on a pull request and the full local-test run before production.

**Reliability:** the failure mode unique to this layout is that the development environment
cannot reproduce it. A scratch org with all packages pushed installs fine regardless of
whether dependencies are declared, ownership is clear, or the order is right. Every one of
those defects surfaces first in a clean org — which is the argument for having a clean-install
job at all, and for not treating a green scratch org as evidence about installation.

## Official Sources Used

Corpus: `sfdx_dev.txt` is the Salesforce DX Developer Guide, Summer '26 (API 67.0), fetched from resources.docs.salesforce.com/262 and converted with `pdftotext -layout`; `api_meta.txt` is the Metadata API Developer Guide, Summer '26. Line numbers are `grep -n` positions.

- `sfdx_dev.txt` L2457–2473 — multiple package directories, listed separately in `packageDirectories`; the structure is client-side only and deploys have no association with packages in the org (gotcha 3, SKILL.md Core Concepts).
- `sfdx_dev.txt` L2484–2488 — a custom object in the default directory and a field on it in an extension directory (gotcha 1, anti-pattern 3).
- `sfdx_dev.txt` L2526–2552 — deploy of all directories in one transaction for new orgs, `--source-dir` targeting, retrieve placing unmatched components in the default directory (gotcha 2).
- `sfdx_dev.txt` L14724–14740 — `default`: retrieve target, only one package directory can have default true (Review Checklist, checker).
- `sfdx_dev.txt` L1784–1806 and L1893–1931 — `.forceignore` syntax and the nearest-file-wins resolution with a per-package example (gotcha 5, checker).
- `sfdx_dev.txt` L2410–2420 — `sourceApiVersion` determines the fields retrieved for each metadata type (gotcha 7).
- `sfdx_dev.txt` L14750–14826 — `dependencies` declaration in install order (gotcha 6, examples.md).
- `api_meta.txt` L3143–3163 — `testLevel` values; `RunLocalTests` excludes tests from installed managed and unlocked packages (anti-pattern 7).
- `sfdx_dev.txt` L16147 (also L15695) — 75% code coverage before an unlocked package can be promoted (test classes stay inside the package).
