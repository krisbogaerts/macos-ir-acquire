# Third-Party Notices and Corresponding Source

This package redistributes Python, Acquire, Dissect modules, PyInstaller's bootloader, and the dependencies listed in `requirements.lock` and the generated `dist/SBOM.txt`. Those inventories are part of the release record; they do not replace the license texts shipped by upstream projects.

## Acquire and Dissect

- [Acquire](https://github.com/fox-it/acquire), pinned here to version 3.22, is licensed under **AGPL-3.0-or-later**.
- [Dissect](https://github.com/fox-it/dissect) and its component packages, including [dissect.target](https://github.com/fox-it/dissect.target), are licensed under **AGPL-3.0-or-later**.

The packaging source in this repository—including the launcher, embedded configuration, dependency lock, PyInstaller specification, build scripts, and modifications—is the corresponding packaging source supplied to recipients. Anyone distributing the executable must also satisfy the applicable AGPL source and license-notice obligations for the exact release they distribute. Preserve upstream copyright and license notices.

## PyInstaller

[PyInstaller](https://github.com/pyinstaller/pyinstaller), pinned here to version 6.21.0, is distributed primarily under **GPL-2.0-or-later with a special exception for distributing executables produced by PyInstaller**; certain files use the Apache License 2.0. The exception does not override the licenses of bundled dependencies. See PyInstaller's [license documentation](https://pyinstaller.org/en/stable/license.html) and the license files for the pinned source release.

## Complete inventory

- `requirements.lock` is the hash-locked build dependency inventory.
- `dist/SBOM.txt` is generated from the environment used for the release.
- Upstream source archives and their license files should be retained with the internal release record.

This notice is operational guidance, not legal advice. The distributing organization remains responsible for its license review and source-offer process.
