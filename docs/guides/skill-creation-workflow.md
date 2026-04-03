# Skill Creation Workflow

## Before Writing

1. Install repo tooling if needed:
   - `python3 -m pip install -r requirements.txt`
2. Search the repo:
   - `python3 scripts/search_knowledge.py "<topic>"`
3. Check the relevant official docs from `standards/official-salesforce-sources.md`.
4. Confirm the skill is not a duplicate in `docs/SKILLS.md` or `registry/skills.json`.

## Required Creation Steps

1. Create the skill package under `skills/<domain>/<skill-name>/`
2. Fill out frontmatter completely, including `tags`, `inputs`, `outputs`, and `dependencies`
3. Add references, at least one template file, and at least one stdlib-only checker script
4. Record `Official Sources Used`
5. Run:
   - `python3 scripts/skill_sync.py --skill skills/<domain>/<skill-name>`
   - `python3 scripts/validate_repo.py`

## Definition Of Done

- schema-valid frontmatter
- required package files present
- official sources recorded
- generated artifacts updated
- repo validation passes
