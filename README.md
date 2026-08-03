# Acquire macOS arm64 one-file package

This repository packages [Fox-IT Acquire](https://docs.dissect.tools/en/latest/tools/acquire.html) for authorized incident-response and forensic collection on Apple Silicon Macs. It produces a single PyInstaller executable that an operator runs with `sudo ./acquire`. No Python installation or external disk is required on the target Mac.

The package is a thin launcher around upstream Acquire rather than a custom collector. Its embedded defaults select Acquire's full macOS profile, write a gzip-compressed tar evidence archive, and disable filesystem fallback. The evidence archive, collection report, and execution log are written to the current directory.

PyInstaller one-file mode extracts its bundled runtime to a temporary `_MEI…` directory before execution. The package is therefore not fileless or zero-footprint.

## Pinned build

- Python 3.10
- Acquire 3.22
- dissect.target 3.25.1
- dissect.apfs 1.1
- PyInstaller 6.21.0

All transitive versions and hashes are recorded in `requirements.lock`.

## Build on Apple Silicon

Install `uv` 0.11.x and Apple command-line developer tools, then run from the repository root. CI pins uv 0.11.16.

```bash
./scripts/build.sh
./scripts/verify_release.sh
```

The build script creates `.venv`, installs the hash-locked dependencies, generates Dissect's plugin list, stages Acquire's embedded configuration, builds an arm64 PyInstaller one-file executable, and applies an ad-hoc development signature.

The verifier runs the tests, verifies the architecture and code signature, rejects PyInstaller sidecar directories, creates the software inventory and checksums, and packages the release.

Generated files under `dist/` are:

- `acquire` — arm64 one-file executable;
- `acquire.sha256` — executable SHA-256 checksum;
- `SBOM.txt` — installed-package inventory;
- `LICENSE` and `THIRD_PARTY_NOTICES.md` — source and third-party license terms;
- `acquire-macos-arm64.tar.gz` — release archive that preserves executable permissions;
- `acquire-macos-arm64.tar.gz.sha256` — release-archive SHA-256 checksum.

## Operator use

### Before collection

Run this collector only on a Mac you are authorized to acquire. Its output can contain highly sensitive data, including browser records, cookies, saved-login databases, shell history, preferences, and SSH metadata.

Use a dedicated local, access-controlled case directory. Avoid shared and cloud-synchronized folders, keep the Mac connected to power, and start with at least 20 GiB of free space when practical. The launcher refuses to start below 5 GiB and warns below 20 GiB, but neither threshold guarantees that a complete acquisition will fit.

Root does not bypass every macOS privacy control. For the best coverage, open **System Settings → Privacy & Security → Full Disk Access**, enable the Terminal or execution application, and restart it if macOS requests this.

### Download, verify, and run

Place `acquire-macos-arm64.tar.gz` and `acquire-macos-arm64.tar.gz.sha256` in the approved case directory. In Terminal, change to that directory and restrict permissions on newly created files:

```bash
cd "/path/to/approved-case-directory"
umask 077
shasum -a 256 -c acquire-macos-arm64.tar.gz.sha256
```

Continue only when the checksum command reports:

```text
acquire-macos-arm64.tar.gz: OK
```

Extract the release into a new directory:

```bash
mkdir acquire-macos-arm64
tar -xzf acquire-macos-arm64.tar.gz -C acquire-macos-arm64
cd acquire-macos-arm64
shasum -a 256 -c acquire.sha256
```

Continue only when the executable checksum reports `acquire: OK`. You can also verify its code signature:

```bash
codesign --verify --strict --verbose=2 acquire
```

After verifying the checksums and trusting the release source, remove Gatekeeper's quarantine attribute and start collection:

```bash
xattr -d com.apple.quarantine ./acquire
sudo ./acquire
```

Enter the administrator password when prompted. Leave the terminal open and do not interrupt collection unless necessary. Preserve the console output if an error occurs.

The development release is ad-hoc signed rather than Apple-notarized, which is why Gatekeeper can block a downloaded executable. Only remove quarantine from the checksum-verified `acquire` file obtained from a trusted source.

### Preserve and upload the results

Acquire writes the following collection files into the current extracted directory:

- the evidence archive, normally ending in `.tar.gz`;
- the matching `.report.json` collection report;
- the matching `.log` execution log.

Upload all generated collection files through the approved encrypted evidence channel. Do not rename, edit, recompress, or delete partial output before consulting the investigator.

If collection fails, retain every generated file and the console output. Record the Mac model, macOS version, execution time, available disk space, whether Full Disk Access was granted, and the exact error. Do not rerun into the same directory unless the investigator approves it.

## Forensic coverage and limitations

Acquire 3.22's full macOS profile includes selected:

- system configuration, user preferences, shell histories, LaunchAgents, and user logs;
- `/var` logs and databases, Unified Log backing data, FSEvents, audit data, Notification Center data, and selected sleep or swap files when accessible;
- system and user persistence locations, kernel extensions, application metadata, package receipts, system-version data, preferences, and DHCP leases;
- Safari bookmarks, downloads, extensions, history, last-session data, and cache databases;
- Firefox profile SQLite databases;
- Chrome, Chromium, Edge, and Brave history, cookies, bookmarks, sessions and tabs, favicons, login databases, top sites, and web data;
- SSH configuration and metadata, with private-key files skipped by default;
- selected Docker configuration and log artifacts.

Coverage is path- and profile-based. It does not guarantee that every artifact exists or can be read. Full Disk Access, other macOS privacy controls, System Integrity Protection, permissions, locked or open databases, APFS behavior, macOS version changes, and available disk space can all create gaps.

Acquire 3.22 defines no macOS volatile profile. This package does not claim comprehensive collection of running processes, network sockets, RAM, clipboard data, Mail, Messages, Keychain secrets, or every browser. Review the `.report.json` and `.log` files for successful, missing, empty, and failed artifacts before drawing conclusions.

## Filesystem impact

PyInstaller extracts Python and bundled dependencies into a temporary `_MEI…` directory. It normally removes that directory after a clean exit, but a crash or interruption can leave it behind. Acquire also writes its archive, report, and log to the current directory.

The acquisition reads many files and can affect access-time metadata where the filesystem or mount configuration records it. Execution also creates normal macOS process, security, and audit traces.

Filesystem fallback is disabled: Acquire will not switch to operating-system-level filesystem access when raw filesystem parsing is unsupported.

## Signing and release

`scripts/build.sh` applies an ad-hoc signature suitable for development testing. Before external production distribution:

1. Sign the executable with an organization-controlled Developer ID Application certificate.
2. Apply the organization's approved entitlements, if any.
3. Submit the exact signed artifact for Apple notarization.
4. Staple and validate the notarization where applicable.
5. Regenerate checksums after producing the final signed artifact.

Never place signing credentials in this repository. Test the final notarized binary on a representative clean Apple Silicon Mac, including Full Disk Access behavior and evidence-container opening.

## Security and license

Do not report vulnerabilities or suspected evidence exposure in a public issue. Follow [SECURITY.md](SECURITY.md) and use GitHub's private vulnerability-reporting feature.

- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [AGPL-3.0-or-later license](LICENSE)

The corresponding packaging source must accompany distribution as required by the bundled AGPL software. See `THIRD_PARTY_NOTICES.md` for upstream projects and license responsibilities.
