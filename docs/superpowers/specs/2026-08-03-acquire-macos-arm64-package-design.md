# Acquire macOS Apple Silicon PyInstaller Package Design

## Objective

Package Fox-IT Acquire 3.22 as one native Apple Silicon executable for authorized macOS live-response collection. The operator runs:

```bash
sudo ./acquire
```

The deliverable is one PyInstaller `--onefile` executable. At runtime, PyInstaller extracts its embedded Python runtime and bundled dependencies into a temporary `_MEI…` directory, launches Acquire, and normally removes the directory when the process exits. This temporary extraction is accepted and must be documented as collection impact.

## Scope

The project packages upstream Acquire without changing its forensic collection modules. Custom runtime behavior is limited to:

- a small preflight launcher;
- Acquire's supported embedded default configuration;
- a generated static Dissect plugin list required by frozen applications.

The first release targets native `arm64` macOS only and is intended to run as root on systems where collection is authorized.

## Pinned Baseline

- Acquire: `3.22`
- Python: `3.10`
- PyInstaller: `6.21.0`
- Architecture: `arm64`
- Raw macOS filesystem support: `dissect.apfs`
- All transitive dependencies: exact versions and hashes in a committed lock file

Python 3.10 is installed into a workspace-local virtual environment with `uv`. The binary is built on Apple Silicon because PyInstaller is not a cross-compiler.

## Runtime Defaults

An embedded `acquire.config` uses Acquire's supported configuration interface:

```python
CONFIG = {
    "arguments": [
        "--profile", "full",
        "--output-type", "tar",
        "--no-compress",
    ]
}
```

This makes `sudo ./acquire` perform a full-profile collection into an uncompressed tar archive. Filesystem fallback is disabled. Explicit CLI arguments continue to override these defaults.

Output remains in the current directory. The operator runs the binary from a dedicated case directory and uploads the resulting evidence archive, JSON report, and log. Encryption and automatic upload remain disabled because no organization public key or upload endpoint has been supplied.

## Preflight Launcher

Before delegating to `acquire.acquire.main()`, the launcher:

1. Requires effective UID 0.
2. Resolves and checks the current output directory.
3. Reads free space with `shutil.disk_usage()`.
4. Stops below 5 GiB free.
5. Warns but continues below 20 GiB free.
6. Prints the output directory, free capacity, and PyInstaller extraction directory when present.

The launcher does not recursively estimate artifact sizes, create its own log, upload data, or alter collection behavior.

## Packaging Architecture

The PyInstaller spec bundles:

- CPython 3.10;
- Acquire 3.22;
- required Dissect packages, including APFS support;
- Acquire and Dissect package data;
- all required Dissect submodules discovered by PyInstaller hooks;
- the generated `dissect.target` static plugin list;
- `acquire.config`;
- the preflight launcher.

`target-build-pluginlist` runs in the exact locked Python environment before PyInstaller analysis. It writes `_pluginlist.py` into the build environment's installed `dissect.target` package. The supported `acquire.config` module is similarly staged into the installed Acquire package. PyInstaller then analyzes this prepared environment.

The entry script is the preflight launcher. It imports Acquire only after preflight succeeds.

## Runtime Flow and Filesystem Impact

```text
sudo ./acquire
  -> macOS launches the signed arm64 bootloader
  -> PyInstaller creates a temporary _MEI… directory
  -> embedded Python and dependencies are extracted there
  -> preflight validates root, output path, and free capacity
  -> Acquire opens the local target, preferring raw access
  -> no filesystem fallback is enabled
  -> full macOS profile writes an uncompressed tar evidence archive
  -> Acquire writes its JSON report and log
  -> PyInstaller normally removes _MEI… on clean exit
  -> operator uploads archive, report, and log
```

The collector is not fileless and does not run solely from memory. Abrupt termination, a crash, or power loss can leave the `_MEI…` directory behind. The operator documentation identifies this behavior and prohibits presenting the collector as zero-footprint.

## macOS Evidence Included by the Full Profile

Upstream Acquire 3.22 controls exact paths. Its full macOS profile includes selected:

- system configuration under `/etc` and `/usr/local/etc`;
- shell history, user configuration, user preferences, user LaunchAgents, and logs;
- `/var` logs and databases, audit and scheduled-task data, Unified Log data, sleep image, swap files, and notification data;
- FSEvents;
- system LaunchAgents, LaunchDaemons, StartupItems, extensions, preferences, installation history, OS metadata, and DHCP leases;
- application `Info.plist` metadata;
- Safari, Chrome, Chromium, Edge, Brave, and Firefox artifacts defined by Acquire's History module;
- SSH configuration and metadata, excluding private keys unless explicitly requested;
- selected Docker logs and configuration.

Acquire 3.22 has no macOS volatile-profile modules. This build does not claim comprehensive process, socket, RAM, clipboard, current-session, Mail, Messages, Keychain-secret, or every-browser collection.

## Permissions and macOS Privacy

Root is required for the intended raw-device path. `sudo` does not universally bypass macOS Transparency, Consent, and Control restrictions. The operator guidance recommends Full Disk Access for the execution context when organizational policy permits it. The package does not change TCC, SIP, quarantine, or other security controls.

Acquire's report and log are the authoritative record of collected, skipped, and failed artifacts.

## Signing and Distribution

Development builds receive an ad-hoc signature. Production releases should use an organization-controlled Developer ID Application certificate and Apple notarization. The release includes the executable SHA-256, dependency inventory, signature verification commands, and corresponding source/build scripts.

Acquire and much of Dissect are AGPL-3.0-or-later. PyInstaller is GPL-2.0-or-later with an exception allowing distribution of bundled applications. Applicable notices and corresponding-source obligations accompany distribution.

## Failure Handling

- Non-root, invalid output directory, or less than 5 GiB free: stop before Acquire collection.
- Less than 20 GiB free: warn and continue.
- Raw APFS failure: do not fall back to OS-level filesystem access; preserve the limitation in Acquire output.
- TCC or file-permission denial: continue where upstream Acquire permits and record failures.
- Missing frozen import/plugin: fail build or acceptance testing; do not release.
- Interrupted execution: preserve partial evidence and warn that `_MEI…` cleanup may be incomplete.

## Verification

A release must pass:

1. Unit tests for every preflight branch and default configuration.
2. Hash verification for locked dependencies.
3. Non-empty generated Dissect plugin list.
4. Native arm64 Mach-O inspection.
5. Strict code-signature verification.
6. Frozen `--help`/launcher smoke test.
7. Controlled root `--profile none` acquisition.
8. Confirmation that `_MEI…` is used during execution and normally removed afterward.
9. Controlled full-profile acquisition with report/log review.
10. Successful opening of the evidence container using Dissect tooling.
11. Final SHA-256 and software inventory generation.

## Deliverables

- dependency inputs and hash-locked requirements;
- minimal launcher and tests;
- embedded Acquire configuration;
- deterministic plugin-list staging;
- PyInstaller spec and build scripts;
- native Apple Silicon `acquire` executable;
- checksum and software inventory;
- signature/notarization guidance;
- operator and forensic-impact documentation;
- license notices and corresponding-source instructions.
