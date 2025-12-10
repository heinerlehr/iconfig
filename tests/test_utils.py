import os
from pathlib import Path
from iconfig.utils import discover_config_files


def test_discover_config_files():
    base_path = Path(os.getenv("ICONFIG_HOME", "tests/fixtures/test1"))

    files = discover_config_files(base_path)
    assert isinstance(files, dict)
    assert len(files) > 0
    for dict_ref, info in files.items():
        assert "file_path" in info
        assert "mtime" in info
        assert Path(info["file_path"]).exists()
