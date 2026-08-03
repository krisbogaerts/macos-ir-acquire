#!/bin/zsh
set -euo pipefail

root_dir=${0:A:h:h}
cd "$root_dir"

[[ -x dist/acquire ]]
.venv/bin/pytest tests -v
file dist/acquire | grep -q 'arm64'
codesign --verify --strict --verbose=2 dist/acquire
cp LICENSE THIRD_PARTY_NOTICES.md dist/

if find dist -mindepth 1 -maxdepth 1 -type d | grep -q .; then
  echo "Unexpected PyInstaller sidecar directory in dist" >&2
  exit 1
fi

uv_bin=${ACQUIRE_UV:-${commands[uv]:-}}
[[ -n "$uv_bin" && -x "$uv_bin" ]]
uv_bin=${uv_bin:A}

UV_CACHE_DIR="$root_dir/.uv-cache" "$uv_bin" pip freeze --python .venv/bin/python \
  | sed 's#^acquire-macos-launcher @ file://.*#acquire-macos-launcher==0.1.0#' \
  | LC_ALL=C sort > dist/SBOM.txt
(cd dist && shasum -a 256 acquire > acquire.sha256)
(cd dist && shasum -a 256 -c acquire.sha256)

grep -q '^acquire==3\.22$' dist/SBOM.txt
grep -q '^pyinstaller==6\.21\.0$' dist/SBOM.txt
grep -q '^pytest==9\.0\.3$' dist/SBOM.txt
