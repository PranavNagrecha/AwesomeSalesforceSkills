#!/usr/bin/env python3
"""Checker script for the Multi-Language and Translation skill.

Lints the four translation metadata types against the metadata they claim to
translate, in a Salesforce DX (or MDAPI) source tree. Everything it enforces is
grounded in the Metadata API Developer Guide; the citation is printed with the
finding so a reviewer can check it.

Check families
--------------
1. File naming and locale codes
     - ``*.objectTranslation`` must be named ``<Object>-<lang>``      ERROR
       ("customObjectName__c-lang.objectTranslation", api_meta.txt:45899-45901)
     - ``*.globalValueSetTranslation`` must be ``<ValueSet>-<lang>``  ERROR
       (api_meta.txt:79446-79448)
     - ``*.standardValueSetTranslation`` must be ``<ValueSet>-<lang>`` ERROR
       (api_meta.txt:130842-130844)
     - ``*.translation`` must be a bare locale code                   ERROR
       (api_meta.txt:135574-135575)
     - the locale must appear in the guide's Language lists           ERROR
       (api_meta.txt:135356-135572)

2. The locale must actually be switched on
     - ``settings/Language.settings`` with enableTranslationWorkbench
       false or absent, while translation files exist                 ERROR
       (default is false, api_meta.txt:120965-120967)
     - an end-user locale without enableEndUserLanguages              ERROR
     - a platform-only locale without enablePlatformLanguages         ERROR
       (setting platform true also sets end-user true,
        api_meta.txt:120961-120964)
     - ``--active-locales`` given and a file's locale is not in it     ERROR

3. Referential integrity against the translated metadata
     - <fields><name> not defined on the object                        ERROR
     - <picklistValues><masterLabel> not a value of that field         ERROR
     - <recordTypes>/<validationRules>/<webLinks> name not on object   ERROR
     - GlobalValueSetTranslation naming a value set that only exists
       with the ``__gvs`` suffix (api_meta.txt:79419-79421)            ERROR
     - a GlobalValueSetTranslation value not in the value set          ERROR
     - object / value set not present in the tree, so unverifiable     INFO

4. Length ceilings from the field tables
     - field <label> over 40 characters      (api_meta.txt:46000)      ERROR
     - <nameFieldLabel>/<relationshipLabel> over 80
       (api_meta.txt:45941, api_meta.txt:46024-46027)                  ERROR
     - section / record type / web link / quick action / custom label
       <label> over 765 (api_meta.txt:46069, 46213, 46256-46257,
       46203, 135934-135935)                                          ERROR

5. Blank and untranslated content
     - an empty translated element                                     WARN
       ("If a translation label is left blank, it's skipped during
        deployment, and no error will be shown", api_meta.txt:135789)
     - a <translation> whose only content is an XML comment, the
       guide's own untranslated marker (api_meta.txt:79475-79476)      WARN
     - <flowDefinitions> using <name> instead of <fullName>            ERROR
       (api_meta.txt:136015)
     - coverage: fields and picklist values on the object that this
       objectTranslation never mentions                                INFO

Exit code: 1 if any ERROR is reported (or the tree is unreadable), else 0.
WARN and INFO are printed but do not fail the run unless --fail-on-warn.

Usage:
    python3 check_multi_language_and_translation.py --manifest-dir force-app/main/default
    python3 check_multi_language_and_translation.py --manifest-dir . \
        --active-locales de,fr --fail-on-warn
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

MDNS = "{http://soap.sforce.com/2006/04/metadata}"
ERROR, WARN, INFO = "ERROR", "WARN", "INFO"

# Metadata API Developer Guide, Translations > Language (api_meta.txt:135356-135572).
FULLY_SUPPORTED = {
    "zh_CN", "zh_TW", "da", "nl_NL", "en_US", "fi", "fr", "de", "it", "ja",
    "ko", "no", "pt_BR", "ru", "es", "es_MX", "sv", "th",
}
END_USER = {
    "ar", "bg", "hr", "cs", "en_GB", "el", "iw", "hu", "in", "pl", "pt_PT",
    "ro", "sk", "sl", "tr", "uk", "vi",
}
PLATFORM_ONLY = {
    "sq", "af", "am", "ar_DZ", "ar_BH", "ar_EG", "ar_IQ", "ar_JO", "ar_KW",
    "ar_LB", "ar_LY", "ar_MA", "ar_OM", "ar_QA", "ar_SA", "ar_SD", "ar_SY",
    "ar_TN", "ar_AE", "ar_YE", "hy", "eu", "bs", "bn", "my", "ca", "zh_HK",
    "zh_SG", "zh_MY", "nl_BE", "en_AU", "en_BE", "en_CA", "en_CY", "en_DE",
    "en_HK", "en_IN", "en_IE", "en_IL", "en_MY", "en_MT", "en_NL", "en_NZ",
    "en_PH", "en_SG", "en_ZA", "en_AE", "et", "fa", "fr_BE", "fr_CA", "fr_LU",
    "fr_MA", "fr_CH", "ka", "de_AT", "de_BE", "de_LU", "de_CH", "el_CY", "kl",
    "gu", "haw", "ht", "hi", "hmn", "is", "ga", "it_CH", "kn", "kk", "km",
    "lv", "lt", "lb", "mk", "ms", "ml", "mt", "mr", "sh_ME", "pa", "ro_MD",
    "rm", "ru_AM", "ru_BY", "ru_KZ", "ru_KG", "ru_LT", "ru_MD", "ru_PL",
    "ru_UA", "sm", "sr", "sh", "es_AR", "es_BO", "es_CL", "es_CO", "es_CR",
    "es_DO", "es_EC", "es_SV", "es_GT", "es_HN", "es_NI", "es_PA", "es_PY",
    "es_PE", "es_PR", "es_US", "es_UY", "es_VE", "sw", "tl", "ta", "mi", "te",
    "ur", "cy", "xh", "ji", "zu",
}
ALL_LOCALES = FULLY_SUPPORTED | END_USER | PLATFORM_ONLY

# Right-to-left locales the guide flags with an explicit warning before you
# enable them (api_meta.txt:135407 for ar/iw, api_meta.txt:135569 for ur).
RTL_FLAGGED = {"ar", "iw", "ur"} | {c for c in PLATFORM_ONLY if c.startswith("ar_")}

# Length ceilings, all from the CustomObjectTranslation and Translations field
# tables. (tag, parent kind) -> (max, citation)
LABEL_MAX = {
    "field_label": (40, "api_meta.txt:46000"),
    "name_field_label": (80, "api_meta.txt:45941"),
    "relationship_label": (80, "api_meta.txt:46024-46027"),
    "section_label": (765, "api_meta.txt:46069"),
    "record_type_label": (765, "api_meta.txt:46213"),
    "web_link_label": (765, "api_meta.txt:46256-46257"),
    "quick_action_label": (765, "api_meta.txt:46203"),
    "custom_label_label": (765, "api_meta.txt:135934-135935"),
    "custom_app_label": (765, "api_meta.txt:135923-135924"),
}

OBJ_TRANSLATION_SUFFIXES = (".objectTranslation-meta.xml", ".objectTranslation")
TRANSLATION_SUFFIXES = (".translation-meta.xml", ".translation")
GVS_TRANSLATION_SUFFIXES = (
    ".globalValueSetTranslation-meta.xml", ".globalValueSetTranslation",
)
SVS_TRANSLATION_SUFFIXES = (
    ".standardValueSetTranslation-meta.xml", ".standardValueSetTranslation",
)


class Finding:
    __slots__ = ("severity", "where", "message")

    def __init__(self, severity: str, where: str, message: str) -> None:
        self.severity = severity
        self.where = where
        self.message = message

    def __str__(self) -> str:
        return f"{self.severity}: {self.where}: {self.message}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Lint Salesforce translation metadata against what it translates."
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root directory of the metadata tree (default: current directory).",
    )
    parser.add_argument(
        "--active-locales",
        default="",
        help="Comma-separated locale codes this org has active in Translation "
        "Workbench. When given, a translation file for any other locale is an "
        "ERROR. When omitted, the check falls back to settings/Language.settings.",
    )
    parser.add_argument(
        "--fail-on-warn",
        action="store_true",
        help="Exit 1 on WARN findings as well as ERROR findings.",
    )
    return parser.parse_args()


# --------------------------------------------------------------------------
# XML helpers. Never rely on the truthiness of an Element: a leaf Element with
# no children is falsy, so `el.find(a) or el.find(b)` silently discards a real
# match. Every lookup below tests `is not None`.
# --------------------------------------------------------------------------

def child(element: ET.Element, tag: str) -> ET.Element | None:
    for candidate in (f"{MDNS}{tag}", tag):
        found = element.find(candidate)
        if found is not None:
            return found
    return None


def child_text(element: ET.Element, tag: str) -> str | None:
    found = child(element, tag)
    if found is None:
        return None
    return (found.text or "").strip()


def children(element: ET.Element, tag: str) -> list[ET.Element]:
    found = element.findall(f"{MDNS}{tag}")
    if found:
        return found
    return element.findall(tag)


def parse_xml(path: Path, rel: str, findings: list[Finding]) -> ET.Element | None:
    try:
        return ET.parse(str(path)).getroot()
    except (ET.ParseError, OSError) as exc:
        findings.append(Finding(ERROR, rel, f"could not parse as XML: {exc}"))
        return None


def has_only_comment(element: ET.Element) -> bool:
    """True when <translation><!-- Foo --></translation>: the guide's own
    marker for an untranslated value (api_meta.txt:79475-79476). ElementTree
    drops comments, so a comment-only element reads as empty text with no
    children; the raw-text scan in ``comment_only_lines`` catches the rest.
    """
    return (element.text or "").strip() == "" and len(list(element)) == 0


def files_with_suffix(root: Path, suffixes: tuple[str, ...]) -> list[Path]:
    out: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        for suffix in suffixes:
            if path.name.endswith(suffix):
                out.append(path)
                break
    return out


def strip_suffix(name: str, suffixes: tuple[str, ...]) -> str:
    for suffix in suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return name


# --------------------------------------------------------------------------
# Build a picture of the metadata being translated.
# --------------------------------------------------------------------------

class ObjectModel:
    """Fields, picklist values, record types, validation rules and web links
    for one sObject, gathered from whichever layout the tree uses."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.fields: dict[str, dict] = {}   # api name -> {"values": set, "value_set": str|None}
        self.record_types: set[str] = set()
        self.validation_rules: set[str] = set()
        self.web_links: set[str] = set()
        self.sharing_reasons: set[str] = set()


def read_field_element(field_el: ET.Element, model: ObjectModel) -> None:
    api_name = child_text(field_el, "fullName")
    if not api_name:
        return
    values: set[str] = set()
    value_set_name: str | None = None
    value_set = child(field_el, "valueSet")
    if value_set is not None:
        value_set_name = child_text(value_set, "valueSetName") or None
        definition = child(value_set, "valueSetDefinition")
        if definition is not None:
            for value in children(definition, "value"):
                full = child_text(value, "fullName")
                label = child_text(value, "label")
                # CustomValue: "If you don't specify the label when creating a
                # value it defaults to the API name" (api_meta.txt CustomValue
                # field table). masterLabel in a translation matches the label.
                for candidate in (label, full):
                    if candidate:
                        values.add(candidate)
    # Pre-38.0 shape, still present in older trees.
    for legacy in children(field_el, "picklist"):
        for value in children(legacy, "picklistValues"):
            full = child_text(value, "fullName")
            if full:
                values.add(full)
    model.fields[api_name] = {"values": values, "value_set": value_set_name}


def collect_objects(root: Path, findings: list[Finding]) -> dict[str, ObjectModel]:
    models: dict[str, ObjectModel] = {}

    def model_for(name: str) -> ObjectModel:
        if name not in models:
            models[name] = ObjectModel(name)
        return models[name]

    # DX decomposed: objects/<Name>/<Name>.object-meta.xml + fields/*.field-meta.xml
    # MDAPI: objects/<Name>.object
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        if name.endswith(".object-meta.xml"):
            obj = name[: -len(".object-meta.xml")]
        elif name.endswith(".object"):
            obj = name[: -len(".object")]
        elif name.endswith(".field-meta.xml"):
            # .../objects/<Object>/fields/<Field>.field-meta.xml
            parts = path.parts
            if len(parts) < 3 or parts[-2] != "fields":
                continue
            obj = parts[-3]
            element = parse_xml(path, str(path), findings)
            if element is not None:
                read_field_element(element, model_for(obj))
            continue
        elif name.endswith(".recordType-meta.xml"):
            parts = path.parts
            if len(parts) >= 3 and parts[-2] == "recordTypes":
                model_for(parts[-3]).record_types.add(name[: -len(".recordType-meta.xml")])
            continue
        elif name.endswith(".validationRule-meta.xml"):
            parts = path.parts
            if len(parts) >= 3 and parts[-2] == "validationRules":
                model_for(parts[-3]).validation_rules.add(
                    name[: -len(".validationRule-meta.xml")]
                )
            continue
        elif name.endswith(".webLink-meta.xml"):
            parts = path.parts
            if len(parts) >= 3 and parts[-2] == "webLinks":
                model_for(parts[-3]).web_links.add(name[: -len(".webLink-meta.xml")])
            continue
        else:
            continue

        element = parse_xml(path, str(path), findings)
        if element is None:
            continue
        model = model_for(obj)
        for field_el in children(element, "fields"):
            read_field_element(field_el, model)
        for rt in children(element, "recordTypes"):
            value = child_text(rt, "fullName")
            if value:
                model.record_types.add(value)
        for vr in children(element, "validationRules"):
            value = child_text(vr, "fullName")
            if value:
                model.validation_rules.add(value)
        for wl in children(element, "webLinks"):
            value = child_text(wl, "fullName")
            if value:
                model.web_links.add(value)
        for sr in children(element, "sharingReasons"):
            value = child_text(sr, "fullName")
            if value:
                model.sharing_reasons.add(value)

    return models


def collect_global_value_sets(root: Path, findings: list[Finding]) -> dict[str, set[str]]:
    """value set developer name -> set of acceptable masterLabel strings."""
    out: dict[str, set[str]] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        name = path.name
        for suffix in (".globalValueSet-meta.xml", ".globalValueSet"):
            if not name.endswith(suffix):
                continue
            dev_name = name[: -len(suffix)]
            element = parse_xml(path, str(path), findings)
            if element is None:
                break
            labels: set[str] = set()
            for value in children(element, "customValue"):
                for tag in ("label", "fullName"):
                    text = child_text(value, tag)
                    if text:
                        labels.add(text)
            out[dev_name] = labels
            break
    return out


def read_language_settings(root: Path, findings: list[Finding]) -> dict[str, bool] | None:
    for path in sorted(root.rglob("*")):
        if path.is_file() and path.name in (
            "Language.settings-meta.xml", "Language.settings"
        ):
            element = parse_xml(path, str(path), findings)
            if element is None:
                return None
            flags: dict[str, bool] = {}
            for flag in (
                "enableTranslationWorkbench",
                "enableEndUserLanguages",
                "enablePlatformLanguages",
                "enableDataTranslation",
                "useLanguageFallback",
            ):
                text = child_text(element, flag)
                if text is not None:
                    flags[flag] = text.lower() == "true"
            return flags
    return None


# --------------------------------------------------------------------------
# Checks.
# --------------------------------------------------------------------------

def check_locale(locale: str, where: str, active: set[str],
                 settings: dict[str, bool] | None, findings: list[Finding]) -> None:
    if locale not in ALL_LOCALES:
        findings.append(
            Finding(
                ERROR,
                where,
                f"'{locale}' is not a Salesforce language code. The fully "
                "supported, end-user and platform-only lists are in the "
                "Metadata API Developer Guide (api_meta.txt:135356-135572). A "
                "file named for an unknown locale deploys nothing.",
            )
        )
        return

    if active and locale not in active:
        findings.append(
            Finding(
                ERROR,
                where,
                f"locale '{locale}' is not in --active-locales. Translations "
                "for a language that is not active in Translation Workbench "
                "are stored and never displayed (Translation.IsActive, "
                "object_reference.txt:290205-290206).",
            )
        )

    if locale in RTL_FLAGGED:
        findings.append(
            Finding(
                INFO,
                where,
                f"'{locale}' is right-to-left. The guide says to review the "
                "right-to-left language support limitations before enabling it "
                "(api_meta.txt:135407, api_meta.txt:135569); custom LWC and "
                "Experience Cloud templates are not covered by native RTL.",
            )
        )

    if settings is None:
        return

    if not settings.get("enableTranslationWorkbench", False):
        findings.append(
            Finding(
                ERROR,
                where,
                "settings/Language.settings does not set "
                "<enableTranslationWorkbench>true</enableTranslationWorkbench>; "
                "the field defaults to false (api_meta.txt:120965-120967), so "
                "this translation has nothing to attach to.",
            )
        )
    if locale in END_USER and not settings.get("enableEndUserLanguages", False):
        findings.append(
            Finding(
                ERROR,
                where,
                f"'{locale}' is an end-user language but "
                "<enableEndUserLanguages> is not true (default false, "
                "api_meta.txt:120911-120971).",
            )
        )
    if locale in PLATFORM_ONLY and not settings.get("enablePlatformLanguages", False):
        findings.append(
            Finding(
                ERROR,
                where,
                f"'{locale}' is a platform-only language but "
                "<enablePlatformLanguages> is not true. Setting it true also "
                "sets enableEndUserLanguages true (api_meta.txt:120961-120964).",
            )
        )


def check_length(value: str | None, kind: str, where: str,
                 findings: list[Finding]) -> None:
    if not value:
        return
    limit, citation = LABEL_MAX[kind]
    if len(value) > limit:
        findings.append(
            Finding(
                ERROR,
                where,
                f"translated text is {len(value)} characters; the maximum is "
                f"{limit} ({citation}). Translations into German, Finnish and "
                "Hungarian routinely overrun the 40-character field-label cap.",
            )
        )


def check_blank(element: ET.Element, tag: str, where: str,
                findings: list[Finding]) -> None:
    found = child(element, tag)
    if found is None:
        return
    if has_only_comment(found):
        findings.append(
            Finding(
                WARN,
                where,
                f"<{tag}> is empty. A blank translation is skipped during "
                "deployment and no error is shown "
                "(api_meta.txt:135789), so this reads as a delivered "
                "translation and delivers nothing. Remove the element or fill it.",
            )
        )


def check_object_translation(path: Path, root: Path, objects: dict[str, ObjectModel],
                             gvs: dict[str, set[str]], active: set[str],
                             settings: dict[str, bool] | None,
                             findings: list[Finding]) -> None:
    rel = str(path.relative_to(root))
    stem = strip_suffix(path.name, OBJ_TRANSLATION_SUFFIXES)

    if "-" not in stem:
        findings.append(
            Finding(
                ERROR,
                rel,
                f"file name '{stem}' has no '-<lang>' part. The guide requires "
                "customObjectName__c-lang.objectTranslation, e.g. "
                "myCustomObject__c-de.objectTranslation "
                "(api_meta.txt:45899-45901).",
            )
        )
        return
    object_name, _, locale = stem.rpartition("-")
    check_locale(locale, f"{rel} [{locale}]", active, settings, findings)

    element = parse_xml(path, rel, findings)
    if element is None:
        return

    check_length(child_text(element, "nameFieldLabel"), "name_field_label", rel, findings)

    model = objects.get(object_name)
    if model is None:
        findings.append(
            Finding(
                INFO,
                rel,
                f"object '{object_name}' is not in this tree, so field, picklist "
                "and record-type names in this file cannot be verified. Include "
                "the CustomObject in the same retrieve to make this check real.",
            )
        )

    translated_fields: set[str] = set()
    translated_values: dict[str, set[str]] = {}

    for field_el in children(element, "fields"):
        api_name = child_text(field_el, "name")
        where = f"{rel} [fields/{api_name or '?'}]"
        if not api_name:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    "<fields> has no <name>. It is Required and is 'the name of "
                    "the field relative to the custom object; for example, "
                    "MyField__c' (api_meta.txt:46016-46017).",
                )
            )
            continue
        translated_fields.add(api_name)
        check_length(child_text(field_el, "label"), "field_label", where, findings)
        check_length(
            child_text(field_el, "relationshipLabel"), "relationship_label", where, findings
        )
        check_blank(field_el, "label", where, findings)
        check_blank(field_el, "help", where, findings)

        field_model = model.fields.get(api_name) if model is not None else None
        if model is not None and field_model is None:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"field '{api_name}' is not defined on {object_name} in this "
                    "tree. A translation whose <name> matches nothing is stored "
                    "and never rendered.",
                )
            )

        seen: set[str] = set()
        for value_el in children(field_el, "picklistValues"):
            master = child_text(value_el, "masterLabel")
            translation = child(value_el, "translation")
            vwhere = f"{where} [{master or '?'}]"
            if not master:
                findings.append(
                    Finding(
                        ERROR,
                        vwhere,
                        "<picklistValues> has no <masterLabel>. Both masterLabel "
                        "and translation are Required "
                        "(api_meta.txt:46186-46189).",
                    )
                )
                continue
            seen.add(master)
            if translation is None:
                findings.append(
                    Finding(
                        ERROR,
                        vwhere,
                        "<picklistValues> has no <translation>. It is Required "
                        "here, unlike GlobalValueSetTranslation where it is "
                        "optional (api_meta.txt:46186-46189 vs "
                        "api_meta.txt:79466-79470).",
                    )
                )
            elif has_only_comment(translation):
                findings.append(
                    Finding(
                        WARN,
                        vwhere,
                        "<translation> is blank or comment-only, which is the "
                        "guide's own untranslated marker "
                        "(api_meta.txt:79475-79476). It deploys clean and shows "
                        "the master label.",
                    )
                )
            if field_model is not None:
                if field_model["value_set"]:
                    findings.append(
                        Finding(
                            ERROR,
                            vwhere,
                            f"field '{api_name}' inherits the global value set "
                            f"'{field_model['value_set']}', so its values are "
                            "translated once in a GlobalValueSetTranslation, not "
                            "per field. PicklistValueTranslation covers only "
                            "'a local, custom picklist field' "
                            "(api_meta.txt:46182-46183).",
                        )
                    )
                elif field_model["values"] and master not in field_model["values"]:
                    findings.append(
                        Finding(
                            ERROR,
                            vwhere,
                            f"'{master}' is not a value of {object_name}."
                            f"{api_name}. masterLabel is 'the picklist value "
                            "defined on the setup page' "
                            "(api_meta.txt:46186-46188) — match the value's "
                            "label, not a guess at its API name.",
                        )
                    )
        if field_model is not None and not field_model["value_set"]:
            missing = field_model["values"] - seen
            if seen and missing:
                findings.append(
                    Finding(
                        INFO,
                        where,
                        f"{len(missing)} value(s) of this picklist have no "
                        f"translation entry: {', '.join(sorted(missing)[:6])}"
                        + (" …" if len(missing) > 6 else ""),
                    )
                )
        translated_values[api_name] = seen

    for kind, tag, name_tag, label_tag in (
        ("record type", "recordTypes", "name", "label"),
        ("validation rule", "validationRules", "name", "errorMessage"),
        ("web link", "webLinks", "name", "label"),
        ("sharing reason", "sharingReasons", "name", "label"),
        ("workflow task", "workflowTasks", "name", "subject"),
        ("quick action", "quickActions", "name", "label"),
    ):
        for entry in children(element, tag):
            entry_name = child_text(entry, name_tag)
            where = f"{rel} [{tag}/{entry_name or '?'}]"
            if not entry_name:
                findings.append(
                    Finding(ERROR, where, f"<{tag}> entry has no <{name_tag}> (Required).")
                )
                continue
            check_blank(entry, label_tag, where, findings)
            if tag == "recordTypes":
                check_length(child_text(entry, "label"), "record_type_label", where, findings)
            if tag == "webLinks":
                check_length(child_text(entry, "label"), "web_link_label", where, findings)
            if tag == "quickActions":
                check_length(child_text(entry, "label"), "quick_action_label", where, findings)
            if model is None:
                continue
            pool = {
                "recordTypes": model.record_types,
                "validationRules": model.validation_rules,
                "webLinks": model.web_links,
                "sharingReasons": model.sharing_reasons,
            }.get(tag)
            if pool is not None and pool and entry_name not in pool:
                findings.append(
                    Finding(
                        ERROR,
                        where,
                        f"{kind} '{entry_name}' is not defined on {object_name} "
                        "in this tree.",
                    )
                )

    for layout in children(element, "layouts"):
        layout_name = child_text(layout, "layout")
        if not layout_name:
            findings.append(
                Finding(
                    ERROR,
                    f"{rel} [layouts]",
                    "<layouts> has no <layout>. It is 'Required. The layout "
                    "name' (api_meta.txt:46051).",
                )
            )
        for section in children(layout, "sections"):
            swhere = f"{rel} [layouts/{layout_name or '?'}/{child_text(section, 'section') or '?'}]"
            if not child_text(section, "section"):
                findings.append(
                    Finding(ERROR, swhere, "<sections> has no <section> (Required).")
                )
            check_length(child_text(section, "label"), "section_label", swhere, findings)
            check_blank(section, "label", swhere, findings)

    if model is not None and model.fields:
        untranslated = sorted(set(model.fields) - translated_fields)
        if untranslated:
            findings.append(
                Finding(
                    INFO,
                    rel,
                    f"{len(untranslated)} field(s) on {object_name} have no "
                    f"translation entry for '{locale}': "
                    f"{', '.join(untranslated[:8])}"
                    + (" …" if len(untranslated) > 8 else "")
                    + ". With useLanguageFallback on (default true, "
                    "api_meta.txt:120968-120971) these render in the source "
                    "language with no error.",
                )
            )


def check_value_set_translation(path: Path, root: Path, kind: str,
                                suffixes: tuple[str, ...],
                                gvs: dict[str, set[str]], active: set[str],
                                settings: dict[str, bool] | None,
                                findings: list[Finding]) -> None:
    rel = str(path.relative_to(root))
    stem = strip_suffix(path.name, suffixes)
    citation = (
        "api_meta.txt:79446-79448" if kind == "global" else "api_meta.txt:130842-130844"
    )
    if "-" not in stem:
        findings.append(
            Finding(
                ERROR,
                rel,
                f"file name '{stem}' has no '-<lang>' part; the required form is "
                f"ValueSetName-lang ({citation}).",
            )
        )
        return
    value_set_name, _, locale = stem.rpartition("-")
    check_locale(locale, f"{rel} [{locale}]", active, settings, findings)

    element = parse_xml(path, rel, findings)
    if element is None:
        return

    known = gvs.get(value_set_name)
    if kind == "global" and known is None:
        if not value_set_name.endswith("__gvs") and (value_set_name + "__gvs") in gvs:
            findings.append(
                Finding(
                    ERROR,
                    rel,
                    f"the value set in this tree is '{value_set_name}__gvs'. Any "
                    "global value set created in API version 57.0 or later has "
                    "the __gvs suffix appended to its developer name and the "
                    "suffix must be used when referencing the type "
                    f"(api_meta.txt:79419-79421). Rename this file to "
                    f"{value_set_name}__gvs-{locale}.",
                )
            )
        else:
            findings.append(
                Finding(
                    INFO,
                    rel,
                    f"global value set '{value_set_name}' is not in this tree, so "
                    "its values cannot be verified.",
                )
            )

    for value_el in children(element, "valueTranslation"):
        master = child_text(value_el, "masterLabel")
        where = f"{rel} [{master or '?'}]"
        if not master:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    "<valueTranslation> has no <masterLabel>; it is Required "
                    "(api_meta.txt:79466-79468).",
                )
            )
            continue
        translation = child(value_el, "translation")
        if translation is None or has_only_comment(translation):
            findings.append(
                Finding(
                    WARN,
                    where,
                    "no translation. The guide's convention is that an "
                    "untranslated value's translation 'becomes a comment that's "
                    "paired with its masterLabel' "
                    "(api_meta.txt:79475-79476) — valid XML that ships English.",
                )
            )
        if known and master not in known:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"'{master}' is not a value of {value_set_name} in this tree.",
                )
            )


def check_translations_file(path: Path, root: Path, active: set[str],
                            settings: dict[str, bool] | None,
                            label_names: set[str],
                            findings: list[Finding]) -> None:
    rel = str(path.relative_to(root))
    stem = strip_suffix(path.name, TRANSLATION_SUFFIXES)
    locale = stem.split("__")[-1] if "__" in stem else stem  # pkgNamespace__localeCode
    check_locale(locale, f"{rel} [{locale}]", active, settings, findings)

    element = parse_xml(path, rel, findings)
    if element is None:
        return

    for entry in children(element, "customLabels"):
        name = child_text(entry, "name")
        where = f"{rel} [customLabels/{name or '?'}]"
        if not name:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    "<customLabels> has no <name>; it is Required "
                    "(api_meta.txt:135937).",
                )
            )
            continue
        check_length(child_text(entry, "label"), "custom_label_label", where, findings)
        check_blank(entry, "label", where, findings)
        if label_names and name not in label_names:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    f"custom label '{name}' is not defined in the CustomLabels "
                    "file in this tree. The label's own lifecycle belongs to "
                    "admin/custom-label-management.",
                )
            )

    for entry in children(element, "customApplications"):
        where = f"{rel} [customApplications/{child_text(entry, 'name') or '?'}]"
        check_length(child_text(entry, "label"), "custom_app_label", where, findings)
        check_blank(entry, "label", where, findings)

    for entry in children(element, "quickActions"):
        where = f"{rel} [quickActions/{child_text(entry, 'name') or '?'}]"
        check_length(child_text(entry, "label"), "quick_action_label", where, findings)

    for entry in children(element, "flowDefinitions"):
        full_name = child_text(entry, "fullName")
        legacy_name = child_text(entry, "name")
        where = f"{rel} [flowDefinitions/{full_name or legacy_name or '?'}]"
        if full_name is None:
            findings.append(
                Finding(
                    ERROR,
                    where,
                    "<flowDefinitions> identifies the flow with <fullName>, not "
                    "<name>: 'Required. The API name for the flow definition' "
                    "(api_meta.txt:136015). Copying the <name> shape from a "
                    "sibling element here is the usual hand-edit error."
                    + (f" Found <name>{legacy_name}</name>." if legacy_name else ""),
                )
            )


def collect_label_names(root: Path, findings: list[Finding]) -> set[str]:
    names: set[str] = set()
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if not (path.name.endswith(".labels-meta.xml") or path.name.endswith(".labels")):
            continue
        element = parse_xml(path, str(path), findings)
        if element is None:
            continue
        for entry in children(element, "labels"):
            value = child_text(entry, "fullName")
            if value:
                names.add(value)
    return names


def main() -> int:
    args = parse_args()
    root = Path(args.manifest_dir)
    findings: list[Finding] = []

    if not root.is_dir():
        print(f"ERROR: manifest dir not found: {root}", file=sys.stderr)
        return 1

    active = {
        code.strip() for code in args.active_locales.split(",") if code.strip()
    }
    for code in sorted(active):
        if code not in ALL_LOCALES:
            findings.append(
                Finding(
                    ERROR,
                    "--active-locales",
                    f"'{code}' is not a Salesforce language code "
                    "(api_meta.txt:135356-135572).",
                )
            )

    obj_files = files_with_suffix(root, OBJ_TRANSLATION_SUFFIXES)
    gvs_files = files_with_suffix(root, GVS_TRANSLATION_SUFFIXES)
    svs_files = files_with_suffix(root, SVS_TRANSLATION_SUFFIXES)
    tr_files = [
        p for p in files_with_suffix(root, TRANSLATION_SUFFIXES)
        if not any(p.name.endswith(s) for s in
                   OBJ_TRANSLATION_SUFFIXES + GVS_TRANSLATION_SUFFIXES
                   + SVS_TRANSLATION_SUFFIXES)
    ]
    total = len(obj_files) + len(gvs_files) + len(svs_files) + len(tr_files)

    if total == 0:
        print(
            f"INFO: {root}: no translation metadata found "
            "(*.objectTranslation, *.translation, *.globalValueSetTranslation, "
            "*.standardValueSetTranslation). Nothing to check."
        )
        return 0

    settings = read_language_settings(root, findings)
    if settings is None:
        findings.append(
            Finding(
                WARN,
                str(root),
                "no settings/Language.settings file in this tree, so the "
                "Translation Workbench and end-user/platform language flags "
                "cannot be verified. enableTranslationWorkbench defaults to "
                "false (api_meta.txt:120965-120967); include Settings:Language "
                "in the same payload.",
            )
        )

    objects = collect_objects(root, findings)
    gvs = collect_global_value_sets(root, findings)
    label_names = collect_label_names(root, findings)

    for path in obj_files:
        check_object_translation(path, root, objects, gvs, active, settings, findings)
    for path in gvs_files:
        check_value_set_translation(
            path, root, "global", GVS_TRANSLATION_SUFFIXES, gvs, active, settings, findings
        )
    for path in svs_files:
        check_value_set_translation(
            path, root, "standard", SVS_TRANSLATION_SUFFIXES, {}, active, settings, findings
        )
    for path in tr_files:
        check_translations_file(path, root, active, settings, label_names, findings)

    errors = [f for f in findings if f.severity == ERROR]
    warns = [f for f in findings if f.severity == WARN]
    infos = [f for f in findings if f.severity == INFO]

    for finding in errors + warns:
        print(str(finding), file=sys.stderr)
    for finding in infos:
        print(str(finding))

    print(
        f"\n{total} translation file(s) checked against {len(objects)} object(s), "
        f"{len(gvs)} global value set(s) and {len(label_names)} custom label(s); "
        f"{len(errors)} ERROR, {len(warns)} WARN, {len(infos)} INFO."
    )

    if errors:
        return 1
    if warns and args.fail_on_warn:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
