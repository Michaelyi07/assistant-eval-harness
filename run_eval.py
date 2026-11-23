#!/usr/bin/env python
"""CLI entry: run the local evaluation and enforce the thresholds via exit code."""

import sys

from assistant_eval.runner import main

if __name__ == "__main__":
    sys.exit(main())
