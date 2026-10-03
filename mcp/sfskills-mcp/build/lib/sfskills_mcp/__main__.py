"""Console entry point: ``python -m sfskills_mcp`` runs the MCP server over stdio."""

from __future__ import annotations

import argparse
import sys

from .server import run


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sfskills-mcp",
        description="SfSkills MCP server (Salesforce skills + live-org metadata).",
    )
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio"],
        help="MCP transport. Only 'stdio' is supported today.",
    )
    args = parser.parse_args(argv)
    run(transport=args.transport)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
