#!/bin/zsh
set -euo pipefail

release_dir=${1:-dist}
release_dir=${release_dir:A}
archive_name=acquire-macos-arm64.tar.gz
checksum_name=${archive_name}.sha256
members=(acquire acquire.sha256 SBOM.txt LICENSE THIRD_PARTY_NOTICES.md)

for member in $members; do
  [[ -f "$release_dir/$member" ]]
done
[[ -x "$release_dir/acquire" ]]

COPYFILE_DISABLE=1 tar -czf "$release_dir/$archive_name" -C "$release_dir" $members
(cd "$release_dir" && shasum -a 256 "$archive_name" > "$checksum_name")

verify_dir=$(mktemp -d "${TMPDIR:-/tmp}/acquire-release.XXXXXX")
trap 'rm -rf "$verify_dir"' EXIT
tar -xzf "$release_dir/$archive_name" -C "$verify_dir"

for member in $members; do
  [[ -f "$verify_dir/$member" ]]
done
[[ -x "$verify_dir/acquire" ]]
(cd "$verify_dir" && shasum -a 256 -c acquire.sha256)
(cd "$release_dir" && shasum -a 256 -c "$checksum_name")
