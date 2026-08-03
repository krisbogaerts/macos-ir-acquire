# Acquire macOS Apple Silicon PyInstaller Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and verify one native Apple Silicon PyInstaller executable that runs upstream Acquire 3.22 through `sudo ./acquire`, using the full macOS profile by default.

**Architecture:** A minimal Python launcher performs root and free-space preflight, reports PyInstaller's `_MEI…` extraction path, and delegates to unmodified `acquire.acquire.main()`. A prepared Python 3.10 environment contains locked Acquire/Dissect dependencies, an embedded Acquire configuration, and a generated static Dissect plugin list before PyInstaller performs one-file analysis.

**Tech Stack:** Python 3.10, Acquire 3.22, Dissect, `dissect.apfs`, PyInstaller 6.21.0, `uv`, `pytest`, macOS `codesign`.

## Global Constraints

- Build and run natively on Apple Silicon (`arm64`); PyInstaller is not a cross-compiler.
- Pin Acquire to `3.22`, Python to `3.10`, and PyInstaller to `6.21.0`.
- Do not alter upstream Acquire collection modules or add macOS volatile modules.
- Build exactly one runtime deliverable with PyInstaller `--onefile` behavior.
- Explicitly document and verify temporary `_MEI…` extraction; never call the result fileless, memory-only, or zero-footprint.
- Default arguments are exactly `--profile full --output-type tar --no-compress`.
- Require effective UID 0; stop below 5 GiB free and warn below 20 GiB free.
- Write evidence to the current directory; do not upload, encrypt, delete, quarantine, or clean up automatically.
- Preserve Acquire's archive, JSON report, log, exit behavior, and CLI overrides.
- Do not release until frozen imports, plugin loading, architecture, signature, smoke acquisition, cleanup observation, and evidence-container opening pass.

## File Map

- `pyproject.toml` — local launcher project and pytest configuration.
- `.gitignore` — build environment, caches, binaries, and collected evidence.
- `requirements.in` — direct pinned build/runtime inputs.
- `requirements.lock` — exact Python 3.10 Apple Silicon dependency versions and hashes.
- `src/acquire_launcher/__init__.py` — launcher API and Acquire delegation.
- `src/acquire_launcher/preflight.py` — deterministic preflight decision logic and host probes.
- `src/acquire_launcher/__main__.py` — PyInstaller entry script.
- `packaging/acquire_config.py` — supported embedded Acquire defaults.
- `scripts/prepare_environment.py` — installs locked dependencies and stages config/plugin registry into the virtual environment.
- `acquire.spec` — PyInstaller one-file analysis, hidden imports, package data, signing inputs, and executable definition.
- `scripts/build.sh` — clean deterministic build and ad-hoc development signing.
- `scripts/verify_release.sh` — tests, architecture/signature checks, checksum, and dependency inventory.
- `tests/test_preflight.py` — all preflight branches and extraction-path reporting.
- `tests/test_acquire_config.py` — default-argument contract.
- `tests/test_prepare_environment.py` — deterministic staging behavior.
- `tests/test_spec_contract.py` — one-file, arm64, entry-point, and hidden-import assertions.
- `docs/OPERATOR.md` — execution, upload, privacy, disk impact, and evidence coverage.
- `THIRD_PARTY_NOTICES.md` — Acquire/Dissect/PyInstaller licenses and source availability.
- `README.md` — build and verification entry points.

---

### Task 1: Implement the Minimal Preflight Launcher

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `src/acquire_launcher/__init__.py`
- Create: `src/acquire_launcher/preflight.py`
- Create: `src/acquire_launcher/__main__.py`
- Create: `packaging/acquire_config.py`
- Create: `tests/test_preflight.py`
- Create: `tests/test_acquire_config.py`

**Interfaces:**
- Produces: `PreflightResult(allowed: bool, warning: bool, message: str)`.
- Produces: `evaluate_preflight(euid: int, output_dir: Path, writable: bool, free_bytes: int) -> PreflightResult`.
- Produces: `runtime_extraction_path() -> Path | None`.
- Produces: `run_preflight() -> PreflightResult`.
- Produces: `acquire_launcher.main() -> int`, delegating to `acquire.acquire.main()` only after preflight succeeds.
- Produces: `packaging/acquire_config.py::CONFIG` with exact packaged defaults.

- [ ] **Step 1: Create local project metadata and ignore generated state**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=77", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "acquire-macos-launcher"
version = "0.1.0"
requires-python = ">=3.10"

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
include = ["acquire_launcher*"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `.gitignore`:

```gitignore
.venv/
.uv-cache/
__pycache__/
.pytest_cache/
build/
dist/
*.pyc
*.tar
*.tar.gz
*.zip
*.report.json
Acquire_*.log
```

- [ ] **Step 2: Write failing preflight tests**

Create `tests/test_preflight.py`:

```python
import sys
from pathlib import Path

from acquire_launcher.preflight import GIB, evaluate_preflight, runtime_extraction_path


def test_rejects_non_root():
    result = evaluate_preflight(501, Path("/case"), True, 100 * GIB)
    assert result.allowed is False
    assert result.message == "Run with: sudo ./acquire"


def test_rejects_unwritable_output():
    result = evaluate_preflight(0, Path("/case"), False, 100 * GIB)
    assert result.allowed is False
    assert result.message == "Output directory is not writable: /case"


def test_rejects_less_than_five_gib():
    result = evaluate_preflight(0, Path("/case"), True, 5 * GIB - 1)
    assert result.allowed is False
    assert "at least 5.0 GiB" in result.message


def test_warns_below_twenty_gib():
    result = evaluate_preflight(0, Path("/case"), True, 10 * GIB)
    assert result.allowed is True
    assert result.warning is True
    assert "10.0 GiB available" in result.message


def test_allows_twenty_gib_or_more():
    result = evaluate_preflight(0, Path("/case"), True, 20 * GIB)
    assert result.allowed is True
    assert result.warning is False
    assert "20.0 GiB available" in result.message


def test_reports_pyinstaller_extraction_path(monkeypatch):
    monkeypatch.setattr(sys, "_MEIPASS", "/private/tmp/_MEI123", raising=False)
    assert runtime_extraction_path() == Path("/private/tmp/_MEI123")


def test_returns_none_outside_frozen_runtime(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    assert runtime_extraction_path() is None
```

- [ ] **Step 3: Run the tests and confirm the expected import failure**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --python 3.10 --with pytest pytest tests/test_preflight.py -v
```

Expected: fail with `ModuleNotFoundError: No module named 'acquire_launcher'`.

- [ ] **Step 4: Implement preflight and extraction-path reporting**

Create `src/acquire_launcher/preflight.py`:

```python
from __future__ import annotations

import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

GIB = 1024**3
HARD_MIN_BYTES = 5 * GIB
WARN_MIN_BYTES = 20 * GIB


@dataclass(frozen=True)
class PreflightResult:
    allowed: bool
    warning: bool
    message: str


def evaluate_preflight(euid: int, output_dir: Path, writable: bool, free_bytes: int) -> PreflightResult:
    if euid != 0:
        return PreflightResult(False, False, "Run with: sudo ./acquire")
    if not writable:
        return PreflightResult(False, False, f"Output directory is not writable: {output_dir}")

    free_gib = free_bytes / GIB
    if free_bytes < HARD_MIN_BYTES:
        return PreflightResult(
            False,
            False,
            f"Insufficient free space: {free_gib:.1f} GiB available; at least 5.0 GiB is required",
        )
    if free_bytes < WARN_MIN_BYTES:
        return PreflightResult(
            True,
            True,
            f"WARNING: only {free_gib:.1f} GiB available in {output_dir}; full acquisition may not fit",
        )
    return PreflightResult(True, False, f"Output: {output_dir} ({free_gib:.1f} GiB available)")


def runtime_extraction_path() -> Path | None:
    value = getattr(sys, "_MEIPASS", None)
    return Path(value) if value else None


def run_preflight() -> PreflightResult:
    output_dir = Path.cwd().resolve()
    return evaluate_preflight(
        euid=os.geteuid(),
        output_dir=output_dir,
        writable=output_dir.is_dir() and os.access(output_dir, os.W_OK),
        free_bytes=shutil.disk_usage(output_dir).free,
    )
```

Create `src/acquire_launcher/__init__.py`:

```python
from __future__ import annotations

import sys

from acquire_launcher.preflight import run_preflight, runtime_extraction_path


def main() -> int:
    extraction_path = runtime_extraction_path()
    if extraction_path:
        print(f"PyInstaller runtime extraction: {extraction_path}", file=sys.stderr)

    result = run_preflight()
    print(result.message, file=sys.stderr)
    if not result.allowed:
        return 2

    from acquire.acquire import main as acquire_main

    acquire_main()
    return 0
```

Create `src/acquire_launcher/__main__.py`:

```python
from acquire_launcher import main

raise SystemExit(main())
```

- [ ] **Step 5: Add the supported Acquire configuration and its contract test**

Create `packaging/acquire_config.py`:

```python
CONFIG = {
    "arguments": [
        "--profile",
        "full",
        "--output-type",
        "tar",
        "--no-compress",
    ]
}
```

Create `tests/test_acquire_config.py`:

```python
import importlib.util
from pathlib import Path


def test_embedded_arguments_are_exact():
    path = Path("packaging/acquire_config.py")
    spec = importlib.util.spec_from_file_location("acquire_config", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.CONFIG == {
        "arguments": [
            "--profile",
            "full",
            "--output-type",
            "tar",
            "--no-compress",
        ]
    }
```

- [ ] **Step 6: Run all Task 1 tests**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --python 3.10 --with pytest pytest tests/test_preflight.py tests/test_acquire_config.py -v
```

Expected: all tests pass.

- [ ] **Step 7: Commit the launcher**

```bash
git add .gitignore pyproject.toml src packaging tests/test_preflight.py tests/test_acquire_config.py
git commit -m "feat: add Acquire preflight launcher"
```

---

### Task 2: Lock Dependencies and Stage Acquire for Freezing

**Files:**
- Create: `requirements.in`
- Create: `requirements.lock`
- Create: `scripts/prepare_environment.py`
- Create: `tests/test_prepare_environment.py`

**Interfaces:**
- Consumes: `packaging/acquire_config.py`.
- Produces: a Python 3.10 `.venv` containing Acquire 3.22, `dissect.apfs`, PyInstaller 6.21.0, pytest, and the launcher.
- Produces: installed `acquire/config.py` and `dissect/target/plugins/_pluginlist.py` before PyInstaller analysis.
- Produces: `stage_generated_modules(config_source: Path, acquire_dir: Path, plugin_dir: Path, plugin_text: str) -> tuple[Path, Path]`.

- [ ] **Step 1: Define and generate the locked environment**

Create `requirements.in`:

```text
acquire==3.22
dissect.apfs>=1.1,<2
pyinstaller==6.21.0
pytest==8.4.2
```

Generate the lock:

```bash
UV_CACHE_DIR=.uv-cache uv pip compile requirements.in --python-version 3.10 --python-platform aarch64-apple-darwin --generate-hashes --output-file requirements.lock
```

Verify the lock contains exact entries for Acquire, PyInstaller, `dissect.target`, and `dissect.apfs`.

- [ ] **Step 2: Write the failing staging test**

Create `tests/test_prepare_environment.py`:

```python
from pathlib import Path

from scripts.prepare_environment import stage_generated_modules


def test_stages_config_and_pluginlist(tmp_path: Path):
    config = tmp_path / "acquire_config.py"
    config.write_text('CONFIG = {"arguments": ["--profile", "full"]}\n')
    acquire_dir = tmp_path / "site/acquire"
    plugin_dir = tmp_path / "site/dissect/target/plugins"

    config_out, plugin_out = stage_generated_modules(config, acquire_dir, plugin_dir, "PLUGINS = []\n")

    assert config_out == acquire_dir / "config.py"
    assert config_out.read_text() == config.read_text()
    assert plugin_out == plugin_dir / "_pluginlist.py"
    assert plugin_out.read_text() == "PLUGINS = []\n"
```

- [ ] **Step 3: Run the staging test and confirm failure**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --python 3.10 --with pytest pytest tests/test_prepare_environment.py -v
```

Expected: fail with `ModuleNotFoundError: No module named 'scripts.prepare_environment'`.

- [ ] **Step 4: Implement environment preparation**

Create `scripts/prepare_environment.py`:

```python
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def stage_generated_modules(
    config_source: Path,
    acquire_dir: Path,
    plugin_dir: Path,
    plugin_text: str,
) -> tuple[Path, Path]:
    if "PLUGIN" not in plugin_text.upper():
        raise ValueError("generated plugin list is empty or malformed")
    config_out = acquire_dir / "config.py"
    plugin_out = plugin_dir / "_pluginlist.py"
    acquire_dir.mkdir(parents=True, exist_ok=True)
    plugin_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_source, config_out)
    plugin_out.write_text(plugin_text)
    return config_out, plugin_out


def run(root: Path) -> None:
    venv = root / ".venv"
    python = venv / "bin/python"
    if not python.exists():
        subprocess.run(["uv", "venv", "--python", "3.10", str(venv)], check=True)
    subprocess.run(
        ["uv", "pip", "sync", "--python", str(python), str(root / "requirements.lock")],
        check=True,
    )
    subprocess.run(["uv", "pip", "install", "--python", str(python), str(root)], check=True)

    acquire_dir = Path(
        subprocess.run(
            [str(python), "-c", "import acquire, pathlib; print(pathlib.Path(acquire.__file__).parent)"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
    )
    plugin_dir = Path(
        subprocess.run(
            [
                str(python),
                "-c",
                "import dissect.target.plugins as p, pathlib; print(pathlib.Path(next(iter(p.__path__))))",
            ],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
    )
    plugin_text = subprocess.run(
        [str(venv / "bin/target-build-pluginlist")],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout
    stage_generated_modules(root / "packaging/acquire_config.py", acquire_dir, plugin_dir, plugin_text)


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
```

- [ ] **Step 5: Run tests and prepare the real environment**

Run:

```bash
UV_CACHE_DIR=.uv-cache uv run --python 3.10 --with pytest pytest tests/test_prepare_environment.py -v
UV_CACHE_DIR=.uv-cache python3 scripts/prepare_environment.py
```

Expected: test passes and both staged modules exist under `.venv/lib/python3.10/site-packages`.

- [ ] **Step 6: Verify installed imports and plugin registry**

Run:

```bash
uv pip check --python .venv/bin/python
.venv/bin/python -c "import acquire.config, dissect.apfs, dissect.target.plugins._pluginlist; print(acquire.config.CONFIG)"
.venv/bin/target-build-pluginlist | rg -q 'PLUGIN'
```

Expected: no broken requirements; imports succeed; printed config contains `full`; plugin command exits zero.

- [ ] **Step 7: Commit dependency and preparation files**

```bash
git add requirements.in requirements.lock scripts/prepare_environment.py tests/test_prepare_environment.py
git commit -m "build: lock and prepare Acquire environment"
```

---

### Task 3: Build the Native PyInstaller One-File Executable

**Files:**
- Create: `acquire.spec`
- Create: `scripts/build.sh`
- Create: `tests/test_spec_contract.py`

**Interfaces:**
- Consumes: prepared `.venv`, `src/acquire_launcher/__main__.py`, installed `acquire.config`, and installed `_pluginlist.py`.
- Produces: `dist/acquire`, a console-mode arm64 one-file executable.

- [ ] **Step 1: Write spec contract tests**

Create `tests/test_spec_contract.py`:

```python
from pathlib import Path


def test_spec_uses_launcher_and_arm64_onefile():
    text = Path("acquire.spec").read_text()
    assert 'src/acquire_launcher/__main__.py' in text
    assert 'target_arch="arm64"' in text
    assert "COLLECT(" not in text


def test_spec_collects_dissect_plugins_and_package_data():
    text = Path("acquire.spec").read_text()
    assert 'collect_submodules("dissect")' in text
    assert 'collect_data_files("acquire")' in text
    assert 'collect_data_files("dissect.target")' in text
```

- [ ] **Step 2: Run the contract tests and confirm failure**

Run:

```bash
.venv/bin/pytest tests/test_spec_contract.py -v
```

Expected: fail because `acquire.spec` does not exist.

- [ ] **Step 3: Create the PyInstaller spec**

Create `acquire.spec`:

```python
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("dissect")
datas = []
for package in ("acquire", "dissect.target", "dissect.apfs"):
    datas += collect_data_files(package)

a = Analysis(
    ["src/acquire_launcher/__main__.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["IPython", "tkinter", "minio"],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="acquire",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch="arm64",
    codesign_identity=None,
    entitlements_file=None,
)
```

The absence of `COLLECT(...)` is intentional: `EXE` receives binaries and data directly, producing one-file mode.

- [ ] **Step 4: Add the clean build script**

Create `scripts/build.sh`:

```bash
#!/bin/zsh
set -euo pipefail

root_dir=${0:A:h:h}
cd "$root_dir"

UV_CACHE_DIR="$root_dir/.uv-cache" python3 scripts/prepare_environment.py
PYTHONHASHSEED=0 .venv/bin/pyinstaller --clean --noconfirm acquire.spec

[[ -x dist/acquire ]]
codesign --force --sign - dist/acquire
```

Run `chmod +x scripts/build.sh`.

- [ ] **Step 5: Run spec tests and build**

Run:

```bash
.venv/bin/pytest tests/test_spec_contract.py -v
./scripts/build.sh
```

Expected: tests pass and `dist/acquire` is the only runtime deliverable. PyInstaller warnings are reviewed; missing `dissect` or `acquire` modules are release blockers.

- [ ] **Step 6: Verify basic binary behavior**

Run:

```bash
file dist/acquire
codesign --verify --strict --verbose=2 dist/acquire
dist/acquire --help
```

Expected: `file` reports arm64 Mach-O; signature verification passes; non-root execution prints a `_MEI…` extraction path followed by `Run with: sudo ./acquire`, then exits 2.

- [ ] **Step 7: Commit the build configuration**

```bash
git add acquire.spec scripts/build.sh tests/test_spec_contract.py
git commit -m "build: freeze Acquire with PyInstaller"
```

---

### Task 4: Verify Release Integrity and Extraction Cleanup

**Files:**
- Create: `scripts/verify_release.sh`

**Interfaces:**
- Consumes: `dist/acquire` and the prepared `.venv`.
- Produces: `dist/acquire.sha256` and `dist/SBOM.txt`.
- Returns non-zero for test, architecture, signature, checksum, or sidecar-directory failures.

- [ ] **Step 1: Implement deterministic release verification**

Create `scripts/verify_release.sh`:

```bash
#!/bin/zsh
set -euo pipefail

root_dir=${0:A:h:h}
cd "$root_dir"

[[ -x dist/acquire ]]
.venv/bin/pytest tests -v
file dist/acquire | grep -q 'arm64'
codesign --verify --strict --verbose=2 dist/acquire

if find dist -mindepth 1 -maxdepth 1 -type d | grep -q .; then
  echo "Unexpected PyInstaller sidecar directory in dist" >&2
  exit 1
fi

uv pip freeze --python .venv/bin/python | LC_ALL=C sort > dist/SBOM.txt
(cd dist && shasum -a 256 acquire > acquire.sha256)
shasum -a 256 -c dist/acquire.sha256
```

Run `chmod +x scripts/verify_release.sh`.

- [ ] **Step 2: Run the release verifier**

Run:

```bash
./scripts/verify_release.sh
```

Expected: all tests and checks pass; `SBOM.txt` includes Acquire 3.22 and PyInstaller 6.21.0; checksum verification succeeds.

- [ ] **Step 3: Run a privileged no-profile smoke acquisition**

Run:

```bash
mkdir -p build/smoke
(cd build/smoke && sudo ../../dist/acquire --profile none --no-compress 2>&1 | tee smoke-console.log)
```

Expected: output includes `PyInstaller runtime extraction:` followed by an `_MEI…` path; preflight passes; Acquire detects the local target; the run exits successfully and produces a report/log.

- [ ] **Step 4: Confirm normal `_MEI…` cleanup**

Extract the printed path and verify it no longer exists after clean exit:

```bash
mei_path=$(sed -n 's/^PyInstaller runtime extraction: //p' build/smoke/smoke-console.log | head -1)
[[ -n "$mei_path" ]]
[[ ! -e "$mei_path" ]]
```

Expected: the path was reported and is absent after exit. This confirms normal cleanup, not absence of runtime filesystem impact.

- [ ] **Step 5: Commit verification tooling**

```bash
git add scripts/verify_release.sh
git commit -m "test: verify PyInstaller Acquire release"
```

---

### Task 5: Document Operation, Forensic Impact, and Licensing

**Files:**
- Create: `docs/OPERATOR.md`
- Create: `THIRD_PARTY_NOTICES.md`
- Create: `README.md`

**Interfaces:**
- Consumes: runtime and output behavior proven in Tasks 1–4.
- Produces: operator, build, signing, upload, limitation, and license instructions.

- [ ] **Step 1: Write the operator guide**

Create `docs/OPERATOR.md` with these required sections and commands:

```markdown
# Acquire for macOS: Operator Guide

## Authorized use and privacy
Run only on an authorized Mac. Root does not universally bypass macOS privacy controls. Grant Full Disk Access to the execution context when policy permits it.

## Run
Place `acquire` in a dedicated writable case directory, open Terminal in that directory, and run:

```bash
chmod +x acquire
sudo ./acquire
```

The embedded defaults select Acquire's full macOS profile and an uncompressed tar archive. Filesystem fallback is disabled.

## Upload
Upload the evidence archive, `.report.json`, and `.log`. Do not edit or delete partial output before consulting the investigator.

## Verify

```bash
shasum -a 256 -c acquire.sha256
codesign --verify --strict --verbose=2 acquire
```

## Filesystem impact
PyInstaller one-file mode extracts Python and bundled dependencies into a temporary `_MEI…` directory. It normally removes this directory on clean exit, but interruption can leave it behind. Acquire also writes its archive, report, and log to the current directory. This package is not fileless or zero-footprint.

## Coverage and gaps
The full macOS profile includes selected configuration, logs, Unified Log data, FSEvents, persistence, application metadata, shell history, browser artifacts, SSH metadata, and Docker artifacts. Acquire 3.22 has no macOS volatile profile and this package does not claim comprehensive process, socket, RAM, clipboard, Mail, Messages, Keychain-secret, or every-browser collection. Review the report and log for all gaps.

## Disk-space behavior
The launcher stops below 5 GiB free and warns below 20 GiB. This does not guarantee that a full acquisition will fit.
```

- [ ] **Step 2: Write licensing and source notices**

Create `THIRD_PARTY_NOTICES.md` identifying:

- Acquire and Dissect as AGPL-3.0-or-later with upstream repository links;
- PyInstaller as GPL-2.0-or-later with its bootloader exception;
- `requirements.lock` and `dist/SBOM.txt` as dependency inventories;
- this repository as the corresponding packaging source supplied to recipients.

- [ ] **Step 3: Write the build README**

Create `README.md` with:

- authorized-use purpose;
- exact pinned versions;
- `./scripts/build.sh` build command;
- `./scripts/verify_release.sh` verification command;
- output files under `dist/`;
- development ad-hoc signing behavior;
- production Developer ID/notarization requirements using organization-controlled credentials;
- links to the design, implementation plan, operator guide, and third-party notices.

- [ ] **Step 4: Verify required documentation statements**

Run:

```bash
rg -n 'sudo ./acquire|_MEI|not fileless|Acquire 3.22|Full Disk Access|report.json|AGPL|PyInstaller' README.md docs/OPERATOR.md THIRD_PARTY_NOTICES.md
```

Expected: every operational, forensic-impact, and licensing statement appears.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md docs/OPERATOR.md THIRD_PARTY_NOTICES.md
git commit -m "docs: add PyInstaller Acquire operator guidance"
```

---

### Task 6: Controlled Full-Profile Acceptance Test

**Files:**
- Modify existing source/build/test/documentation files only if acceptance findings require a correction.
- Never commit collected evidence.

**Interfaces:**
- Consumes: verified `dist/acquire`.
- Produces: final acceptance evidence summarized in the handoff.

- [ ] **Step 1: Confirm authorization, checksum, and free capacity**

Run:

```bash
df -h .
shasum -a 256 -c dist/acquire.sha256
```

Expected: adequate free space and valid executable checksum. Do not run a full collection without explicit authorization for the test Mac.

- [ ] **Step 2: Run the default full profile**

Run:

```bash
mkdir -p build/acceptance
(cd build/acceptance && sudo ../../dist/acquire 2>&1 | tee acceptance-console.log)
```

Expected: output shows `_MEI…`, preflight passes, effective/default arguments contain the full profile and uncompressed tar output, and Acquire exits zero.

- [ ] **Step 3: Review collection failures and frozen-import health**

Run:

```bash
rg -n 'FAILED|ERROR|Traceback|ModuleNotFoundError|permission|denied|APFS|History|MacOS' build/acceptance/*.log build/acceptance/*.report.json
```

Expected: no missing frozen imports, missing plugins, or unexpected tracebacks. Permission/TCC gaps remain visible as target limitations.

- [ ] **Step 4: Open the evidence archive with Dissect tooling**

Run:

```bash
.venv/bin/target-info build/acceptance/*.tar
```

Expected: Dissect opens the acquired uncompressed tar container successfully.

- [ ] **Step 5: Re-run release gates and inspect repository state**

Run:

```bash
./scripts/verify_release.sh
git status --short
```

Expected: all gates pass and no evidence files are tracked or staged.

- [ ] **Step 6: Commit only verified acceptance corrections**

If acceptance reveals an implementation defect, add a focused failing test, implement the minimal correction, rerun the affected and full verification suites, and commit only source/build/test/documentation files. Do not create an empty commit when no correction is needed.
