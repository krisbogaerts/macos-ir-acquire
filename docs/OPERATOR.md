# Acquire for macOS: Operator Guide

## Authorized use and privacy

Run this collector only on a Mac you are authorized to acquire. The archive can contain highly sensitive user data, including browsing records, cookies, saved-login databases, shell history, preferences, and SSH metadata.

Root does not universally bypass macOS privacy controls. Grant **Full Disk Access** to the Terminal application, remote-management agent, or other execution context when your policy permits it. Keep the Mac awake and connected to power during collection.

## Run

Create a dedicated local case directory with enough free space, restrict access to authorized personnel, and avoid shared or cloud-synchronized folders. Place the extracted release files in it, open Terminal in that directory, and verify the executable before running it:

```bash
umask 077
shasum -a 256 -c acquire.sha256
xattr -d com.apple.quarantine ./acquire
sudo ./acquire
```

Continue only if checksum verification reports `acquire: OK`. Remove quarantine only from a release obtained from a trusted source after its checksums have been verified.

The embedded defaults select Acquire's full macOS profile and a gzip-compressed tar archive. Filesystem fallback is disabled, so Acquire will not switch to OS-level filesystem access when raw filesystem parsing is unsupported. No external disk is required; output is written beside the executable. The launcher stops below 5 GiB free and warns below 20 GiB, but this does not guarantee that a full acquisition will fit.

Do not interrupt the process unless necessary. Preserve the console output if an error occurs.

## Upload

Upload all generated evidence from the case directory:

- the evidence archive (normally a `.tar.gz` file);
- the matching `.report.json` collection report;
- the matching `.log` execution log.

Do not rename, edit, recompress, or delete partial output before consulting the investigator. Use an approved encrypted upload channel because the archive may contain credentials-related databases and personal data.

## Verify

If `acquire.sha256` was supplied with the binary, verify it before execution from the directory containing both files:

```bash
shasum -a 256 -c acquire.sha256
codesign --verify --strict --verbose=2 acquire
```

The development build is ad-hoc signed. A production release should carry the organization's Developer ID signature and notarization.

## Filesystem impact

PyInstaller one-file mode first extracts Python and bundled dependencies into a temporary `_MEI…` directory. It normally removes this directory on clean exit, but interruption or a crash can leave it behind. Acquire also writes its archive, report, and log to the current directory. The executable may be memory-mapped while running, but this package is **not fileless** and is not zero-footprint.

The acquisition itself reads many files and may affect access-time metadata where the filesystem or mount configuration records it. Running the program also creates normal macOS process, security, and audit traces.

## Coverage and gaps

Acquire 3.22's full macOS profile includes selected:

- `/etc`, user-home configuration, preferences, shell histories, user LaunchAgents, and user logs;
- `/var` logs and databases, Unified Log backing data, FSEvents, audit data, notification-center data, and selected sleep/swap files when accessible;
- system and user persistence locations, kernel extensions, installed-application metadata, receipts, system version, preferences, and DHCP leases;
- Safari bookmarks, downloads, extensions, history, last-session and cache database;
- Firefox profile SQLite databases;
- Chrome, Chromium, Edge, and Brave history, cookies, bookmarks, sessions/tabs, favicons, login databases, top sites, and web data;
- SSH configuration and metadata (private-key files are skipped by default) and selected Docker configuration/log artifacts.

Collection is path/profile based, not a guarantee that every artifact exists or was readable. macOS privacy controls, SIP, open/locked databases, APFS behavior, permissions, version changes, or disk pressure can create gaps. Acquire 3.22 defines no macOS volatile profile, so this package does not claim comprehensive running-process, socket, RAM, clipboard, Mail, Messages, Keychain-secret, or every-browser collection. Review the `.report.json` and `.log` for successful, missing, empty, and failed artifacts before drawing conclusions.

## If the run fails

Keep every generated file and the console output. Record the Mac model, macOS version, execution time, available disk space, whether Full Disk Access was granted, and the exact error. Do not simply rerun into the same directory unless the investigator approves it.
