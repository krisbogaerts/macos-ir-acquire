# Acquire macOS arm64 one-file package

This repository packages Fox-IT's Acquire for authorized incident-response and forensic collection on Apple Silicon Macs. It produces a single PyInstaller executable that an operator runs as `sudo ./acquire`; the embedded defaults use Acquire's full macOS profile, raw-filesystem fallback, and gzip compression.

The package is intentionally a thin launcher around upstream Acquire rather than a new collector. It requires no Python installation on the target Mac and writes the evidence archive, collection report, and log to the current directory. PyInstaller one-file execution creates a temporary `_MEI…` extraction directory, so the result is not fileless.

## Pinned build

- Python 3.10
- Acquire 3.22
- dissect.target 3.25.1
- dissect.apfs 1.1
- PyInstaller 6.21.0

All transitive versions and hashes are recorded in `requirements.lock`.

## Build on Apple Silicon

Install `uv` and Apple command-line developer tools, then run from the repository root:

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

## Operator use

Follow the [operator guide](docs/OPERATOR.md). The target command is:

```bash
sudo ./acquire
```

Root is preferred, but Full Disk Access is still needed for the best macOS coverage. Collection can include sensitive browser history, cookies, saved-login databases, shell history, logs, persistence data, SSH metadata, and other user/system artifacts. Only use the collector with explicit authorization and an approved evidence-handling process.

## Signing and release

`scripts/build.sh` applies an ad-hoc signature suitable for development testing. Before external production distribution, sign with an organization-controlled Developer ID Application certificate, apply the organization's approved entitlements (if any), submit the exact artifact for Apple notarization, staple/validate where applicable, and regenerate the checksum after the final signed artifact is produced. Do not place signing credentials in this repository.

Gatekeeper behavior varies with distribution method and organizational policy. Test the final notarized binary on a representative clean Apple Silicon Mac, including Full Disk Access behavior and evidence-container opening, before release.

## Project records

- [Design specification](docs/superpowers/specs/2026-08-03-acquire-macos-arm64-package-design.md)
- [Implementation plan](docs/superpowers/plans/2026-08-03-acquire-macos-arm64-package.md)
- [Operator guide](docs/OPERATOR.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

The corresponding packaging source must accompany distribution as required by the bundled AGPL software. See `THIRD_PARTY_NOTICES.md` for upstream projects and license responsibilities.
