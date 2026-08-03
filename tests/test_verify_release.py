from pathlib import Path


def test_checksum_is_verified_from_dist_directory():
    script = Path("scripts/verify_release.sh").read_text()

    assert "(cd dist && shasum -a 256 -c acquire.sha256)" in script


def test_sbom_normalizes_editable_launcher_path():
    script = Path("scripts/verify_release.sh").read_text()

    assert "acquire-macos-launcher==0.1.0" in script
    assert "file://.*#acquire-macos-launcher==0.1.0" in script
