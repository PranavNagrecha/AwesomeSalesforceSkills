# LLM Anti-Patterns — OmniStudio Field Mapping Governance

Scope: keeping the field references inside data mappers correct as the underlying objects
change. Authoring a mapper belongs to `omnistudio/dataraptor-patterns`; packaging and
deploying OmniStudio metadata belongs to `data/omnistudio-metadata-management`. This file is
about references breaking, and about nothing telling you that they have.

## Anti-Pattern 1: Using only the old name, so half the documentation is unreachable

Salesforce renamed the component: current documentation calls it an **Omnistudio Data
Mapper**, with the types documented as Data Mapper Extract, Turbo Extract, Transform and
Load. "DataRaptor" persists in older material, in the managed-package designer and in almost
every model's training data — so generated guidance sends people looking for a menu item
under a name the current UI may not use, and cites pages that have been superseded.

❌ Write "DataRaptor" throughout and cite only pre-rename pages.
✅ Lead with Data Mapper, note DataRaptor once as the prior name, and establish which runtime
the org is on before describing any navigation path — the managed-package designer and the
standard runtime do not present these identically. The naming split is also why searching the
old term returns stale answers; search the current term when checking behaviour.

Source: Omnistudio Data Mappers — https://help.salesforce.com/s/articleView?id=xcloud.os_omnistudio_dataraptors_45587.htm&type=5

## Anti-Pattern 2: Assuming a field reference is a dependency the platform tracks

The assumption underneath every governance failure in this area. A mapper's field references
live inside its own configuration as strings naming an object and a field. That is not the
same kind of relationship as a formula referencing a field, so the field can be renamed or
removed while the mapper carries on pointing at something that is no longer there.

❌ Delete a field after checking Setup for what uses it, and read a clean result as safe.
✅ Treat OmniStudio references as a separate inventory you maintain, and check it explicitly
before any field change. The comparison has to exist somewhere automated, because nothing in
the platform performs it for you:

```apex
// Enumerate what each object actually exposes, to diff against extracted mapper references.
public class MapperFieldAudit {
    public static Set<String> missingFields(String objectApiName, Set<String> referenced) {
        Schema.SObjectType t = Schema.getGlobalDescribe().get(objectApiName);
        if (t == null) {
            return referenced;                       // whole object is gone
        }
        Set<String> live = new Set<String>();
        for (String f : t.getDescribe().fields.getMap().keySet()) {
            live.add(f.toLowerCase());
        }
        Set<String> missing = new Set<String>();
        for (String r : referenced) {
            if (!live.contains(r.toLowerCase())) {
                missing.add(r);                      // a break that will NOT raise at runtime
            }
        }
        return missing;
    }
}
```

Emit the result as a build failure rather than as a report, because a report of things that
have not broken visibly yet is a report nobody reads.

## Anti-Pattern 3: Expecting the failure to be loud

The reason this class of defect reaches production. A missing source field usually does not
raise: the node is simply absent from the output, the consuming OmniScript renders an empty
value, and the user sees a blank where a number used to be. There is no exception to catch
and nothing to alert on.

❌ Rely on the deployment or the runtime to surface the break.
✅ Assert on the shape of the output rather than on the absence of an error. A post-deploy
smoke test that runs each critical mapper and checks that the expected nodes are **present
and populated** is the only thing that separates "worked" from "returned nothing quietly".
Silence is the default outcome here, so silence cannot also be the success signal.

## Anti-Pattern 4: Renaming a mapper without tracing who calls it by name

Callers reference a mapper by name — an OmniScript action, an Integration Procedure step,
Apex, an LWC. Those references are strings too, so a rename updates nothing downstream, and
it looks successful because the mapper itself saves cleanly.

❌ Rename for tidiness, then find the callers during the next release.
✅ Establish the caller set first and treat rename as a two-phase change: introduce the new
name, migrate callers, retire the old one. Enumerate across every caller surface, because
Apex and custom LWCs hold the name as a plain string and no designer view lists them:

```bash
#!/usr/bin/env bash
# Every reference to a mapper name, anywhere it can be held as a string.
set -euo pipefail
NAME="${1:?usage: callers.sh <MapperName>}"

grep -rl --fixed-strings "$NAME" \
     force-app/main/default/classes \
     force-app/main/default/lwc \
     force-app/main/default/aura \
     force-app 2>/dev/null \
  | grep -v "/${NAME}\."      # exclude the mapper's own definition file
```

Where that cost is not worth paying — which is usually — leave the name alone and apply the
naming standard to new components only. A convention applied going forward beats a rename
campaign against callers nobody enumerated.

## Anti-Pattern 5: Choosing Turbo Extract without checking what it gives up

Turbo Extract is faster and simpler, and generated advice recommends it on performance
grounds alone. It reads from a single Salesforce object plus fields from related objects, and
it explicitly **cannot use formulas, custom JSON, default values or transformations**. Teams
adopt it and then reintroduce the missing transformation downstream in an Integration
Procedure or an LWC — which moves mapping logic somewhere this governance process does not
look.

❌ Migrate every Extract to Turbo Extract for speed.
✅ Use Turbo Extract where the requirement genuinely is "read these fields from this object
and its relations". The moment a default value or a transformation is needed, a standard
Extract keeps that logic in one governable place. Mapping split between a Turbo Extract and a
hand-written transformation elsewhere is the expensive outcome, because half of it is then
invisible to any audit of the mappers.

Source: Omnistudio Data Mapper Turbo Extract Overview — the single-object scope and the exclusion of formulas, custom JSON, default values and transformations — https://help.salesforce.com/s/articleView?id=xcloud.os_dataraptor_turbo_extract_overview.htm&type=5

## Anti-Pattern 6: Letting versions accumulate with no rule about which one is live

Mappers and the components that call them are versioned, and it is easy to reach a state
where several versions exist, one is active, and the team is debugging a different one.
Generated advice says "version your mappers" and stops, which produces the sprawl without the
discipline that makes versioning worth anything.

❌ Create a version per edit and leave the previous ones in place indefinitely.
✅ One active version, an explicit reason for any second, and a scheduled review that retires
the rest. Confirm which version is active before debugging anything — a disproportionate
share of "the mapper is broken" turns out to be an edit applied to a version that is not
running.

## Anti-Pattern 7: Auditing the mappers that fail and ignoring the ones nobody calls

The inverse problem, skipped because it produces no incidents. A mapper with no callers still
appears in every audit, still has to be reviewed when its object changes, and still has to be
migrated at every runtime change. Its entire cost is in the maintenance tail.

❌ Audit only what is failing.
✅ Keep the inventory in both directions — which fields each mapper reads, and which
components call each mapper — and treat a caller-less mapper as a finding. Confirm before
deleting: callers can be in Apex or in a custom LWC rather than in an OmniScript, and those
are exactly the ones a designer-only search misses.
