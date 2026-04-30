# Gotchas — Release Notes Automation

Non-obvious behaviors that cause real production problems in this domain.

## Gotcha 1: `git describe` requires fetch-depth 0 in CI

**What happens:** Pipeline returns "fatal: No names found, cannot describe anything" — release notes pipeline fails on the first run after a green CI build.

**When it occurs:** GitHub Actions / Bitbucket Pipelines clone with shallow depth by default; tag history is missing.

**How to avoid:** Set `fetch-depth: 0` in the checkout step. Test the resolver against the *previous* tag before relying on it for the current release.

---

## Gotcha 2: Squashed merge loses ticket keys

**What happens:** PR title was `ABC-1234: Fix race condition` but the merged commit subject is just `Fix race condition (#142)` because the team customized squash format.

**When it occurs:** Whenever the squash-merge subject template doesn't include the PR title, or maintainers edit the commit subject during merge.

**How to avoid:** Either lock the squash-merge format at the repo level (GitHub: "Default to PR title for squash merge"), or read PR titles via the host API instead of the commit log.

---

## Gotcha 3: Hotfix branch picks the wrong "previous" tag

**What happens:** Hotfix tagged `v2025.4.1` off `v2025.3.0` produces a notes section listing every commit between `v2025.4.0` and `v2025.4.1`, including changes that shipped in `v2025.4.0`.

**When it occurs:** `git describe --tags --abbrev=0` finds the most recent tag in history, regardless of whether it's an ancestor of the hotfix branch.

**How to avoid:** For hotfix releases, pass an explicit `from-ref` input. The pipeline must support manual override.

---

## Gotcha 4: Metadata-diff scope leaks .forceignore'd files

**What happens:** Notes list `force-app/main/default/profiles/Admin.profile-meta.xml` as changed, but profile changes are intentionally excluded from deploy via `.forceignore`. Stakeholders chase a phantom change.

**When it occurs:** When the `git diff` filter doesn't honor `.forceignore` parsing.

**How to avoid:** Apply `.forceignore` filtering before grouping diff entries. Many libraries don't do this — implement explicitly with `pathspec` or a hand-rolled glob matcher.

---

## Gotcha 5: Tag patterns collide with feature-branch tags

**What happens:** A contributor tags a personal experiment `v-mybranch`. The next release-notes pipeline picks that as the previous tag.

**When it occurs:** Lax tag governance.

**How to avoid:** Pin the match pattern strictly — `v[0-9]*.[0-9]*.[0-9]*` or a named pattern (`release-*`). Add a CI guard rejecting non-matching `v*` tags.
