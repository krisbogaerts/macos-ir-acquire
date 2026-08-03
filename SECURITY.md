# Security Policy

## Supported versions

Security fixes are applied to the current `main` branch and the latest published release. Older binaries and source snapshots are not supported.

## Reporting a vulnerability

Use GitHub's private vulnerability-reporting feature: open the repository's **Security** tab, select **Advisories**, and choose **Report a vulnerability**. Do not open a public issue for a suspected vulnerability, credential exposure, or forensic-data leak.

Include the affected commit or release checksum, macOS and hardware version, reproduction steps, expected and observed behavior, and an impact assessment. Do not attach real acquired evidence, credentials, browser data, private keys, or other personal information. Use synthetic test data and redact hostnames, usernames, and paths.

You should receive an acknowledgement within five business days. Publication and disclosure timing will be coordinated after validation and remediation.

## Scope

Reports about the packaging launcher, PyInstaller configuration, build/release process, or unsafe interaction with upstream Acquire are in scope. Vulnerabilities that reproduce in an unmodified upstream dependency should also be reported privately to that project's maintainers.
