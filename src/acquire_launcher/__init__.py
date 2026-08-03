from __future__ import annotations

import sys

from acquire_launcher.preflight import run_preflight, runtime_extraction_path


def main() -> int:
    extraction_path = runtime_extraction_path()
    if extraction_path:
        print(f"PyInstaller runtime extraction: {extraction_path}", file=sys.stderr)

    result = run_preflight()
    print(result.message, file=sys.stderr)
    if not result.allowed:
        return 2

    from acquire.acquire import main as acquire_main

    acquire_main()
    return 0
