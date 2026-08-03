from pathlib import Path

import pytest

from scripts.prepare_environment import resolve_uv, stage_generated_modules


def test_resolves_explicit_uv_executable(tmp_path: Path):
    uv = tmp_path / "uv"
    uv.write_text("#!/bin/sh\n")
    uv.chmod(0o755)

    assert resolve_uv({"ACQUIRE_UV": str(uv), "PATH": ""}) == uv.resolve()


def test_rejects_missing_uv_executable():
    with pytest.raises(RuntimeError, match="uv executable not found"):
        resolve_uv({"PATH": ""})


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


def test_rejects_malformed_pluginlist(tmp_path: Path):
    config = tmp_path / "acquire_config.py"
    config.write_text("CONFIG = {}\n")

    with pytest.raises(ValueError, match="empty or malformed"):
        stage_generated_modules(config, tmp_path / "acquire", tmp_path / "plugins", "\n")
