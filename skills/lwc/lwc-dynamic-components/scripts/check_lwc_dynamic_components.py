#!/usr/bin/env python3
"""Entry point alias for the LWC Dynamic Components checker.

The canonical checker is check_lwc_dynamic.py in this directory.
This file delegates to it so both names work.

Usage:
    python3 check_lwc_dynamic_components.py [--manifest-dir path/to/lwc]
"""

import sys
from pathlib import Path

# Add this directory to the path and run the canonical checker
sys.path.insert(0, str(Path(__file__).parent))

from check_lwc_dynamic import main  # noqa: E402

if __name__ == '__main__':
    sys.exit(main())
