#!/usr/bin/env python3
"""check_lwc_app_builder_config.py — audit LWC ``*.js-meta.xml`` files for App Builder defects.

Stdlib only. Reads a Salesforce source tree (``--manifest-dir``) and reports the configuration
mistakes that deploy cleanly and then misbehave: a component that never appears, a knob that
goes nowhere, an object scope that scopes nothing, a form factor written with the wrong tag.

Every rule is grounded in the Lightning Web Components Developer Guide; the page slug and
crawled line number are printed with each finding so a reviewer can check the claim.

Rules
-----
ERROR  ``apiVersion`` missing — required from Spring '25 to save changes back to Salesforce
       (create-version-components L796-L798)
ERROR  ``isExposed`` true with an absent or empty ``<targets>`` — both halves are required
       (reference-configuration-tags L18711-L18712)
ERROR  ``targetConfig`` with a missing or empty ``targets`` attribute (targets-lightning-app-page L18966)
ERROR  ``targetConfig targets="X"`` where X is not listed under ``<targets>``
       (targets-lightning-app-page L18966; targets-lightning-community-default L18769)
ERROR  ``property type="X"`` where X is outside the documented type set for that target
       (targets-lightning-record-page L19351-L19353; targets-lightning-community-default L18775-L18779;
       targets-lightning-static-email L18870-L18876; use-config-for-app-builder-tips L9908)
ERROR  a ``property name`` with no matching ``@api`` field in the bundle's JavaScript
       (targets-lightning-app-page L18968, L18971)
ERROR  ``<supported formFactor="…"/>`` — the child tag is ``supportedFormFactor`` and the
       attribute is ``type`` (targets-lightning-app-page L18994-L18998)
ERROR  ``<supportedFormFactors>`` at the bundle root instead of inside a ``targetConfig``
       (targets-lightning-app-page L18993; use-config-form-factors L9793)
ERROR  ``datasource="apex://Class"`` naming a class absent from the tree — downgraded to
       ADVISORY when the tree contains no ``.cls`` files at all (targets-lightning-record-page L19355)
WARN   ``<objects>`` inside a ``targetConfig`` that is not configured for ``lightning__RecordPage``
       (targets-lightning-record-page L19363)
WARN   a ``lightning__RecordPage`` ``targetConfig`` with no ``<objects>`` — the component then
       supports every supported object (targets-lightning-record-page L19363)
WARN   ``<objects>`` specified more than once in one ``targetConfig`` (targets-lightning-record-page L19364)
WARN   ``supportedFormFactor type="Small"`` on a bundle whose template uses ``lightning-datatable``
       or ``lightning-tree-grid`` — neither is supported on mobile (data-table-vs-tree-grid L5600)
WARN   ``supportedFormFactor type="Small"`` in a ``lightning__HomePage`` targetConfig — Home pages
       support only the Large form factor (use-config-form-factors L9795)
WARN   ``supportedFormFactor type="Small"`` in a ``lightning__RecordAction`` targetConfig — not
       supported, LWC quick actions do not appear in the mobile app (targets-lightning-record-action L19313)
WARN   ``property`` or ``supportedFormFactors`` under a ``lightning__Tab`` targetConfig — the target
       supports neither tag (use-config-custom-tab L7987)
WARN   ``property`` under a ``lightning__RecordAction`` / ``lightning__GlobalAction`` targetConfig —
       neither target supports component properties (L19307, L19170)
WARN   ``required="true"`` with no ``default`` — the component shows as invalid when added
       (use-config-for-app-builder-tips L9899)
WARN   ``min`` / ``max`` on a property whose type is not ``Integer`` (targets-lightning-app-page L18980-L18981)
WARN   ``datasource`` or ``placeholder`` on a property whose type is not ``String``
       (targets-lightning-app-page L18976, L18982)
WARN   missing ``<masterLabel>`` — builders show the bundle API name instead (reference-configuration-tags L18714)

Exit codes
----------
1  ``--manifest-dir`` does not exist, or any ERROR was reported
0  otherwise (WARNs alone do not fail unless ``--strict`` promotes them; ADVISORY never fails)

Usage
-----
    python3 check_lwc_app_builder_config.py --manifest-dir force-app/main/default
    python3 check_lwc_app_builder_config.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"

COMMON_TYPES = {"Boolean", "Integer", "String"}

# The documented `type` set is per target, not global. Targets absent from this map
# (Agentforce, PropertyEditor, Snapin, …) accept types this checker does not model,
# so their properties are skipped rather than guessed at.
TYPES_BY_TARGET = {
    "lightning__RecordPage": COMMON_TYPES,
    "lightning__AppPage": COMMON_TYPES,
    "lightning__HomePage": COMMON_TYPES,
    "lightning__Inbox": COMMON_TYPES,
    "lightning__UtilityBar": COMMON_TYPES,
    "lightning__VoiceExtension": COMMON_TYPES,
    "lightningCommunity__Default": COMMON_TYPES | {"Color", "ContentReference"},
    "lightningStatic__Email": COMMON_TYPES | {"Color", "HorizontalAlignment", "VerticalAlignment"},
    "lightning__FlowScreen": COMMON_TYPES | {"Double", "Date", "DateTime"},
    "lightning__FlowAction": COMMON_TYPES | {"Double", "Date", "DateTime"},
    "analytics__Dashboard": COMMON_TYPES | {"Measure", "Dimension"},
    "lightning__EnablementProgram": COMMON_TYPES | {"Multilinetext"},
}

# Type values that name something outside the fixed enum and must not be flagged.
DYNAMIC_TYPE_PREFIXES = ("apex://", "@salesforce/schema/")

NO_PROPERTY_TARGETS = {
    "lightning__Tab": "use-config-custom-tab L7987",
    "lightning__RecordAction": "targets-lightning-record-action L19307",
    "lightning__GlobalAction": "targets-lightning-global-action L19170",
    "lightningCommunity__Page": "targets-lightning-community-page L18812",
}

MOBILE_UNSUPPORTED_TAGS = ("lightning-datatable", "lightning-tree-grid")

API_DECORATED = re.compile(r"@api\s+(?:get\s+|set\s+|static\s+)*([A-Za-z_$][\w$]*)")


class Finding:
    __slots__ = ("level", "where", "message")

    def __init__(self, level: str, where: str, message: str) -> None:
        self.level = level
        self.where = where
        self.message = message

    def render(self) -> str:
        return f"{self.level}: {self.where}: {self.message}"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _strip_ns(tag: str) -> str:
    if tag.startswith("{") and "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _child(elem, name):
    """Find one child by local name. Never use `a.find(x) or a.find(y)` — a leaf
    Element is falsy, so `or` silently discards a real match."""
    if elem is None:
        return None
    found = elem.find(f"{NS}{name}")
    if found is None:
        found = elem.find(name)
    return found


def _children(elem, name) -> list:
    if elem is None:
        return []
    out = list(elem.findall(f"{NS}{name}"))
    if not out:
        out = list(elem.findall(name))
    return out


def _text(elem) -> str:
    return (elem.text or "").strip() if elem is not None else ""


def _line_of(raw: str, needle: str) -> str:
    idx = raw.find(needle)
    return f":{raw.count(chr(10), 0, idx) + 1}" if idx >= 0 else ""


def _targets_of(target_config) -> list[str]:
    return [t.strip() for t in (target_config.attrib.get("targets") or "").split(",") if t.strip()]


# ------------------------------------------------------------------- discovery --

def find_bundles(root: Path) -> list[Path]:
    """A bundle is any directory containing a *.js-meta.xml file."""
    return sorted({p.parent for p in root.rglob("*.js-meta.xml")})


def apex_class_names(root: Path) -> set[str]:
    return {p.name[: -len(".cls")] for p in root.rglob("*.cls")}


def api_properties(bundle: Path) -> set[str]:
    names: set[str] = set()
    for js in bundle.glob("*.js"):
        if js.name.endswith((".test.js", ".spec.js")):
            continue
        names.update(API_DECORATED.findall(_read(js)))
    return names


def template_text(bundle: Path) -> str:
    return "".join(_read(p) for p in bundle.glob("*.html"))


# ----------------------------------------------------------------------- rules --

def check_bundle(meta_path: Path, apex_classes: set[str], any_apex: bool) -> list[Finding]:
    findings: list[Finding] = []
    raw = _read(meta_path)
    rel = str(meta_path)

    try:
        root = ET.fromstring(raw.encode("utf-8"))
    except ET.ParseError as exc:
        return [Finding("ERROR", rel, f"XML parse error: {exc}")]

    if _strip_ns(root.tag) != "LightningComponentBundle":
        return []

    bundle_dir = meta_path.parent
    declared_api = api_properties(bundle_dir)
    has_js = any(
        not p.name.endswith((".test.js", ".spec.js")) for p in bundle_dir.glob("*.js")
    )
    html = template_text(bundle_dir)

    # --- apiVersion ---------------------------------------------------------
    if not _text(_child(root, "apiVersion")):
        findings.append(Finding(
            "ERROR", rel,
            "no <apiVersion> — from Spring '25 a component must set one to save changes back "
            "to Salesforce (create-version-components L796-L798)",
        ))

    # --- masterLabel --------------------------------------------------------
    if not _text(_child(root, "masterLabel")):
        findings.append(Finding(
            "WARN", rel,
            "no <masterLabel> — builders and the Setup list show the bundle API name instead of a "
            "friendly title (reference-configuration-tags L18714)",
        ))

    # --- isExposed vs targets ----------------------------------------------
    exposed = _text(_child(root, "isExposed")).lower() == "true"
    targets_el = _child(root, "targets")
    declared_targets = [_text(t) for t in _children(targets_el, "target") if _text(t)]

    if exposed and not declared_targets:
        findings.append(Finding(
            "ERROR", rel,
            "<isExposed> is true but <targets> is absent or empty; a builder needs both "
            "(reference-configuration-tags L18711-L18712)",
        ))
    if declared_targets and not exposed:
        findings.append(Finding(
            "ERROR", rel,
            f"<targets> lists {len(declared_targets)} surface(s) but <isExposed> is not true; the "
            "component will not appear in any builder (reference-configuration-tags L18711)",
        ))

    # --- supportedFormFactors at the bundle root ---------------------------
    if _child(root, "supportedFormFactors") is not None:
        findings.append(Finding(
            "ERROR", rel + _line_of(raw, "<supportedFormFactors"),
            "<supportedFormFactors> is declared at the bundle root; it must be specified inside a "
            "<targetConfig> (targets-lightning-app-page L18993; use-config-form-factors L9793)",
        ))

    # --- the wrong form-factor tag or attribute, anywhere in the file ------
    if re.search(r"<supported\s+[^>]*formFactor\s*=", raw) or re.search(r"<supported\s", raw):
        findings.append(Finding(
            "ERROR", rel + _line_of(raw, "<supported "),
            'found a <supported …> element: the child tag is <supportedFormFactor> and its '
            'attribute is type="Large"|"Small", not formFactor '
            "(targets-lightning-app-page L18994-L18998)",
        ))
    for bad in re.finditer(r"<supportedFormFactor\s+[^>]*formFactor\s*=", raw):
        findings.append(Finding(
            "ERROR", rel + _line_of(raw, bad.group(0)),
            'supportedFormFactor uses the attribute type="Large"|"Small", not formFactor '
            "(targets-lightning-app-page L18996-L18998)",
        ))

    # --- targetConfigs ------------------------------------------------------
    target_configs_el = _child(root, "targetConfigs")
    configured: set[str] = set()

    for tc in _children(target_configs_el, "targetConfig"):
        tc_targets = _targets_of(tc)
        label = ",".join(tc_targets) if tc_targets else "?"
        where = rel + _line_of(raw, f'targets="{tc.attrib.get("targets", "")}"')

        if not tc_targets:
            findings.append(Finding(
                "ERROR", where,
                "<targetConfig> has no targets attribute; it is required and must name page types "
                "listed under <targets> (targets-lightning-app-page L18966)",
            ))
            continue

        configured.update(tc_targets)
        for t in tc_targets:
            if t not in declared_targets:
                findings.append(Finding(
                    "ERROR", where,
                    f"targetConfig targets '{t}' which is not listed under <targets>; the attribute "
                    "value must match one or more declared page types "
                    "(targets-lightning-app-page L18966)",
                ))

        # ---- objects scoping ----
        objects_blocks = _children(tc, "objects")
        is_record_page = "lightning__RecordPage" in tc_targets
        if objects_blocks and not is_record_page:
            findings.append(Finding(
                "WARN", where,
                f"<objects> inside targetConfig '{label}' scopes nothing; the tag set works only "
                "inside a targetConfig configured for lightning__RecordPage "
                "(targets-lightning-record-page L19363)",
            ))
        if len(objects_blocks) > 1:
            findings.append(Finding(
                "WARN", where,
                "<objects> is specified more than once; specify the tag set only one time inside a "
                "targetConfig (targets-lightning-record-page L19364)",
            ))
        if is_record_page and not objects_blocks:
            findings.append(Finding(
                "WARN", where,
                "record-page targetConfig has no <objects>; without it the component supports all "
                "supported objects and admins can drop it anywhere "
                "(targets-lightning-record-page L19363)",
            ))

        # ---- targets that accept no properties / no form factors ----
        props = _children(tc, "property")
        form_factor_blocks = _children(tc, "supportedFormFactors")
        for t in tc_targets:
            if t in NO_PROPERTY_TARGETS and props:
                findings.append(Finding(
                    "WARN", where,
                    f"targetConfig '{label}' declares {len(props)} property tag(s) but "
                    f"{t} does not support component properties ({NO_PROPERTY_TARGETS[t]})",
                ))
            if t == "lightning__Tab" and form_factor_blocks:
                findings.append(Finding(
                    "WARN", where,
                    "lightning__Tab supports neither the property nor the supportedFormFactor tags "
                    "(use-config-custom-tab L7987)",
                ))

        # ---- form factors ----
        for ffs in form_factor_blocks:
            for ff in _children(ffs, "supportedFormFactor"):
                kind = (ff.attrib.get("type") or "").strip()
                if kind and kind not in ("Large", "Small"):
                    findings.append(Finding(
                        "ERROR", where,
                        f"supportedFormFactor type='{kind}' is not a documented value; valid values "
                        "are Large (desktop) and Small (phone) "
                        "(targets-lightning-app-page L18997-L18998)",
                    ))
                if kind != "Small":
                    continue
                if "lightning__HomePage" in tc_targets:
                    findings.append(Finding(
                        "WARN", where,
                        "Small form factor on a lightning__HomePage targetConfig; Home pages support "
                        "only the Large form factor (use-config-form-factors L9795)",
                    ))
                if "lightning__RecordAction" in tc_targets:
                    findings.append(Finding(
                        "WARN", where,
                        "Small is not supported for lightning__RecordAction because LWC quick actions "
                        "do not appear in the Salesforce mobile app "
                        "(targets-lightning-record-action L19313)",
                    ))
                for tag in MOBILE_UNSUPPORTED_TAGS:
                    if tag in html:
                        findings.append(Finding(
                            "WARN", where,
                            f"targetConfig '{label}' declares the Small form factor but the template "
                            f"uses <{tag}>, which is not supported on mobile devices "
                            "(data-table-vs-tree-grid L5600)",
                        ))

        # ---- properties ----
        allowed_sets = [TYPES_BY_TARGET[t] for t in tc_targets if t in TYPES_BY_TARGET]
        allowed = set.intersection(*allowed_sets) if allowed_sets else None

        for prop in props:
            name = (prop.attrib.get("name") or "").strip()
            ptype = (prop.attrib.get("type") or "").strip()
            pwhere = rel + _line_of(raw, f'name="{name}"') if name else where

            if not name:
                findings.append(Finding(
                    "ERROR", pwhere,
                    f"<property> in targetConfig '{label}' has no name attribute; it is required and "
                    "must match the JavaScript property (targets-lightning-app-page L18971)",
                ))
                continue

            # type enum, per target
            if (
                allowed is not None
                and ptype
                and ptype not in allowed
                and not ptype.startswith(DYNAMIC_TYPE_PREFIXES)
                and "__" not in ptype  # a custom Lightning type such as c__layoutType
            ):
                findings.append(Finding(
                    "ERROR", pwhere,
                    f"property '{name}' type='{ptype}' is not documented for targetConfig '{label}'; "
                    f"the documented set there is {sorted(allowed)} "
                    "(targets-lightning-record-page L19351-L19353; "
                    "targets-lightning-community-default L18775-L18779; "
                    "use-config-for-app-builder-tips L9908)",
                ))

            # every property name needs an @api field
            if has_js and name not in declared_api:
                findings.append(Finding(
                    "ERROR", pwhere,
                    f"property '{name}' has no matching @api field in the bundle's JavaScript; the "
                    "name must match the property in the component's JavaScript class, which the "
                    "author declares with @api (targets-lightning-app-page L18968, L18971)",
                ))

            # required without a default
            if (prop.attrib.get("required") or "").strip().lower() == "true" and not prop.attrib.get("default"):
                findings.append(Finding(
                    "WARN", pwhere,
                    f"property '{name}' is required but has no default; a component with required "
                    "properties and no defaults appears invalid when added in App Builder "
                    "(use-config-for-app-builder-tips L9899)",
                ))

            # min/max are Integer-only, datasource/placeholder are String-only
            if ptype and ptype != "Integer":
                for attr in ("min", "max"):
                    if prop.attrib.get(attr) is not None:
                        findings.append(Finding(
                            "WARN", pwhere,
                            f"property '{name}' sets {attr} but its type is '{ptype}'; "
                            f"{attr} applies to attributes of type Integer "
                            "(targets-lightning-app-page L18980-L18981)",
                        ))
            if ptype and ptype != "String":
                for attr in ("datasource", "placeholder"):
                    if prop.attrib.get(attr) is not None:
                        findings.append(Finding(
                            "WARN", pwhere,
                            f"property '{name}' sets {attr} but its type is '{ptype}'; "
                            f"{attr} is supported only when the type attribute is String "
                            "(targets-lightning-app-page L18976, L18982)",
                        ))

            # apex:// datasource must resolve to a class in the tree
            datasource = (prop.attrib.get("datasource") or "").strip()
            if datasource.startswith("apex://"):
                ref = datasource[len("apex://"):].strip()
                cls = ref.split(".")[-1]
                if cls not in apex_classes:
                    level = "ERROR" if any_apex else "ADVISORY"
                    tail = (
                        "no such .cls in the tree"
                        if any_apex
                        else "the tree contains no Apex classes, so this cannot be resolved here"
                    )
                    findings.append(Finding(
                        level, pwhere,
                        f"property '{name}' uses datasource='{datasource}' but {tail}; the class must "
                        "extend VisualEditor.DynamicPickList and be deployed with the bundle "
                        "(targets-lightning-record-page L19355)",
                    ))

    return findings


# ------------------------------------------------------------------------ main --

def run(root: Path) -> tuple[list[Finding], int]:
    apex = apex_class_names(root)
    any_apex = bool(apex)
    findings: list[Finding] = []
    metas = sorted(root.rglob("*.js-meta.xml"))
    for meta in metas:
        findings.extend(check_bundle(meta, apex, any_apex))
    return findings, len(metas)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit LWC js-meta.xml files for App Builder and Experience Builder configuration "
            "defects (exposure, target/targetConfig coherence, property types, orphan design "
            "attributes, object scoping, form factors, Apex datasources)."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree (for example force-app/main/default).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote every WARN to an ERROR (use in CI). ADVISORY findings are never promoted.",
    )
    args = parser.parse_args()

    root = Path(args.manifest_dir)
    if not root.is_dir():
        print(f"ERROR: --manifest-dir not found: {root}")
        return 1

    findings, scanned = run(root)

    if scanned == 0:
        print(f"WARN: {root}: no *.js-meta.xml files found — nothing to check.")
        return 0

    if args.strict:
        for finding in findings:
            if finding.level == "WARN":
                finding.level = "ERROR"

    order = {"ERROR": 0, "WARN": 1, "ADVISORY": 2}
    for finding in sorted(findings, key=lambda f: (order.get(f.level, 3), f.where)):
        print(finding.render())

    errors = sum(1 for f in findings if f.level == "ERROR")
    warns = sum(1 for f in findings if f.level == "WARN")
    advisories = sum(1 for f in findings if f.level == "ADVISORY")
    print(
        f"\n{scanned} configuration file(s) scanned — "
        f"{errors} ERROR, {warns} WARN, {advisories} ADVISORY"
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
