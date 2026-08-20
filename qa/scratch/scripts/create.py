#!/usr/bin/env python3
"""Guarded scratch-org create stub. Refuses unless explicit opt-in is set.

Does not call the Salesforce CLI. No Dev Hub is required for this file to exist
or for unit tests to import it.
"""

from __future__ import annotations

import os
import sys

OPT_IN = "SFSKILLS_SCRATCH_OPT_IN"


def main() -> int:
    if os.environ.get(OPT_IN) != "1":
        print(
            "refused: scratch create is opt-in only. "
            f"Set {OPT_IN}=1 and pass an allowlisted Dev Hub. Status=not_run.",
            file=sys.stderr,
        )
        return 2
    print("not_implemented: scratch create remains not_run in M3", file=sys.stderr)
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
