#!/usr/bin/env python3
"""
Verify the fung_ai_v2/ package structure is complete.

IMPORTANT: This script does NOT generate or overwrite package files. The
real extraction (splitting fungaiV2_extracted/fung_ai_v2.py into modules
with actual logic) is done directly, file by file, not by a generator here
— a generator that fabricates module contents independent of the real
source is exactly how you get imports for functions that were never
extracted correctly (e.g. an earlier version of this script referenced
`apply_rule`, `flood_fill`, `export_json` — none of which exist in the
real source or the real package).

This script only CHECKS that the expected modules exist and are
non-empty/non-stub. It never writes __init__.py or any module file. Rerun
it any time to confirm the package hasn't regressed to a stub state.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
PACKAGE_DIR = PROJECT_ROOT / "fung_ai_v2"

# The real modules that make up the extracted package, per the actual
# split performed against fungaiV2_extracted/fung_ai_v2.py.
EXPECTED_MODULES = [
    "__init__.py",
    "ca_engine.py",
    "fitness.py",
    "archive.py",
    "emitters.py",
    "algorithms.py",
    "exporters.py",
    "validators.py",
    "environment.py",
    "cache.py",
    "cli.py",
]

# A file under this many bytes almost certainly means "stub", not "real
# extracted logic" (the smallest real module, validators.py, is well over
# this).
MIN_REAL_FILE_BYTES = 200


def main() -> int:
    if not PACKAGE_DIR.exists():
        print(f"❌ {PACKAGE_DIR} does not exist yet — extraction hasn't started.")
        return 1

    missing = []
    stub_like = []
    ok = []

    for name in EXPECTED_MODULES:
        path = PACKAGE_DIR / name
        if not path.exists():
            missing.append(name)
            continue

        size = path.stat().st_size
        text = path.read_text(encoding="utf-8", errors="ignore")

        # A stub from the old broken generator looked like:
        #   """Module: x\n\nTODO: ...\n"""\n\n__all__ = []\n
        if size < MIN_REAL_FILE_BYTES or ("TODO: Extract from original" in text):
            stub_like.append(name)
        else:
            ok.append(name)

    print(f"Checked {PACKAGE_DIR}\n")
    if ok:
        print(f"✅ Real ({len(ok)}): {', '.join(ok)}")
    if stub_like:
        print(f"⚠️  Stub-like, needs real extraction ({len(stub_like)}): {', '.join(stub_like)}")
    if missing:
        print(f"❌ Missing ({len(missing)}): {', '.join(missing)}")

    if missing or stub_like:
        print("\nDo NOT auto-generate these — extract each one by hand from")
        print("fungaiV2_extracted/fung_ai_v2.py so the logic is real, not a stub.")
        return 1

    print("\n✅ Package structure complete, no stubs detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
