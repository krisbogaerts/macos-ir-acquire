from __future__ import annotations

import os
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


def _capture(command: list[str], env: dict[str, str]) -> str:
    return subprocess.run(
        command,
        check=True,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()


def run(root: Path) -> None:
    venv = root / ".venv"
    python = venv / "bin/python"
    env = os.environ.copy()
    env.setdefault("UV_CACHE_DIR", str(root / ".uv-cache"))

    if not python.exists():
        subprocess.run(["uv", "venv", "--python", "3.10", str(venv)], check=True, env=env)

    subprocess.run(
        ["uv", "pip", "sync", "--python", str(python), str(root / "requirements.lock")],
        check=True,
        env=env,
    )
    subprocess.run(
        ["uv", "pip", "install", "--python", str(python), str(root)],
        check=True,
        env=env,
    )

    acquire_dir = Path(
        _capture(
            [str(python), "-c", "import acquire, pathlib; print(pathlib.Path(acquire.__file__).parent)"],
            env,
        )
    )
    plugin_dir = Path(
        _capture(
            [
                str(python),
                "-c",
                "import dissect.target.plugins as p, pathlib; print(pathlib.Path(next(iter(p.__path__))))",
            ],
            env,
        )
    )
    plugin_text = _capture([str(venv / "bin/target-build-pluginlist")], env)
    stage_generated_modules(root / "packaging/acquire_config.py", acquire_dir, plugin_dir, plugin_text + "\n")


if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
