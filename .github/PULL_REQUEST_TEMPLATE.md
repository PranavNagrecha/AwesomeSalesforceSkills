<!-- Thanks for contributing! Fill out the sections that apply. -->

## What does this PR do?

<!-- One-paragraph summary. Focus on the WHY. -->

## Type of change

- [ ] New skill (`skills/<domain>/<name>/`)
- [ ] Update to an existing skill
- [ ] New MCP tool / prompt / resource
- [ ] MCP server bug fix
- [ ] Agent (`agents/<name>/AGENT.md`) addition or update
- [ ] Template / decision tree
- [ ] Documentation
- [ ] Tooling / CI / scripts
- [ ] Other (explain)

## Pre-flight checks

- [ ] `python3 scripts/validate_repo.py` exits 0
- [ ] If touching `mcp/sfskills-mcp/`: `python3 -m unittest discover -s mcp/sfskills-mcp/tests` exits 0
- [ ] If adding a skill: `python3 scripts/skill_sync.py --skill skills/<domain>/<name>` ran clean and the registry diff is included
- [ ] If adding an MCP tool: registered in `server.py` with the matching annotation profile; new test in `tests/`
- [ ] No `/Users/<author>/` paths or other identifiable info introduced
- [ ] Frontmatter is complete on every new SKILL.md / AGENT.md

## Linked issue

<!-- Closes #123 / Refs #456 -->

## Anything reviewers should look at first?

<!-- Risky bit, judgment call, follow-up debt -->
