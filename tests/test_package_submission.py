"""Security boundaries and reproducibility of the private judge snapshot."""
import io
from pathlib import Path
import tarfile

import pytest

from scripts import package_submission as package


def test_unknown_private_files_never_enter_allowlist():
    names = set(package.TOP_LEVEL + package.SOURCE_FILES + package.TEST_FILES + package.CONFIG_FILES)
    assert not any("SOURCE_VERIFICATION" in name or "RESEARCH_CASES" in name for name in names)
    assert not any(name.startswith(("runs/", ".env", ".git/", ".venv/")) for name in names)
    assert package.REPLAY_NAME.fullmatch("full-deepseek-bp-09-scan.json")
    assert not package.REPLAY_NAME.fullmatch("original-research.json")
    assert not package.REPLAY_NAME.fullmatch("../../.env")


def test_regular_file_reader_rejects_symlinks_at_each_component(tmp_path):
    (tmp_path / "safe").mkdir()
    (tmp_path / "safe/file").write_bytes(b"ordinary content")
    assert package._read(tmp_path, "safe/file") == b"ordinary content"
    (tmp_path / "linked").symlink_to(tmp_path / "safe", target_is_directory=True)
    with pytest.raises(ValueError, match="Symlink rejected"):
        package._read(tmp_path, "linked/file")


def test_secret_value_scan_fails_without_disclosing_value():
    sentinel = "synthetic-credential-for-boundary-test"
    with pytest.raises(ValueError) as error:
        package.scan({"public.txt": sentinel.encode()}, {"TEST_API_KEY": sentinel})
    assert sentinel not in str(error.value)
    assert package.scan({"public.txt": b"TEST_API_KEY is configured externally"}, {"TEST_API_KEY": sentinel}) == 1


def test_private_key_signature_rejected_without_environment():
    marker = b"-----BEGIN " + b"PRIVATE KEY-----"
    with pytest.raises(ValueError, match="Secret scan rejected"):
        package.scan({"accident.txt": marker}, {})


def test_tar_is_byte_reproducible_and_contains_only_passed_bytes():
    payload = {"README.md": b"private review\n", "scripts/start.sh": b"#!/bin/sh\n"}
    first = package.archive_bytes(payload)
    assert first == package.archive_bytes(dict(reversed(list(payload.items()))))
    with tarfile.open(fileobj=io.BytesIO(first), mode="r:gz") as archive:
        assert archive.getnames() == ["blueprint-takeoff-gym/README.md", "blueprint-takeoff-gym/scripts/start.sh"]
        for member in archive:
            assert member.uid == member.gid == member.mtime == 0
            assert member.isfile()
            assert archive.extractfile(member).read() == payload[str(Path(member.name).relative_to("blueprint-takeoff-gym"))]


@pytest.mark.parametrize("status,pending", [("partial", 1), ("complete", 0)])
def test_snapshot_metadata_reports_captured_state_without_claiming_approval(status, pending):
    core = {"status": status, "runs": [{"status": "pending" if pending else "completed"}]}
    science = {"runs": [{"status": "pending" if pending else "completed"}]}
    metadata = package.snapshot_metadata(core, science)
    assert metadata["snapshot_status"] == "captured evaluation snapshot"
    assert metadata["evaluation_status"] == status
    assert metadata["pending_trials"] == pending
    assert metadata["science_pending_trials"] == pending
    assert "approval" not in str(metadata).lower()
