#!/bin/zsh
set -euo pipefail

root_dir=${0:A:h:h}
cd "$root_dir"

UV_CACHE_DIR="$root_dir/.uv-cache" python3 scripts/prepare_environment.py
PYTHONHASHSEED=0 .venv/bin/pyinstaller --clean --noconfirm acquire.spec

[[ -x dist/acquire ]]
codesign --force --sign - dist/acquire
