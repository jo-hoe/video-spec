"""``python -m videospec`` entrypoint."""

from __future__ import annotations

import sys

from videospec.entrypoint import main

if __name__ == "__main__":
    sys.exit(main())
