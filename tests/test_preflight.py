import sys
from collections import namedtuple
from pathlib import Path

import acquire_launcher
from acquire_launcher.preflight import GIB, PreflightResult, evaluate_preflight, run_preflight, runtime_extraction_path


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


def test_run_preflight_uses_current_directory_and_host_values(tmp_path, monkeypatch):
    usage = namedtuple("usage", "total used free")(100 * GIB, 50 * GIB, 50 * GIB)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("acquire_launcher.preflight.os.geteuid", lambda: 0)
    monkeypatch.setattr("acquire_launcher.preflight.os.access", lambda path, mode: True)
    monkeypatch.setattr("acquire_launcher.preflight.shutil.disk_usage", lambda path: usage)

    result = run_preflight()

    assert result.allowed is True
    assert str(tmp_path) in result.message


def test_main_stops_before_importing_acquire_when_preflight_fails(monkeypatch, capsys):
    monkeypatch.setattr(acquire_launcher, "runtime_extraction_path", lambda: None)
    monkeypatch.setattr(
        acquire_launcher,
        "run_preflight",
        lambda: PreflightResult(False, False, "Run with: sudo ./acquire"),
    )

    assert acquire_launcher.main() == 2
    assert capsys.readouterr().err == "Run with: sudo ./acquire\n"


def test_main_reports_extraction_and_delegates_to_acquire(monkeypatch, capsys):
    called = []
    acquire_package = type(sys)("acquire")
    acquire_module = type(sys)("acquire.acquire")
    acquire_module.main = lambda: called.append(True)
    monkeypatch.setitem(sys.modules, "acquire", acquire_package)
    monkeypatch.setitem(sys.modules, "acquire.acquire", acquire_module)
    monkeypatch.setattr(acquire_launcher, "runtime_extraction_path", lambda: Path("/tmp/_MEI123"))
    monkeypatch.setattr(
        acquire_launcher,
        "run_preflight",
        lambda: PreflightResult(True, False, "Output: /case (50.0 GiB available)"),
    )

    assert acquire_launcher.main() == 0
    assert called == [True]
    assert capsys.readouterr().err == (
        "PyInstaller runtime extraction: /tmp/_MEI123\n"
        "Output: /case (50.0 GiB available)\n"
    )
