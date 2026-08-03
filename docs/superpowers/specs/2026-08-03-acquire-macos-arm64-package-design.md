# Acquire macOS Apple Silicon Package Design

## Objective

Build a single Apple Silicon executable named `acquire` that packages Fox-IT Acquire 3.22 for authorized macOS live-response collection. The operator runs:

```bash
sudo ./acquire
```

The package must load its embedded Python runtime, Python modules, and Dissect plugins from memory. It must not extract an interpreter or support files onto the target filesystem. Acquire will write its evidence archive, execution report, and log to the operator's current directory.

## Scope

This project packages upstream Acquire; it does not reimplement or extend its forensic collectors. The only custom runtime code is a small launcher that performs practical preflight checks and then calls `acquire.acquire.main()`.

The first release targets native `arm64` macOS only. Acquire runs as root and is intended only for systems on which collection is authorized.

## Pinned Baseline

- Acquire: `3.22`
- Embedded Python: `3.10`
- PyOxidizer: `0.24.0`
- Architecture: `aarch64-apple-darwin`
- Dissect dependencies: resolved within Acquire's declared compatible ranges and locked by exact version and hash for reproducible builds
- Raw macOS filesystem support: include `dissect.apfs` and its required dependencies

The build records the Acquire tag/commit, dependency versions, input hashes, build-host macOS version, Apple SDK version, PyOxidizer version, and final executable SHA-256.

## Runtime Defaults

An embedded `acquire.config` uses Acquire's supported configuration interface:

```python
CONFIG = {
    "arguments": [
        "--profile", "full",
        "--fallback",
        "--compress",
        "--compress-method", "gzip",
    ]
}
```

This makes `sudo ./acquire` perform a compressed full-profile collection. Normal CLI arguments continue to override configured defaults, so an investigator can explicitly select another profile or output setting.

Output remains in the current directory because a reliable external drive or fixed destination cannot be assumed. Operators are instructed to launch the executable from a dedicated case directory and upload the resulting archive, report, and log.

Encryption is not enabled by default because no organization public key has been supplied. It can be added later through Acquire's existing public-key encryption configuration without changing collection logic.

## Preflight Launcher

The in-memory launcher performs only these checks:

1. Require effective UID 0. If not root, print `Run with: sudo ./acquire` and exit without starting collection.
2. Resolve the current working directory and confirm it is a writable directory.
3. Read available capacity for the output filesystem with `shutil.disk_usage()`.
4. Stop when less than 5 GiB is available.
5. Print a warning, but continue automatically, when less than 20 GiB is available.
6. Print the output directory and available capacity before calling `acquire.acquire.main()`.

The launcher does not recursively scan the target to estimate acquisition size. Such a scan would add delay and filesystem access while still failing to predict compressed output accurately. It creates no preflight files and changes no Acquire collection behavior.

## Packaging Architecture

PyOxidizer embeds the following into one native executable:

- CPython 3.10 runtime
- Acquire 3.22
- required Dissect packages, including APFS support
- native extension modules needed by those packages
- the generated static `dissect.target` plugin list
- the embedded Acquire defaults
- the preflight launcher
- required package metadata and data resources

`target-build-pluginlist` runs during the build against the exact locked Dissect environment. The generated `_pluginlist.py` is included before PyOxidizer freezes resources. This replaces runtime plugin discovery, which does not work reliably from an in-memory frozen package.

The PyOxidizer entry module is the preflight launcher. After successful checks, the launcher imports and invokes upstream `acquire.acquire.main()` in the same process.

## Collection Flow

```text
sudo ./acquire
  -> native arm64 Mach-O is mapped by macOS
  -> embedded Python/resources load from memory
  -> preflight validates root, output path, and free capacity
  -> Acquire opens the local target, preferring raw access
  -> --fallback permits OS-level access when required
  -> full macOS profile streams artifacts into compressed TAR output
  -> Acquire writes its JSON execution report and log
  -> operator uploads archive, report, and log
```

The executable itself must exist on a filesystem for macOS to launch it. "In memory" means that the embedded Python environment is not unpacked into a temporary directory. macOS and the source filesystem can still record execution and file access.

## macOS Evidence Included by the Full Profile

Upstream Acquire 3.22 controls the exact artifact paths. The full macOS profile includes:

- `/etc` and `/usr/local/etc`
- selected user shell histories, shell configuration, application configuration, user LaunchAgents, preferences, and logs
- `/var/log`, `/var/db`, audit, cron/at, runtime, Unified Log data, sleep image, swap files, and selected notification data
- FSEvents
- system and user LaunchAgents, LaunchDaemons, and StartupItems
- kernel extensions
- system and user preferences
- installation history, macOS version information, DHCP leases, and application `Info.plist` metadata
- Safari history, bookmarks, downloads, extensions, last session, and cache database
- Chrome, Chromium, Edge, and Brave history/profile databases and selected session, cookie, login, bookmark, favicon, top-sites, and web-data artifacts
- Firefox profile SQLite databases
- SSH configuration and metadata, excluding private keys unless explicitly requested
- Docker logs and configuration selected by Acquire

Acquire's current macOS volatile profile is empty. This build therefore does not claim comprehensive collection of live processes, sockets, clipboard, RAM, current sessions, Mail, Messages, Keychain secrets, or every third-party browser. No custom volatile modules are added.

## Permissions and macOS Privacy

Root is required for the intended raw-device collection path. `sudo` does not universally bypass macOS Transparency, Consent, and Control protections. Raw APFS acquisition may provide artifacts unavailable through normal filesystem APIs; fallback access can still encounter Full Disk Access restrictions. Acquire's report and log are the authoritative record of collected, skipped, and failed artifacts.

The release documentation will recommend granting Full Disk Access to the terminal or deployment context when organizational policy permits it. The package will not attempt to alter TCC, SIP, quarantine, or other security controls.

## Output and Evidence Handling

Acquire creates and incrementally writes the compressed evidence archive plus its JSON execution report and log. These are intentional writes to the investigated device because no external destination is available. The operator must upload all three outputs and retain them together.

The package does not silently upload, delete, quarantine, or clean up files. It leaves incomplete outputs in place after interruption or an out-of-space failure so investigators can identify and handle them explicitly.

## Signing, Distribution, and Licensing

Development builds may use ad-hoc signing for local validation. A production release should use a Developer ID signature and Apple notarization when credentials are available. Signing status, executable SHA-256, and verification instructions accompany each release.

Acquire and much of Dissect are AGPL-3.0-or-later. Distribution must include the applicable license notices and provide recipients the corresponding source and build scripts. The runtime remains one executable; compliance files and source can be distributed alongside it through the delivery portal.

## Failure Handling

- Non-root execution: fail before Acquire starts.
- Invalid or unwritable current directory: fail before Acquire starts.
- Less than 5 GiB free: fail before Acquire starts.
- Less than 20 GiB free: warn and continue.
- Missing raw-device/APFS capability: allow Acquire's `--fallback` behavior and record the limitation.
- Permission/TCC denial: continue where upstream Acquire permits and preserve failures in its report/log.
- Collection exception or out-of-space condition: preserve upstream exit status and leave outputs for review.
- Missing frozen module or plugin: treat as a build-validation failure; do not release the executable.

## Verification

The build is not considered releasable until all of the following pass:

1. Unit tests cover root rejection, unwritable output, hard capacity failure, low-capacity warning, and successful delegation to Acquire.
2. Dependency lock and hashes verify cleanly.
3. The generated Dissect plugin list is present and non-empty.
4. The binary reports a native `arm64` Mach-O architecture.
5. `codesign --verify --strict` passes for the selected signing mode.
6. `sudo ./acquire --help` starts without extracting a PyInstaller-style temporary tree.
7. A controlled `--profile none` smoke acquisition produces a valid report/log and exits successfully.
8. A controlled full-profile macOS acquisition is opened successfully by the supported Dissect analysis tooling, and its report is reviewed for unexpected module/plugin failures.
9. The final executable SHA-256 and software bill of materials are generated.

## Deliverables

- PyOxidizer configuration
- minimal preflight launcher and tests
- embedded Acquire configuration
- reproducible dependency lock
- deterministic plugin-list generation/build script
- Apple Silicon `acquire` executable
- checksum and software bill of materials
- signing/notarization helper commands
- operator instructions for execution, output upload, privacy permissions, and limitations
- license notices and corresponding-source instructions

