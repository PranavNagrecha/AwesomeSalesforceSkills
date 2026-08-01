# Examples — OmniStudio Field Mapping Governance

Both examples assume the data mappers are already in source control as OmniStudio metadata.
Getting them there is `data/omnistudio-metadata-management`; authoring them is
`omnistudio/dataraptor-patterns`.

## Example 1: A field deletion that produced blanks instead of errors

**Context:** A quarterly cleanup removed a custom field on Account that Setup reported as
unused.

**Problem:** Three data mappers referenced it. Nothing failed. The mappers ran, the node was
simply absent from the output, and the OmniScript rendered an empty value where a figure had
been — for two weeks, until a user asked why a total looked wrong. Setup's answer had been
truthful about the dependencies it tracks; a mapper's field references live inside its own
configuration as strings, so they were not among them.

**Solution:** A build step that extracts every object/field pair referenced by any mapper in
the repository and compares it against what the target org actually exposes.

```python
#!/usr/bin/env python3
"""Fail the build when a data mapper references a field the org does not have.

Reads mapper metadata from the repo, writes the referenced (object, field) pairs to a
file that the Apex check below verifies against the live schema.
"""
import json
import pathlib
import sys

referenced: dict[str, set[str]] = {}

for path in pathlib.Path("force-app").rglob("*.json"):
    try:
        doc = json.loads(path.read_text())
    except (json.JSONDecodeError, UnicodeDecodeError):
        continue

    # Mapper items carry the source object and the field path they read.
    for item in doc.get("dataMappings", []):
        obj = item.get("sourceObject")
        field = item.get("sourceField")
        if obj and field:
            referenced.setdefault(obj, set()).add(field)

if not referenced:
    print("no mapper field references found — check the parser before trusting this", file=sys.stderr)
    sys.exit(1)

pathlib.Path("build/mapper-references.json").write_text(
    json.dumps({k: sorted(v) for k, v in referenced.items()}, indent=2)
)
print(f"extracted references across {len(referenced)} object(s)")
```

```apex
// Verify the extracted references against the schema of the target org.
// Anything missing here is a silent break in production, not a deployment error.
public class MapperReferenceCheck {

    public static Map<String, Set<String>> findBreaks(Map<String, Set<String>> referenced) {
        Map<String, Set<String>> breaks = new Map<String, Set<String>>();

        for (String objectApiName : referenced.keySet()) {
            Schema.SObjectType t = Schema.getGlobalDescribe().get(objectApiName);
            if (t == null) {
                breaks.put(objectApiName, referenced.get(objectApiName));   // object gone
                continue;
            }
            Set<String> live = new Set<String>();
            for (String f : t.getDescribe().fields.getMap().keySet()) {
                live.add(f.toLowerCase());
            }
            Set<String> missing = new Set<String>();
            for (String f : referenced.get(objectApiName)) {
                if (!live.contains(f.toLowerCase())) {
                    missing.add(f);
                }
            }
            if (!missing.isEmpty()) {
                breaks.put(objectApiName, missing);
            }
        }
        return breaks;
    }
}
```

**Why it works:** it makes the reference explicit at build time, which is the only point
where anything is watching. The platform will not raise on a missing source field at runtime,
so the check has to happen before deployment or not at all.

**Why the parser guards against finding nothing:** the failure mode of a script like this is
that a structural change makes it silently match zero items, at which point it reports success
forever. Treat "no references found" as a build failure — a checker that cannot fail is not a
checker.

**What this still does not cover:** it verifies fields exist, not that they are accessible to
the running user, and not that a Turbo Extract's relationship path is still valid. Pair it
with a post-deploy smoke test that runs each critical mapper and asserts the expected output
nodes are present **and populated**, because "returned an empty node" and "worked" are
indistinguishable from an error code.

---

## Example 2: Finding the mappers nobody calls, in both directions

**Context:** Around a hundred data mappers accumulated over three years of OmniStudio work,
with no record of which components used which.

**Problem:** Every object change triggered a review of all hundred, because nobody could say
which were live. The first cleanup attempt searched the OmniScript designer for each mapper's
name, found twelve with no hits, and deleted them — which broke two, because their callers
were in Apex and in a custom LWC rather than in an OmniScript.

**Solution:** Build the inventory from the repository rather than from a designer search, and
cover every kind of caller.

```bash
#!/usr/bin/env bash
# Which components reference each data mapper, by name, anywhere in the repo.
# Callers are Apex, LWC and OmniStudio metadata — a designer-only search misses two of three.
set -euo pipefail

MAPPERS=$(python3 -c "
import json, pathlib
names = []
for p in pathlib.Path('force-app').rglob('*.json'):
    try:
        d = json.loads(p.read_text())
    except Exception:
        continue
    if 'dataMappings' in d and d.get('name'):
        names.append(d['name'])
print('\n'.join(sorted(set(names))))
")

echo "mapper,callers"
while IFS= read -r NAME; do
  [ -z "$NAME" ] && continue
  # Search every caller surface, not just OmniStudio metadata.
  COUNT=$(grep -rl --fixed-strings "$NAME" \
            force-app/main/default/classes \
            force-app/main/default/lwc \
            force-app/main/default/aura \
            force-app 2>/dev/null | grep -v "/${NAME}\." | sort -u | wc -l | tr -d ' ')
  echo "${NAME},${COUNT}"
done <<< "$MAPPERS"
```

**Why it works:** it inverts the question. A designer search answers "which OmniScripts use
this", which is a subset — Apex and custom LWCs call mappers by name too, and those calls are
plain strings that no designer view enumerates. Building the list from the repository covers
every surface that is in source control.

**How to use the output, and how not to:** a count of zero is a finding, not a deletion
order. Confirm against anything outside the repository — a package, an external integration
calling through an API, a scheduled job — before removing. The value of the report is that it
reduces a hundred unknowns to a dozen questions, not that it answers them.

**Keep it in both directions.** The forward index (mapper to fields) from example 1 tells you
what breaks when a field changes. The reverse index (mapper to callers) here tells you what
breaks when a mapper changes, and which mappers are pure maintenance cost. Neither is derivable
from the other, and each one is what makes the other safe to act on.

**On renames:** the reverse index is also the prerequisite for renaming anything. Because
callers hold the mapper's name as a string, a rename updates nothing downstream and still
saves cleanly — so the rename has to be staged as introduce, migrate, retire. If the caller
list is unknown, the correct decision is to leave the name alone and apply the naming standard
to new components only.
