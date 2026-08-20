# Cursor implementation prompt: add the optional SfSkills Salesforce Project Inspector

You are working in the current local SfSkills V2 branch. Add one bounded component only: the optional `sf-project-inspector` used by deployment and Apex-test triage to enrich evidence with local Salesforce metadata paths.

A companion ZIP contains canonical candidate files under `repo-files/`. Treat them as reviewed implementation input, not as permission to overwrite newer branch work blindly.

## Product correction

SfSkills is a skill library, not a Salesforce DX project. Local source mapping must be optional. The product must support:

1. **Explicit project mode** — the user or command supplies a Salesforce project path or a file inside that project.
2. **Workspace mode** — exactly one project containing `sfdx-project.json` is discovered from the active working directory or bounded workspace roots.
3. **Standalone mode** — no local project is present; diagnosis continues using fixture/org/SfSkills evidence.
4. **Ambiguous mode** — multiple projects are found; do not guess. Return candidates and require explicit selection.

## Files supplied

Review and integrate these repository-relative files:

- `pipelines/product/__init__.py`
- `pipelines/product/project_discover.py`
- `scripts/sf_project_inspector.py`
- `integrations/cursor/agents/sf-project-inspector.md`
- `tests/product/__init__.py`
- `tests/product/test_project_discover.py`
- `config/product/project-inspection.schema.json`
- `docs/product-v2/sf-project-inspector.md`

## Integration procedure

1. Inspect the current branch for existing implementations with the same purpose. Preserve stronger existing behavior and merge contracts instead of duplicating modules.
2. Ensure the final deterministic Python implementation remains standard-library-only at runtime.
3. Update the native Cursor plugin builder/manifest so `sf-project-inspector.md` is packaged exactly once.
4. Replace mandatory `sf-repo-mapper` references in the shipped triage command, agent prompts, docs, and tests with optional `sf-project-inspector` behavior.
5. Add an optional `project_path`/`repo_path` input alias to `/triage-deployment` if the current command contract has neither. Choose one canonical output field and document the alias.
6. Do not assume the SfSkills repository is the target Salesforce project. A directory is a Salesforce project only when its selected/ancestor root has a valid `sfdx-project.json`.
7. Do not make standalone mode a refusal or failure. Mark local source mapping unavailable and continue.
8. Do not run Salesforce CLI, mutate files, deploy metadata, or scan outside the selected project/package roots.
9. Keep all current product Salesforce tools read-only.
10. Make local commits only. Do not push, publish, open a PR, or submit a marketplace package.

## Required behavior

- Explicit invalid paths return `invalid`; they must not silently fall back.
- The nearest ancestor project is selected for a file/path inside a DX project.
- Multiple workspace projects return `ambiguous` with sorted candidates.
- No project returns `standalone` with exit code 0 by default.
- Package-directory paths escaping the project root are rejected.
- Mapping is deterministic and bounded for common metadata types, including Apex classes/triggers, LWC/Aura bundles, flows, custom objects/fields, validation rules, permission sets, profiles, layouts, FlexiPages, and nested object metadata.
- Missing components return `not_found`; never invent a path.
- Unsafe component names containing traversal or path separators return `invalid_component`.
- The subagent returns a compact structured handoff, never a full terminal transcript.

## Tests

Run and capture exact exit codes for:

```bash
python3 -m unittest tests.product.test_project_discover -v
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/build_cursor_plugin.py --check
```

Use the actual plugin builder command if the branch uses a different name. Rebuild generated output before `--check` when required.

Add or retain tests for:

- explicit root;
- file inside project;
- invalid explicit path;
- cwd ancestor discovery;
- one workspace project;
- multiple-project ambiguity;
- valid standalone mode;
- malformed descriptor;
- escaping package directory;
- Apex class mapping;
- custom field mapping;
- LWC bundle mapping;
- honest not-found result;
- unsafe component name;
- CLI standalone exit behavior;
- plugin packaging includes the agent once;
- `/triage-deployment` continues when local mapping is unavailable.

## Local commit

Create one local commit with a message similar to:

```text
feat(v2): add optional Salesforce project inspector
```

Do not rewrite unrelated history.

## Required review ZIP

Create a self-contained ZIP named:

```text
sfskills-v2-project-inspector-review.zip
```

It must contain:

- `BASELINE_SHA.txt`
- `HEAD_SHA.txt`
- `COMMITS.txt`
- `STATUS.txt`
- `CHANGED_FILES.txt`
- `DIFF.patch`
- `SOURCE/` containing every changed/additional file in the reviewed range
- `TESTS/project-inspector.log`
- `TESTS/full-unit-suite.log`
- `TESTS/cursor-plugin-check.log`
- `ARTIFACTS/cursor-plugin-tree.txt`
- `ARTIFACTS/discovery-explicit.json`
- `ARTIFACTS/discovery-standalone.json`
- `ARTIFACTS/discovery-ambiguous.json`
- `ARTIFACTS/component-mapped.json`
- `ARTIFACTS/component-not-found.json`
- `REVIEW_REPORT.md`
- `SHA256SUMS.txt`

Every test log must show the command, working directory, stdout, stderr, and real exit code. Do not claim a pass when a command did not run. The review ZIP must include the actual source files, not only a patch.

## Final report

Stop after this component. Report:

1. baseline/head SHA;
2. local commit SHA;
3. files changed;
4. integration decisions;
5. tests and exact results;
6. generated plugin verification;
7. known limitations;
8. review ZIP path and SHA-256;
9. confirmation that nothing was pushed or published.
