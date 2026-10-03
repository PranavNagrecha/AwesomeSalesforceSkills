"""Whole-tree manifest check for the build-level manifest (read-only)."""
import os, re, sys, glob
import xml.etree.ElementTree as ET
NS = "{http://soap.sforce.com/2006/04/metadata}"
def parse_pkg(path):
    out = {}
    for t in ET.parse(path).getroot().findall(NS + "types"):
        n = t.find(NS + "name").text
        out.setdefault(n, set()).update(m.text for m in t.findall(NS + "members"))
    return out
manifest = parse_pkg("artefacts/M4-S04/package.xml")
SUF = {"businessProcess": "BusinessProcess", "field": "CustomField", "recordType": "RecordType",
       "standardValueSet": "StandardValueSet", "layout": "Layout", "customPermission": "CustomPermission",
       "permissionset": "PermissionSet", "profile": "Profile", "validationRule": "ValidationRule",
       "pathAssistant": "PathAssistant", "settings": "Settings", "emailFolder": "EmailFolder",
       "email": "EmailTemplate", "approvalProcess": "ApprovalProcess", "workflow": "Workflow",
       "flexipage": "FlexiPage", "dashboardFolder": "Dashboard", "dashboard": "Dashboard",
       "group": "Group", "reportType": "ReportType", "reportFolder": "Report", "report": "Report",
       "object": "CustomObject"}
derived = {}; excluded = []; sibling = 0; unclassified = []
def add(t, m): derived.setdefault(t, set()).add(m)
for root, _, files in os.walk("artefacts"):
    for f in files:
        p = os.path.join(root, f); rel = p
        parts = rel.split("/")
        step = parts[1]
        if step == "M4-S04" or f == "package.xml" or f.endswith((".md", ".yaml")):
            excluded.append(rel); continue
        if "/lwc/" in rel:
            add("LightningComponentBundle", parts[parts.index("lwc") + 1]); continue
        if "/classes/" in rel:
            if f.endswith(".cls"): add("ApexClass", f[:-4])
            else: sibling += 1
            continue
        if f.endswith(".email"):
            sibling += 1; continue  # body file; member comes from -meta.xml
        m = re.match(r"^(.*)\.([A-Za-z]+)-meta\.xml$", f)
        if not m: unclassified.append(rel); continue
        name, suf = m.groups()
        if suf not in SUF: unclassified.append(rel); continue
        t = SUF[suf]
        if suf in ("businessProcess", "field", "recordType", "validationRule"):
            obj = parts[parts.index("objects") + 1]; name = obj + "." + name
        elif suf == "email":
            name = parts[-2] + "/" + name
        elif suf in ("dashboard", "report"):
            name = parts[-2] + "/" + name
        elif suf == "workflow": pass  # Opportunity.workflow -> Workflow:Opportunity
        add(t, name)
# Opportunity.object-meta.xml and Opportunity.workflow -> members Opportunity; approvalProcess file is Opportunity.Discount_Approval
for t in derived:
    pass
fails = []
for t, ms in sorted(derived.items()):
    for m in sorted(ms):
        if m not in manifest.get(t, set()) and "*" not in manifest.get(t, set()):
            fails.append(f"file->manifest: {t}:{m} has a file but no covering member")
for t, ms in sorted(manifest.items()):
    for m in sorted(ms):
        if m == "*": continue
        if m not in derived.get(t, set()):
            fails.append(f"manifest->file: {t}:{m} has no file under any step's artefacts/")
# cross-check against union of step manifests
union = {}
for p in glob.glob("artefacts/*/package.xml"):
    if "M4-S04" in p: continue
    for t, ms in parse_pkg(p).items(): union.setdefault(t, set()).update(ms)
for t, ms in union.items():
    for m in ms - manifest.get(t, set()):
        fails.append(f"union: {t}:{m} in a step manifest but not in the build-level manifest")
print("=== Manifest types/members ===")
for t, ms in sorted(manifest.items()): print(f"  {t}: {sorted(ms)}")
print("types:", len(manifest), "members:", sum(len(v) for v in manifest.values()))
print(f"files excluded (package.xml, docs, M4-S04 own): {len(excluded)}; sibling/body files: {sibling}; unclassified: {len(unclassified)}")
for u in unclassified: print("  UNCLASSIFIED", u)
print("=== File-derived types/members ===")
for t, ms in sorted(derived.items()): print(f"  {t}: {sorted(ms)}")
print("=== Result ===")
for f in fails: print("FAIL", f)
print("manifest check: CONSISTENT" if not fails and not unclassified else "manifest check: INCONSISTENT")
sys.exit(1 if fails or unclassified else 0)
