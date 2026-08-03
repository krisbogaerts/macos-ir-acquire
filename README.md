# Acquire macOS arm64 one-file package

This repository packages Fox-IT's Acquire for authorized incident-response and forensic collection on Apple Silicon Macs. It produces a single PyInstaller executable that an operator runs as `sudo ./acquire`; the embedded defaults use Acquire's full macOS profile and a gzip-compressed tar archive. Filesystem fallback is disabled.

The package is intentionally a thin launcher around upstream Acquire rather than a new collector. It requires no Python installation on the target Mac and writes the evidence archive, collection report, and log to the current directory. PyInstaller one-file execution creates a temporary `_MEI…` extraction directory, so the result is not fileless.

## Pinned build

- Python 3.10
- Acquire 3.22
- dissect.target 3.25.1
- dissect.apfs 1.1
- PyInstaller 6.21.0

All transitive versions and hashes are recorded in `requirements.lock`.

## Build on Apple Silicon

Install `uv` 0.11.x and Apple command-line developer tools, then run from the repository root. CI pins uv 0.11.16 and the build resolves the selected executable to an absolute path before use:

```bash
./scripts/build.sh
./scripts/verify_release.sh
```

The build script prepares `.venv`, synchronizes the hash-locked dependencies, generates Dissect's plugin list, stages Acquire's embedded configuration, builds an arm64 PyInstaller one-file executable, and applies an ad-hoc development signature.

The verifier runs the test suite, verifies arm64 architecture and the code signature, rejects PyInstaller sidecar directories, and generates/checks the release inventory and checksum.

Generated release files under `dist/` are:

- `acquire` — arm64 one-file executable;
- `acquire.sha256` — SHA-256 checksum;
- `SBOM.txt` — installed-package inventory.
- `LICENSE` and `THIRD_PARTY_NOTICES.md` — source and third-party license terms.
- `acquire-macos-arm64.tar.gz` — downloadable release archive that preserves the executable permission;
- `acquire-macos-arm64.tar.gz.sha256` — SHA-256 checksum for the complete release archive.

## Operator use

Follow the [operator guide](docs/OPERATOR.md). After downloading a release:

1. Create a dedicated, access-controlled case directory on the target Mac with at least 20 GiB of free space when practical. Place `acquire-macos-arm64.tar.gz` and `acquire-macos-arm64.tar.gz.sha256` in that directory. Do not use a shared or cloud-synchronized folder.
2. Open Terminal, change to that case directory, restrict permissions for newly created files, and verify the downloaded archive:

```bash
cd "/path/to/approved-case-directory"
umask 077
shasum -a 256 -c acquire-macos-arm64.tar.gz.sha256
```

Continue only when the command reports `acquire-macos-arm64.tar.gz: OK`.

3. Extract the release into a new directory and enter it:

```bash
mkdir acquire-macos-arm64
tar -xzf acquire-macos-arm64.tar.gz -C acquire-macos-arm64
cd acquire-macos-arm64
```

4. Verify the executable inside the archive:

```bash
shasum -a 256 -c acquire.sha256
```

Continue only when the command reports `acquire: OK`.

5. For the best collection coverage, open **System Settings → Privacy & Security → Full Disk Access**, enable your terminal application, and restart that terminal application if macOS requests it.
6. Return to the extracted directory, remove the quarantine attribute from the checksum-verified executable, and run it:

```bash
cd "/path/to/approved-case-directory/acquire-macos-arm64"
umask 077
xattr -d com.apple.quarantine ./acquire
sudo ./acquire
```

Replace `/path/to/approved-case-directory` with the actual case-directory path. Enter the administrator password when prompted. Acquire writes the evidence archive, report, and log into the current extracted directory; leave the terminal open until collection finishes and upload all resulting collection files according to the approved evidence-handling process.

Only remove the quarantine attribute after both checksum commands report `OK` and you trust the release source. The current release is ad-hoc signed rather than Apple-notarized, so Gatekeeper otherwise blocks the downloaded executable. Start with at least 20 GiB of free space when practical; the launcher refuses to run below 5 GiB.

Root is preferred, but Full Disk Access is still needed for the best macOS coverage. Collection can include sensitive browser history, cookies, saved-login databases, shell history, logs, persistence data, SSH metadata, and other user/system artifacts. Only use the collector with explicit authorization and an approved evidence-handling process.

## Signing and release

`scripts/build.sh` applies an ad-hoc signature suitable for development testing. Before external production distribution, sign with an organization-controlled Developer ID Application certificate, apply the organization's approved entitlements (if any), submit the exact artifact for Apple notarization, staple/validate where applicable, and regenerate the checksum after the final signed artifact is produced. Do not place signing credentials in this repository.

Gatekeeper behavior varies with distribution method and organizational policy. Test the final notarized binary on a representative clean Apple Silicon Mac, including Full Disk Access behavior and evidence-container opening, before release.

## Security

Do not report vulnerabilities or suspected evidence exposure in a public issue. Follow [SECURITY.md](SECURITY.md) and use GitHub's private vulnerability-reporting feature.

## Documentation and license

- [Operator guide](docs/OPERATOR.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [AGPL-3.0-or-later license](LICENSE)

The corresponding packaging source must accompany distribution as required by the bundled AGPL software. See `THIRD_PARTY_NOTICES.md` for upstream projects and license responsibilities.
