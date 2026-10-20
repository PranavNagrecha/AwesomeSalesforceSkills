#!/usr/bin/env python3
"""Checker for the devops-center-pipeline skill.

Scans a project directory for the DevOps Center facts that can be checked offline:

  * settings/DevHub.settings[-meta.xml]
      WARN  both enableDevOpsCenterGA (managed package) and enableALMDevopsCorePref
            (Lifecycle Center, formerly next-generation) are true — pick one product per org
      WARN  enableDevopsCenterMigrationPref is true — developer preview
  * settings/SourceTracking.settings[-meta.xml]
      WARN  enableSourceTrackingSandboxes is false or absent — development
            sandboxes will not track changes
  * any *.json file holding `sf data query --json` output of DevopsPipelineStage
    records (fields Id, NextStageId; optional DevopsPipelineId, IsBundled,
    DevOpsEnvironmentId)
      ERROR a pipeline with no stage whose NextStageId is null (no production stage)
      ERROR a pipeline with more than one stage whose NextStageId is null
      ERROR NextStageId pointing at a stage not in the export, or a cycle
      WARN  two stages with the same NextStageId (the pipeline is an ordered path)
      WARN  two stages on the same DevOpsEnvironmentId
      WARN  IsBundled on the production stage (there is no next stage)
  * profiles/*.profile-meta.xml
      WARN  profiles in source: a frequent shared-component conflict hotspot

Exit 1 on any ERROR (or on WARN with --strict); exit 1 if --manifest-dir is missing.
Stdlib only.

Usage:
    python3 check_devops_center_pipeline.py --manifest-dir .
    python3 check_devops_center_pipeline.py --manifest-dir . --strict
"""

from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

NS = "{http://soap.sforce.com/2006/04/metadata}"


def _child(elem: ET.Element, tag: str) -> ET.Element | None:
    found = elem.find(NS + tag)
    if found is not None:
        return found
    return elem.find(tag)


def _bool(root: ET.Element, tag: str) -> bool | None:
    node = _child(root, tag)
    if node is None:
        return None
    return (node.text or "").strip().lower() == "true"


def _settings(root: Path, stem: str) -> list[Path]:
    names = {f"{stem}.settings", f"{stem}.settings-meta.xml"}
    return sorted(p for p in root.rglob("*") if p.is_file() and p.name in names)


def check_settings(root: Path, out: list[tuple[str, str]]) -> int:
    seen = 0
    for path in _settings(root, "DevHub"):
        seen += 1
        try:
            xml = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: not well-formed XML ({exc})"))
            continue
        if _bool(xml, "enableDevOpsCenterGA") and _bool(xml, "enableALMDevopsCorePref"):
            out.append(("WARN", f"{path}: both the DevOps Center managed package and Lifecycle Center (enableALMDevopsCorePref) are enabled; use one per project"))
        if _bool(xml, "enableDevopsCenterMigrationPref"):
            out.append(("WARN", f"{path}: enableDevopsCenterMigrationPref is a developer preview; keep it out of production manifests"))
    for path in _settings(root, "SourceTracking"):
        seen += 1
        try:
            xml = ET.parse(path).getroot()
        except ET.ParseError as exc:
            out.append(("ERROR", f"{path}: not well-formed XML ({exc})"))
            continue
        if not _bool(xml, "enableSourceTrackingSandboxes"):
            out.append(("WARN", f"{path}: enableSourceTrackingSandboxes is not true; new Developer/Developer Pro sandboxes will not track changes"))
    return seen


def _stage_records(path: Path) -> list[dict] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    records = data.get("result", {}).get("records") if isinstance(data, dict) else None
    if records is None and isinstance(data, dict):
        records = data.get("records")
    if not isinstance(records, list) or not records:
        return None
    if not all(isinstance(r, dict) and "Id" in r and "NextStageId" in r for r in records):
        return None
    return records


def check_stages(path: Path, records: list[dict], out: list[tuple[str, str]]) -> None:
    by_pipeline: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        by_pipeline[str(rec.get("DevopsPipelineId") or "(single pipeline)")].append(rec)
    for pipeline, stages in by_pipeline.items():
        ids = {s["Id"]: s for s in stages}
        name = lambda sid: ids[sid].get("Name") or sid  # noqa: E731
        terminal = [s for s in stages if not s.get("NextStageId")]
        if not terminal:
            out.append(("ERROR", f"{path}: pipeline {pipeline} has no stage with an empty NextStageId (no production stage)"))
        elif len(terminal) > 1:
            names = ", ".join(name(s["Id"]) for s in terminal)
            out.append(("ERROR", f"{path}: pipeline {pipeline} has {len(terminal)} stages with an empty NextStageId: {names}"))
        for s in stages:
            nxt = s.get("NextStageId")
            if nxt and nxt not in ids:
                out.append(("ERROR", f"{path}: stage {name(s['Id'])} points at NextStageId {nxt}, which is not in the export"))
        for start in ids:
            seen, cur = set(), start
            while cur and cur in ids and cur not in seen:
                seen.add(cur)
                cur = ids[cur].get("NextStageId")
            if cur and cur in seen and cur == start:
                out.append(("ERROR", f"{path}: pipeline {pipeline} has a NextStageId cycle through stage {name(start)}"))
                break
        nexts = Counter(s.get("NextStageId") for s in stages if s.get("NextStageId"))
        for nxt, count in nexts.items():
            if count > 1 and nxt in ids:
                out.append(("WARN", f"{path}: {count} stages promote into {name(nxt)}; a pipeline is an ordered path"))
        envs = Counter(s.get("DevOpsEnvironmentId") for s in stages if s.get("DevOpsEnvironmentId"))
        for env, count in envs.items():
            if count > 1:
                out.append(("WARN", f"{path}: {count} stages share environment {env}"))
        for s in terminal:
            if s.get("IsBundled") is True:
                out.append(("WARN", f"{path}: IsBundled is set on the production stage {name(s['Id'])}, which has no next stage"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check a project for DevOps Center pipeline issues.")
    parser.add_argument("--manifest-dir", required=True, type=Path, help="Project or metadata directory to scan.")
    parser.add_argument("--strict", action="store_true", help="Exit 1 on WARN as well as ERROR.")
    args = parser.parse_args(argv)

    root = args.manifest_dir
    if not root.is_dir():
        print(f"ERROR: manifest directory not found: {root}")
        sys.exit(1)

    out: list[tuple[str, str]] = []
    checked = check_settings(root, out)
    for path in sorted(root.rglob("*.json")):
        if "node_modules" in path.parts:
            continue
        records = _stage_records(path)
        if records is not None:
            checked += 1
            check_stages(path, records, out)
    profiles = sorted(root.rglob("*.profile-meta.xml"))
    if profiles:
        checked += 1
        out.append(("WARN", f"{len(profiles)} profile file(s) in source; profiles are a frequent shared-component conflict hotspot between work items"))

    if not checked:
        print(f"WARN: no DevHub/SourceTracking settings, stage export, or profiles found under {root}; nothing to check")
        return 0
    for level, msg in out:
        print(f"{level}: {msg}")
    errors = sum(1 for lvl, _ in out if lvl == "ERROR")
    warns = len(out) - errors
    print(f"Checked {checked} item(s): {errors} error(s), {warns} warning(s).")
    return 1 if errors or (args.strict and warns) else 0


if __name__ == "__main__":
    sys.exit(main())
