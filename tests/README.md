# `tests/` — unit tests for the build tooling

`scripts/` and `pipelines/` decide what ships. When `pipelines/ranking.py` or
`pipelines/validators.py` breaks, every downstream artifact is silently wrong
and no gate notices, because the gates ARE the broken code.

This suite covers the modules on that path. It is stdlib `unittest`, matching
the convention in `mcp/sfskills-mcp/tests/`.

## Running it

```bash
python3 -m unittest discover -s tests -t tests          # from the repo root
python3 -m unittest discover -s tests -t tests -v       # per-test names
python3 -m unittest discover -s tests -t tests -k ranking
```

`-t tests` is load-bearing: `tests/` has no `__init__.py`, so `-t .` raises
"Start directory is not importable". Each module puts the repo root on
`sys.path` itself, so the discovery form does not need to.

The whole suite runs in well under a second and needs no org, no network and
no API key.

## What is covered

| Module under test | File | Why it is on the critical path |
| --- | --- | --- |
| `pipelines/ranking.py` | `test_ranking.py` | Chooses which skill a query resolves to, for both the CLI and the MCP server |
| `pipelines/lexical_index.py` | `test_lexical_index.py` | The mandatory no-API-key retrieval path; raw user input reaches FTS5 through it |
| `pipelines/frontmatter.py` | `test_frontmatter.py` | Every SKILL.md and AGENT.md enters the pipeline here; `stable_hash_for_files` is the drift detector |
| `pipelines/validators.py` | `test_validators.py` | Every gate that decides whether a skill may ship |
| `scripts/check_doc_counts.py` | `test_check_doc_counts.py` | The "56 agents" regression guard |

## House rules for adding tests here

**Hermetic.** Build fixtures in a temp dir. Never read the real
`skills/` corpus and never open `vector_index/` — the artifacts there total
~800 MB and loading them costs gigabytes of RAM. Every helper in this suite
already writes its own synthetic repo.

**Assert both directions.** A gate test that only checks the FAIL case passes
against a validator that always errors; one that only checks PASS passes
against a validator that always returns `[]`. `test_validators.py` pairs them
deliberately.

**Prove the test can fail.** Break the code in a scratch copy, watch the test
go red, restore. Every test in this suite was verified this way against 66
single-line mutations of the modules under test.

**Do not encode a known bug as expected behaviour.** When a test uncovers a
real defect, assert the CORRECT behaviour and mark it
`@unittest.expectedFailure` with a comment naming the file and line. The suite
stays green today, and `unittest` reports an *unexpected success* — a failing
run — the moment the bug is fixed, which is the prompt to delete the decorator.
There is no live example today: `UnsanitisedQueryCrashTest` in
`test_lexical_index.py` was the worked example until the FTS5 sanitiser
defect it documented was fixed in `pipelines/lexical_index.py`, at which
point the decorator was deleted exactly as this rule prescribes.
