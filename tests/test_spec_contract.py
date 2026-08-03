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
