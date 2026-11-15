#!/usr/bin/env python3
# Isolated verifier entry point; only standard-library scoring is imported.
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from scoring import main
if __name__ == "__main__":
    raise SystemExit(main())
