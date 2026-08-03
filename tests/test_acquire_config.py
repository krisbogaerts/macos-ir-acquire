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
