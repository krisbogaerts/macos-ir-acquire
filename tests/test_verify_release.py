from pathlib import Path


def test_checksum_is_verified_from_dist_directory():
    script = Path("scripts/verify_release.sh").read_text()

    assert "(cd dist && shasum -a 256 -c acquire.sha256)" in script
