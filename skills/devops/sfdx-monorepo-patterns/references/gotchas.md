# Gotchas — SFDX Monorepo Patterns

## Gotcha 1: Cross-package field ownership

**What happens:** Two packages define fields on Account; deploy order breaks.

**When it occurs:** Shared Account extensions.

**How to avoid:** Put all shared-object fields in a 'base' package; dependents reference them.


---

## Gotcha 2: Missing dependency declaration

**What happens:** Deploy fails in prod; works in scratch.

**When it occurs:** Dev hand-installs a dep.

**How to avoid:** Encode deps in sfdx-project.json.


---

## Gotcha 3: Templates shipped to prod

**What happens:** Tooling files leak into org.

**When it occurs:** Templates in package dir.

**How to avoid:** Keep tools/ outside package dirs.

