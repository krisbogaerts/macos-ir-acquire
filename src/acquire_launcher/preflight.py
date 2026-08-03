from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

GIB = 1024**3
HARD_MIN_BYTES = 5 * GIB
WARN_MIN_BYTES = 20 * GIB


@dataclass(frozen=True)
class PreflightResult:
    allowed: bool
    warning: bool
    message: str


def evaluate_preflight(euid: int, output_dir: Path, writable: bool, free_bytes: int) -> PreflightResult:
    if euid != 0:
        return PreflightResult(False, False, "Run with: sudo ./acquire")
    if not writable:
        return PreflightResult(False, False, f"Output directory is not writable: {output_dir}")

    free_gib = free_bytes / GIB
    if free_bytes < HARD_MIN_BYTES:
        return PreflightResult(
            False,
            False,
            f"Insufficient free space: {free_gib:.1f} GiB available; at least 5.0 GiB is required",
        )
    if free_bytes < WARN_MIN_BYTES:
        return PreflightResult(
            True,
            True,
            f"WARNING: only {free_gib:.1f} GiB available in {output_dir}; full acquisition may not fit",
        )
    return PreflightResult(True, False, f"Output: {output_dir} ({free_gib:.1f} GiB available)")


def runtime_extraction_path() -> Path | None:
    value = getattr(sys, "_MEIPASS", None)
    return Path(value) if value else None


def run_preflight() -> PreflightResult:
    output_dir = Path.cwd().resolve()
    return evaluate_preflight(
        euid=os.geteuid(),
        output_dir=output_dir,
        writable=output_dir.is_dir() and os.access(output_dir, os.W_OK),
        free_bytes=shutil.disk_usage(output_dir).free,
    )
