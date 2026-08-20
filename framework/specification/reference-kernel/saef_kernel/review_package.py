from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile


DEFAULT_REQUIRED={
    "REVIEW.md",
    "MANIFEST.json",
    "SHA256SUMS.txt",
    "git/repository.bundle",
    "git/baseline.txt",
    "git/head.txt",
    "git/commit-log.txt",
    "git/status.txt",
    "git/diff.patch",
    "tests/test-index.json",
    "traceability/requirements.csv",
    "security/secret-scan.txt",
}


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_sums(text: str) -> dict[str,str]:
    result={}
    for line in text.splitlines():
        line=line.strip()
        if not line or line.startswith("#"):
            continue
        digest,rel=line.split(None,1)
        result[rel.lstrip("* ")]=digest.lower()
    return result


def validate_review_directory(root: str | Path, required: set[str] | None=None) -> list[str]:
    root=Path(root)
    issues=[]
    required=required or DEFAULT_REQUIRED
    for rel in sorted(required):
        if not (root/rel).is_file():
            issues.append(f"missing required file: {rel}")
    manifest_path=root/"MANIFEST.json"
    if manifest_path.is_file():
        try:
            manifest=json.loads(manifest_path.read_text())
            if manifest.get("local_only") is not True:
                issues.append("manifest local_only must be true")
            if manifest.get("clean_tree") is not True:
                issues.append("manifest clean_tree must be true")
            for test in manifest.get("tests",[]):
                if test.get("required",True) and test.get("exit_code")!=0:
                    issues.append(f"required test failed: {test.get('id')}")
        except Exception as exc:
            issues.append(f"invalid MANIFEST.json: {exc}")
    sums_path=root/"SHA256SUMS.txt"
    if sums_path.is_file():
        try:
            sums=_parse_sums(sums_path.read_text())
            for rel,digest in sums.items():
                path=root/rel
                if not path.is_file():
                    issues.append(f"checksum target missing: {rel}")
                elif sha256_file(path)!=digest:
                    issues.append(f"checksum mismatch: {rel}")
        except Exception as exc:
            issues.append(f"invalid SHA256SUMS.txt: {exc}")
    return issues


def validate_review_zip(path: str | Path, required: set[str] | None=None) -> list[str]:
    path=Path(path); required=required or DEFAULT_REQUIRED; issues=[]
    try:
        with zipfile.ZipFile(path) as z:
            names={x.rstrip("/") for x in z.namelist() if not x.endswith("/")}
            roots={x.split('/',1)[0] for x in names}
            prefix=(next(iter(roots))+"/") if len(roots)==1 and all('/' in x for x in names) else ""
            normalized={x[len(prefix):] if x.startswith(prefix) else x for x in names}
            for rel in sorted(required):
                if rel not in normalized:
                    issues.append(f"missing required file: {rel}")
    except zipfile.BadZipFile as exc:
        issues.append(f"bad zip: {exc}")
    return issues
