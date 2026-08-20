from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .context import ContextBudget, ContextCandidate, compile_context_manifest
from .evidence import lint_claims
from .policy import ProductPolicy, Decision, evaluate_salesforce_shell
from .review_package import validate_review_directory, validate_review_zip
from .schema_utils import validate_json


def _json(value):
    print(json.dumps(value,indent=2,sort_keys=True))


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(prog="saef-reference")
    sub=parser.add_subparsers(dest="cmd",required=True)
    p=sub.add_parser("validate-json"); p.add_argument("instance"); p.add_argument("schema")
    p=sub.add_parser("lint-evidence"); p.add_argument("claims"); p.add_argument("evidence")
    p=sub.add_parser("check-shell"); p.add_argument("command")
    p=sub.add_parser("check-tool"); p.add_argument("tool"); p.add_argument("--allow",action="append",default=[]); p.add_argument("--org"); p.add_argument("--allow-org",action="append",default=[])
    p=sub.add_parser("validate-review"); p.add_argument("path")
    args=parser.parse_args(argv)
    if args.cmd=="validate-json":
        errors=validate_json(args.instance,args.schema); _json({"valid":not errors,"errors":errors}); return 0 if not errors else 1
    if args.cmd=="lint-evidence":
        claims=json.loads(Path(args.claims).read_text()); evidence=json.loads(Path(args.evidence).read_text()); findings=lint_claims(claims,evidence); _json({"valid":not any(x['severity']=='blocking' for x in findings),"findings":findings}); return 1 if any(x['severity']=='blocking' for x in findings) else 0
    if args.cmd=="check-shell":
        result=evaluate_salesforce_shell(args.command); _json({"decision":result.decision.value,"reason_code":result.reason_code,"message":result.message}); return 0 if result.decision==Decision.ALLOW else 1
    if args.cmd=="check-tool":
        policy=ProductPolicy(set(args.allow),allowed_orgs=set(args.allow_org) if args.allow_org else None); result=policy.evaluate_tool(args.tool,args.org); _json({"decision":result.decision.value,"reason_code":result.reason_code,"message":result.message}); return 0 if result.decision==Decision.ALLOW else 1
    if args.cmd=="validate-review":
        path=Path(args.path); issues=validate_review_zip(path) if path.is_file() else validate_review_directory(path); _json({"valid":not issues,"issues":issues}); return 0 if not issues else 1
    return 2

if __name__=="__main__":
    raise SystemExit(main())
