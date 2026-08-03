import hashlib
import stat
import subprocess
import tarfile
from pathlib import Path


def test_checksum_is_verified_from_dist_directory():
    script = Path("scripts/verify_release.sh").read_text()

    assert "(cd dist && shasum -a 256 -c acquire.sha256)" in script


def test_sbom_normalizes_editable_launcher_path():
    script = Path("scripts/verify_release.sh").read_text()

    assert "acquire-macos-launcher==0.1.0" in script
    assert "file://.*#acquire-macos-launcher==0.1.0" in script


def test_release_includes_license_and_notices():
    script = Path("scripts/verify_release.sh").read_text()

    assert "cp LICENSE THIRD_PARTY_NOTICES.md dist/" in script


def test_package_release_preserves_executable_mode_and_writes_checksum(tmp_path):
    release_dir = tmp_path / "dist"
    release_dir.mkdir()

    files = {
        "acquire": b"binary",
        "acquire.sha256": f"{hashlib.sha256(b'binary').hexdigest()}  acquire\n".encode(),
        "SBOM.txt": b"acquire==3.22\n",
        "LICENSE": b"license\n",
        "THIRD_PARTY_NOTICES.md": b"notices\n",
    }
    for name, content in files.items():
        (release_dir / name).write_bytes(content)
    (release_dir / "acquire").chmod(0o755)

    subprocess.run(
        ["zsh", "scripts/package_release.sh", str(release_dir)],
        check=True,
        capture_output=True,
        text=True,
    )

    archive = release_dir / "acquire-macos-arm64.tar.gz"
    archive_checksum = release_dir / "acquire-macos-arm64.tar.gz.sha256"
    assert archive.is_file()
    assert archive_checksum.read_text() == (
        f"{hashlib.sha256(archive.read_bytes()).hexdigest()}  {archive.name}\n"
    )

    with tarfile.open(archive, "r:gz") as bundle:
        assert bundle.getnames() == list(files)
        assert bundle.getmember("acquire").mode & stat.S_IXUSR
