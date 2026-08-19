---
name: sfskills-doctor
description: Check SfSkills Cursor plugin install, MCP, Salesforce CLI, org aliases (no secrets), and search-index presence. Reports index_missing explicitly.
---

# /sfskills-doctor

Run the focused doctor. Prefer:

```bash
python3 scripts/sfskills_doctor.py --json
```

from the SfSkills checkout (or the path printed by the install helper).

Interpret `search_index.status == index_missing` as a setup failure, not as "the library has no matching skills".

Do not mutate the org. Do not install packages. Print reload/uninstall hints from the doctor output.
