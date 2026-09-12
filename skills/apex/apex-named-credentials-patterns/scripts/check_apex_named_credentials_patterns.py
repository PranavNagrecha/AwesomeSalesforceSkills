#!/usr/bin/env python3
"""check_apex_named_credentials_patterns.py — static checks for Named Credential usage.

Scans a Salesforce source tree for the failure modes documented in the
apex-named-credentials-patterns skill: secrets that ended up in Apex, `callout:`
references that resolve to nothing, credentials still on the deprecated legacy
shape, `SecuredEndpoint` credentials with no authentication link, principals that
nothing grants, and Apex fighting the platform over the Authorization header.

Stdlib only. Never compiles Apex — every Apex rule is a regex heuristic, and the
rule table below says so where it matters.

Rules
-----
    NC-APEX-001  WARN      setEndpoint() with a literal http(s) URL while the tree
                           also contains Named Credentials.
    NC-APEX-002  ERROR     a literal http(s) endpoint in a file that also builds an
                           Authorization header from string literals — a credential
                           in source control.
    NC-APEX-003  ERROR     callout:<Name> naming a Named Credential that is not in
                           the tree (only raised when the tree has any).
    NC-META-001  WARN      NamedCredential with namedCredentialType Legacy — every
                           field that makes it work is deprecated at API 56.0.
    NC-META-002  ERROR     SecuredEndpoint NamedCredential with no Authentication
                           parameter carrying an externalCredential.
    NC-META-003  WARN      ExternalCredential with no NamedPrincipal or
                           PerUserPrincipal parameter — nothing to grant.
    NC-XREF-001  WARN      Apex sets an Authorization header while the Named
                           Credential it calls still generates one
                           (generateAuthorizationHeader defaults to true).
    NC-PERM-001  ADVISORY  the tree has an ExternalCredential and permission sets,
                           but no externalCredentialPrincipalAccesses grant.
    NC-RSS-001   ADVISORY  a RemoteSiteSetting covers the same host as a Named
                           Credential's Url parameter.
    NC-AUTH-01   ERROR     an ExternalCredential AuthHeader parameter with no
                           (or empty) parameterValue. Proven live in a
                           `sf project deploy start --dry-run`: "The parameter
                           type "AuthHeader" requires these fields:
                           ParameterValue." Not stated in the Metadata API
                           Developer Guide — see gotcha 14.
    NC-AUTH-02   WARN      an AuthHeader parameterValue formula referencing
                           {!$Credential.<EC>.<Param>} whose <EC> does not
                           match the file's own developer name — usually a
                           credential's example copied without rescoping it.
    NC-PS-01     INFO      a permission set's externalCredentialPrincipalAccesses
                           entry names a principal that resolves to no
                           ExternalCredential (or no matching principal
                           parameter) under this manifest dir. A deploy-order
                           dependency to confirm, not necessarily a defect —
                           the credential may deploy from an earlier step or a
                           separate manifest dir.

Exit status
-----------
    0  no ERROR findings (WARN, ADVISORY and INFO do not fail the run)
    1  at least one ERROR, or --manifest-dir does not exist

    --strict promotes every WARN to ERROR. ADVISORY and INFO are never promoted.

Usage
-----
    python3 check_apex_named_credentials_patterns.py --manifest-dir force-app
    python3 check_apex_named_credentials_patterns.py --manifest-dir force-app --strict
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

ERROR = "ERROR"
WARN = "WARN"
ADVISORY = "ADVISORY"
INFO = "INFO"

# --------------------------------------------------------------------------
# Apex regexes
# --------------------------------------------------------------------------

# setEndpoint('https://...') / setEndpoint("http://...")
LITERAL_ENDPOINT_RE = re.compile(
    r"""setEndpoint\s*\(\s*(['"])(https?://[^'"]*)\1""",
    re.IGNORECASE,
)

# callout:Some_Name — the name runs until a /, ?, quote, or concatenation.
CALLOUT_REF_RE = re.compile(r"""callout:([A-Za-z][A-Za-z0-9_]*)""")

# setHeader('Authorization', <value up to the closing paren>)
AUTH_HEADER_RE = re.compile(
    r"""setHeader\s*\(\s*(['"])Authorization\1\s*,\s*(?P<value>[^;]*?)\)\s*;""",
    re.IGNORECASE | re.DOTALL,
)

# A quoted literal that is not a merge field, e.g. 'Bearer ' or 'Basic abc123'.
QUOTED_LITERAL_RE = re.compile(r"""(['"])((?:(?!\1).)*)\1""", re.DOTALL)

MERGE_FIELD_MARKER = "{!$credential"

# $Credential.<ExternalCredentialDeveloperName>.<ParameterName> inside an AuthHeader
# parameterValue formula — the External-Credential-scoped form, distinct from the
# unscoped Apex-side $Credential.Username / $Credential.OAuthToken merge fields.
CREDENTIAL_SCOPED_MERGE_RE = re.compile(
    r"""\$Credential\.([A-Za-z0-9_]+)\.([A-Za-z0-9_]+)"""
)


# --------------------------------------------------------------------------
# XML helpers
# --------------------------------------------------------------------------


def strip_ns(tag: str) -> str:
    """'{http://...}foo' -> 'foo'."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def child(element, name: str):
    """First direct child named `name`, or None.

    Written as an explicit `is not None` walk on purpose: a leaf Element is
    falsy in ElementTree, so `a.find(x) or a.find(y)` silently drops real
    elements that happen to have no children.
    """
    if element is None:
        return None
    for sub in element:
        if strip_ns(sub.tag) == name:
            return sub
    return None


def child_text(element, name: str) -> str:
    """Stripped text of the first direct child named `name`, or ''."""
    sub = child(element, name)
    if sub is None or sub.text is None:
        return ""
    return sub.text.strip()


def children(element, name: str) -> list:
    """All direct children named `name`."""
    if element is None:
        return []
    return [sub for sub in element if strip_ns(sub.tag) == name]


def parse_xml(path: Path):
    """Return the root element, or None when the file cannot be parsed."""
    try:
        return ET.parse(path).getroot()
    except (ET.ParseError, OSError):
        return None


def api_name(path: Path) -> str:
    """'Partner_Orders_NC.namedCredential-meta.xml' -> 'Partner_Orders_NC'."""
    return path.name.split(".", 1)[0]


def host_of(url: str) -> str:
    try:
        return (urlparse(url.strip()).hostname or "").lower()
    except ValueError:
        return ""


# --------------------------------------------------------------------------
# Source-tree model
# --------------------------------------------------------------------------


class Tree:
    """Everything the rules need, collected in one pass."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.apex: list[Path] = sorted(
            p for p in root.rglob("*.cls") if not p.name.endswith("-meta.xml")
        )
        self.named_credentials = self._collect("namedCredential")
        self.external_credentials = self._collect("externalCredential")
        self.permission_sets = self._collect("permissionset")
        self.remote_sites = self._collect("remoteSite")

    def _collect(self, suffix: str) -> list[Path]:
        found = list(self.root.rglob(f"*.{suffix}"))
        found += list(self.root.rglob(f"*.{suffix}-meta.xml"))
        return sorted(set(found))

    def is_empty(self) -> bool:
        return not (
            self.apex
            or self.named_credentials
            or self.external_credentials
            or self.permission_sets
            or self.remote_sites
        )

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)


class Finding:
    def __init__(self, severity: str, rule: str, where: str, message: str) -> None:
        self.severity = severity
        self.rule = rule
        self.where = where
        self.message = message

    def render(self, effective: str) -> str:
        return f"{effective}: [{self.rule}] {self.where}: {self.message}"


# --------------------------------------------------------------------------
# Metadata analysis
# --------------------------------------------------------------------------


def read_named_credentials(tree: Tree) -> dict:
    """name -> {'path', 'type', 'external_credential', 'generates_auth', 'url'}."""
    out: dict[str, dict] = {}
    for path in tree.named_credentials:
        root = parse_xml(path)
        if root is None:
            continue
        params = children(root, "namedCredentialParameters")

        external_credential = ""
        url = ""
        for param in params:
            ptype = child_text(param, "parameterType")
            if ptype == "Authentication":
                value = child_text(param, "externalCredential")
                if value:
                    external_credential = value
            elif ptype == "Url":
                value = child_text(param, "parameterValue")
                if value:
                    url = value

        # generateAuthorizationHeader defaults to true when absent
        # (api_meta L90080-90088).
        raw_gah = child_text(root, "generateAuthorizationHeader")
        generates_auth = raw_gah.lower() != "false"

        out[api_name(path)] = {
            "path": path,
            "type": child_text(root, "namedCredentialType"),
            "external_credential": external_credential,
            "generates_auth": generates_auth,
            "url": url or child_text(root, "endpoint"),
        }
    return out


def check_named_credentials(tree: Tree, creds: dict) -> list[Finding]:
    findings: list[Finding] = []
    for name, meta in sorted(creds.items()):
        where = tree.rel(meta["path"])
        if meta["type"] == "Legacy":
            findings.append(
                Finding(
                    WARN,
                    "NC-META-001",
                    where,
                    f"'{name}' is namedCredentialType Legacy. Every field the legacy "
                    "shape depends on (endpoint, protocol, principalType, username, "
                    "password, oauthToken, authProvider, certificate) is deprecated in "
                    "API version 56.0. Migrate to SecuredEndpoint with an "
                    "ExternalCredential.",
                )
            )
        if meta["type"] == "SecuredEndpoint" and not meta["external_credential"]:
            findings.append(
                Finding(
                    ERROR,
                    "NC-META-002",
                    where,
                    f"'{name}' is SecuredEndpoint but has no namedCredentialParameters "
                    "entry with parameterType Authentication carrying an "
                    "<externalCredential>. Callouts through it cannot authenticate. "
                    "Note that externalCredential is a child of the parameter, not a "
                    "top-level element.",
                )
            )
    return findings


def check_external_credentials(
    tree: Tree,
) -> tuple[list[Finding], list[str], dict[str, set[str]]]:
    """Returns (findings, EC API names present, EC name -> set of principal parameterNames)."""
    findings: list[Finding] = []
    names: list[str] = []
    principal_types = {"NamedPrincipal", "PerUserPrincipal"}
    principal_map: dict[str, set[str]] = {}

    for path in tree.external_credentials:
        root = parse_xml(path)
        if root is None:
            continue
        name = api_name(path)
        names.append(name)

        params = children(root, "externalCredentialParameters")
        principals = [
            p for p in params if child_text(p, "parameterType") in principal_types
        ]
        principal_map[name] = {
            child_text(p, "parameterName") for p in principals if child_text(p, "parameterName")
        }
        if not principals:
            findings.append(
                Finding(
                    WARN,
                    "NC-META-003",
                    tree.rel(path),
                    f"'{name}' declares no principal — no externalCredentialParameters "
                    "entry has parameterType NamedPrincipal or PerUserPrincipal. There "
                    "is nothing for a permission set to grant, so every callout through "
                    "it will fail authorization.",
                )
            )
    return findings, names, principal_map


def check_auth_headers(tree: Tree) -> list[Finding]:
    """NC-AUTH-01 / NC-AUTH-02 over ExternalCredential AuthHeader parameters.

    NC-AUTH-01 (ERROR): an AuthHeader parameter with no (or empty) parameterValue.
    Proven live in a dry-run deploy — "The parameter type "AuthHeader" requires
    these fields: ParameterValue." — not stated in the Metadata API Developer
    Guide (gotcha 14). NC-AUTH-02 (WARN): a parameterValue formula scoped to an
    ExternalCredential ({!$Credential.<EC>.<Param>}) whose <EC> segment does not
    match the file's own developer name — usually a copied example left
    unrescoped.
    """
    findings: list[Finding] = []
    for path in tree.external_credentials:
        root = parse_xml(path)
        if root is None:
            continue
        name = api_name(path)
        where = tree.rel(path)

        for param in children(root, "externalCredentialParameters"):
            if child_text(param, "parameterType") != "AuthHeader":
                continue
            header_name = child_text(param, "parameterName") or "(unnamed)"
            value = child_text(param, "parameterValue")

            if not value:
                findings.append(
                    Finding(
                        ERROR,
                        "NC-AUTH-01",
                        where,
                        f"AuthHeader parameter '{header_name}' on '{name}' has no "
                        "parameterValue. Deploy validation rejects this — proven "
                        'live: \'The parameter type "AuthHeader" requires these '
                        "fields: ParameterValue.\' Write the header formula (for "
                        f"example {{!$Credential.{name}.<ParameterName>}}), naming "
                        "an authentication parameter that gets created in Setup "
                        "against the principal after this file deploys, never in "
                        "this metadata.",
                    )
                )
                continue

            match = CREDENTIAL_SCOPED_MERGE_RE.search(value)
            if match and match.group(1) != name:
                findings.append(
                    Finding(
                        WARN,
                        "NC-AUTH-02",
                        where,
                        f"AuthHeader parameter '{header_name}' on '{name}' formula "
                        f"references '$Credential.{match.group(1)}.{match.group(2)}' "
                        f"— a different External Credential than this file's own "
                        f"developer name ('{name}'). Likely a copied example left "
                        "unrescoped.",
                    )
                )
    return findings


def _parse_principal_ref(value: str) -> tuple[str, str] | None:
    """'<EC>-<principal>' or 'ns__<EC>-<principal>' -> (EC name, principal name).

    The dash between EC and principal is authoritative (api_meta L94995-94999);
    a packaging namespace prefix is joined to the EC name with two underscores
    (api_meta L94999-95003), so the namespace prefix is stripped before the
    comparison.
    """
    if not value or "-" not in value:
        return None
    ec_part, principal = value.split("-", 1)
    if "__" in ec_part:
        ec_part = ec_part.rsplit("__", 1)[-1]
    if not ec_part or not principal:
        return None
    return ec_part, principal


def check_permission_set_principal_refs(
    tree: Tree, ec_principals: dict[str, set[str]]
) -> list[Finding]:
    """NC-PS-01 (INFO): each externalCredentialPrincipalAccesses entry resolves
    to a principal declared on an ExternalCredential in this manifest dir.

    INFO, not ERROR/WARN: the External Credential legitimately may deploy from
    an earlier step or a separate manifest-dir invocation, so an unresolved
    reference here is a deploy-order dependency to confirm, not necessarily a
    defect in this file.
    """
    findings: list[Finding] = []
    for path in tree.permission_sets:
        root = parse_xml(path)
        if root is None:
            continue
        where = tree.rel(path)
        for access in children(root, "externalCredentialPrincipalAccesses"):
            ref = child_text(access, "externalCredentialPrincipal")
            parsed = _parse_principal_ref(ref)
            if parsed is None:
                continue
            ec_name, principal_name = parsed
            principals = ec_principals.get(ec_name)

            if principals is None:
                findings.append(
                    Finding(
                        INFO,
                        "NC-PS-01",
                        where,
                        f"externalCredentialPrincipalAccesses names '{ref}', but no "
                        f"{ec_name}.externalCredential-meta.xml exists under this "
                        "manifest dir. Deploy-order dependency, not necessarily a "
                        "defect — confirm the External Credential deploys (from an "
                        "earlier step or another manifest dir) before this "
                        "permission set.",
                    )
                )
            elif principal_name not in principals:
                findings.append(
                    Finding(
                        INFO,
                        "NC-PS-01",
                        where,
                        f"externalCredentialPrincipalAccesses names '{ref}', but "
                        f"'{ec_name}.externalCredential-meta.xml' declares no "
                        f"NamedPrincipal/PerUserPrincipal parameter named "
                        f"'{principal_name}'. Deploy-order dependency, not "
                        "necessarily a defect — confirm the principal name against "
                        "the External Credential that will actually be deployed.",
                    )
                )
    return findings


def check_permission_sets(tree: Tree, ec_names: list[str]) -> list[Finding]:
    if not ec_names or not tree.permission_sets:
        return []

    granted = False
    for path in tree.permission_sets:
        root = parse_xml(path)
        if root is None:
            continue
        if children(root, "externalCredentialPrincipalAccesses"):
            granted = True
            break

    if granted:
        return []
    return [
        Finding(
            ADVISORY,
            "NC-PERM-001",
            tree.rel(tree.permission_sets[0].parent),
            "the tree defines ExternalCredential(s) "
            f"({', '.join(sorted(ec_names))}) and {len(tree.permission_sets)} "
            "permission set(s), but no permission set carries "
            "externalCredentialPrincipalAccesses. A principal is inert until a "
            "permission set grants it and that set is assigned to the running user. "
            "Harmless if the grant lives in another repository.",
        )
    ]


def check_remote_sites(tree: Tree, creds: dict) -> list[Finding]:
    findings: list[Finding] = []
    cred_hosts: dict[str, str] = {}
    for name, meta in creds.items():
        host = host_of(meta["url"])
        if host:
            cred_hosts.setdefault(host, name)

    for path in tree.remote_sites:
        root = parse_xml(path)
        if root is None:
            continue
        host = host_of(child_text(root, "url"))
        if host and host in cred_hosts:
            findings.append(
                Finding(
                    ADVISORY,
                    "NC-RSS-001",
                    tree.rel(path),
                    f"remote site setting covers '{host}', which is also the host of "
                    f"Named Credential '{cred_hosts[host]}'. Callouts that go through "
                    "the credential do not need a remote site setting; one that remains "
                    "usually means some code path still calls the host directly.",
                )
            )
    return findings


# --------------------------------------------------------------------------
# Apex analysis
# --------------------------------------------------------------------------


def _authorization_values(source: str) -> list[str]:
    return [m.group("value") for m in AUTH_HEADER_RE.finditer(source)]


def _has_literal_secret(value: str) -> bool:
    """True when an Authorization value is built from a non-merge-field literal.

    'Bearer {!$Credential.Password}' is fine — the secret stays in the vault.
    'Bearer ' + token  is not: whatever `token` is, the scheme prefix is a literal
    and the value is assembled in Apex rather than by the platform.
    """
    if MERGE_FIELD_MARKER in value.lower():
        return False
    return bool(QUOTED_LITERAL_RE.search(value))


def check_apex(tree: Tree, creds: dict) -> list[Finding]:
    findings: list[Finding] = []
    known = set(creds)

    for path in tree.apex:
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        where = tree.rel(path)

        literal_endpoints = [m.group(2) for m in LITERAL_ENDPOINT_RE.finditer(source)]
        auth_values = _authorization_values(source)
        referenced = sorted(set(CALLOUT_REF_RE.findall(source)))

        # NC-APEX-002 — a literal endpoint plus a hand-built Authorization header.
        secret_values = [v for v in auth_values if _has_literal_secret(v)]
        if literal_endpoints and secret_values:
            findings.append(
                Finding(
                    ERROR,
                    "NC-APEX-002",
                    where,
                    f"literal endpoint {literal_endpoints[0]!r} together with an "
                    "Authorization header assembled from string literals in Apex. The "
                    "credential is in source control. Move the endpoint to a Named "
                    "Credential and let the platform generate the header, or use a "
                    "{!$Credential.*} merge field.",
                )
            )
        elif literal_endpoints and known:
            # NC-APEX-001 — literal endpoint in a tree that does use credentials.
            findings.append(
                Finding(
                    WARN,
                    "NC-APEX-001",
                    where,
                    f"setEndpoint() uses the literal URL {literal_endpoints[0]!r} while "
                    f"the tree defines {len(known)} Named Credential(s). Use "
                    "'callout:<NamedCredentialApiName>/path' so the endpoint stays "
                    "environment-portable and the auth stays out of code.",
                )
            )

        # NC-APEX-003 — callout: naming a credential the tree does not define.
        if known:
            for name in referenced:
                if name not in known:
                    findings.append(
                        Finding(
                            ERROR,
                            "NC-APEX-003",
                            where,
                            f"'callout:{name}' does not resolve — no "
                            f"{name}.namedCredential-meta.xml in the tree. Check for a "
                            "typo, or for the External Credential name used where the "
                            "Named Credential name belongs.",
                        )
                    )

        # NC-XREF-001 — Apex header versus platform-generated header.
        if auth_values:
            for name in referenced:
                meta = creds.get(name)
                if meta is not None and meta["generates_auth"]:
                    findings.append(
                        Finding(
                            WARN,
                            "NC-XREF-001",
                            where,
                            f"this file sets an Authorization header and calls "
                            f"'callout:{name}', whose generateAuthorizationHeader is "
                            "true (or absent, which defaults to true). Both sides are "
                            "supplying the header. Set "
                            "<generateAuthorizationHeader>false</generateAuthorizationHeader> "
                            "if Apex owns it, or drop the setHeader call if the platform "
                            "does. Heuristic: this rule pairs any Authorization header in "
                            "the file with any callout: reference in the same file.",
                        )
                    )

    return findings


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------


def run(manifest_dir: Path) -> tuple[list[Finding], bool]:
    """Returns (findings, tree_was_empty)."""
    tree = Tree(manifest_dir)
    if tree.is_empty():
        return [], True

    creds = read_named_credentials(tree)
    findings: list[Finding] = []
    findings += check_named_credentials(tree, creds)
    ec_findings, ec_names, ec_principals = check_external_credentials(tree)
    findings += ec_findings
    findings += check_permission_sets(tree, ec_names)
    findings += check_remote_sites(tree, creds)
    findings += check_auth_headers(tree)
    findings += check_permission_set_principal_refs(tree, ec_principals)
    findings += check_apex(tree, creds)
    return findings, False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Check Apex source and Named Credential / External Credential metadata "
            "for the anti-patterns documented in the apex-named-credentials-patterns "
            "skill."
        ),
    )
    parser.add_argument(
        "--manifest-dir",
        default=".",
        help="Root of the Salesforce source tree to scan (default: current directory).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Promote every WARN to ERROR. ADVISORY findings are never promoted.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_dir = Path(args.manifest_dir)

    if not manifest_dir.is_dir():
        print(f"ERROR: --manifest-dir not found or not a directory: {manifest_dir}", file=sys.stderr)
        return 1

    findings, empty = run(manifest_dir)

    if empty:
        print(
            f"WARN: no Apex classes or credential metadata found under {manifest_dir}. "
            "Point --manifest-dir at the package directory (for example force-app).",
            file=sys.stderr,
        )
        return 0

    if not findings:
        print("OK: no Named Credential findings.")
        return 0

    order = {ERROR: 0, WARN: 1, ADVISORY: 2, INFO: 3}
    findings.sort(key=lambda f: (order[f.severity], f.rule, f.where))

    failed = 0
    counts = {ERROR: 0, WARN: 0, ADVISORY: 0, INFO: 0}
    for finding in findings:
        effective = finding.severity
        if args.strict and effective == WARN:
            effective = ERROR
        counts[finding.severity] += 1
        if effective == ERROR:
            failed += 1
        print(finding.render(effective), file=sys.stderr)

    print(
        f"\n{counts[ERROR]} error(s), {counts[WARN]} warning(s), "
        f"{counts[ADVISORY]} advisory, {counts[INFO]} info"
        + (" — --strict is on, warnings fail the run" if args.strict else ""),
        file=sys.stderr,
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
