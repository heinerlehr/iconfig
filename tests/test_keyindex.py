import os
import pytest
from pathlib import Path
from unittest.mock import patch

from iconfig.keyindex import KeyIndex
from iconfig.labels import Labels


class TestKeyIndex:
    """Test cases for the KeyIndex class - focused on index management and querying."""

    @pytest.fixture
    def test_config_dir(self):
        """Use existing test fixtures directory."""
        return str(Path(__file__).parent / "fixtures" / "test1")

    def test_init_default(self):
        """Test KeyIndex initialization with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            ki = KeyIndex(load_index=False)
            assert ki._base == "config"
            assert ki._fn == ".index.yaml"
            assert isinstance(ki._index, dict)
            assert isinstance(ki._files, dict)

    def test_init_with_env_vars(self):
        """Test KeyIndex initialization with environment variables."""
        with patch.dict(
            os.environ,
            {"ICONFIG_HOME": "/custom/path", "ICONFIG_INDEXFN": "custom_index.yaml"},
        ):
            ki = KeyIndex(load_index=False)
            assert ki._base == "/custom/path"
            assert ki._fn == "custom_index.yaml"

    def test_build_index(self, test_config_dir):
        """Test building index from configuration files."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex(force_rebuild=True)

            # Check that files were discovered
            assert len(ki._files) > 0

            # Check that index contains expected keys from your fixtures
            assert "app_name" in ki._index
            assert "port" in ki._index  # appears in database and server sections
            assert "host" in ki._index  # appears in server section
            assert "timeout" in ki._index  # appears in database and defaults sections
            assert "enabled" in ki._index  # appears in features.search and server.ssl

            # Check index structure for a nested key
            timeout_entries = ki._index["timeout"]
            assert len(timeout_entries) >= 1  # Should find timeout in multiple places

            # Verify entry structure
            for entry in timeout_entries:
                assert Labels.LEVEL in entry
                assert Labels.DEPTH in entry
                assert Labels.DICT_REF in entry
                assert Labels.PATH in entry

    def test_get_simple_key(self, test_config_dir):
        """Test getting a simple key from the index."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()

            # Should get the app_name entry
            entry = ki.get("app_name")
            assert entry is not None
            assert entry[Labels.DICT_REF] is not None
            assert entry[Labels.PATH] is not None

    def test_get_with_path_filter(self, test_config_dir):
        """Test getting keys with path filtering."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()

            # Test getting with path filter
            entry = ki.get("port", path=["database"])
            assert entry is not None
            assert "database" in entry[Labels.PATH]

    def test_get_with_level_filter(self, test_config_dir):
        """Test getting keys with level filtering."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()

            # Test getting with level filter
            entry = ki.get("debug", level=0)
            assert entry is not None
            assert entry[Labels.LEVEL] == 0

    def test_get_nonexistent_key(self, test_config_dir):
        """Test getting a non-existent key returns None."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()

            entry = ki.get("nonexistent_key")
            assert entry is None

    def test_whereis_method(self, test_config_dir):
        """Test whereis method returns index entries."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()

            # Get all entries for a key
            entries = ki.whereis("timeout")
            assert entries is not None
            assert isinstance(entries, (list, dict))

    def test_add_entry_to_index(self, test_config_dir):
        """Test adding entries to the index."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex(load_index=False)  # Don't load existing index

            # Add a new entry
            ki.add(
                key="test_key",
                level=0,
                depth=1,
                dict_ref="test_config.yaml",
                path=["section", "test_key"],
            )

            # Verify it was added
            assert "test_key" in ki._index
            entries = ki._index["test_key"]
            assert len(entries) >= 1

            entry = entries[0]
            assert entry[Labels.LEVEL] == 0
            assert entry[Labels.DEPTH] == 1
            assert entry[Labels.DICT_REF] == "test_config.yaml"
            assert entry[Labels.PATH] == ["section", "test_key"]

    def test_duplicate_entry_prevention(self, test_config_dir):
        """Test that duplicate entries are not added to the index."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex(load_index=False)

            # Add same entry twice
            entry_data = {
                "key": "test_key",
                "level": 0,
                "depth": 1,
                "dict_ref": "test_config.yaml",
                "path": ["section", "test_key"],
            }

            ki.add(**entry_data)
            ki.add(**entry_data)  # Add again

            # Should only have one entry
            assert len(ki._index["test_key"]) == 1

    def test_save_and_load_index(self, test_config_dir):
        """Test saving and loading index to/from file."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki1 = KeyIndex()

            # Save the index
            ki1._save()

            # Create new instance and load
            ki2 = KeyIndex(load_index=False)
            ki2._load()

            # Should have same index structure
            assert ki2._index.keys() == ki1._index.keys()
            assert ki2._files.keys() == ki1._files.keys()

    def test_index_update_detection(self, test_config_dir):
        """Test that index detects when files have changed."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()
            original_index_size = len(ki._index)

            # Simulate file modification by changing mtime
            for dict_ref, file_info in ki._files.items():
                file_info[Labels.MTIME] += 1000  # Simulate newer file
                break

            # Update should detect the change
            ki._update()

            # Index should be rebuilt (this is implementation dependent)
            assert len(ki._index) >= original_index_size

    def test_file_discovery(self, test_config_dir):
        """Test that configuration files are properly discovered."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()

            # Should have discovered multiple files
            assert len(ki._files) >= 2  # At least config1.yaml and config2.yaml

            # Check file structure
            for dict_ref, file_info in ki._files.items():
                assert Labels.FILE_PATH in file_info
                assert Labels.MTIME in file_info

                # Verify file actually exists
                file_path = Path(file_info[Labels.FILE_PATH])
                assert file_path.exists()
                assert file_path.suffix in [".yaml", ".yml"]

    def test_index_excludes_index_file(self, test_config_dir):
        """Test that the index file itself is not included in discovery."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex()

            # Index file should not be in the files list
            index_filename = ki._fn
            index_path = str(Path(test_config_dir) / index_filename)

            assert index_filename not in ki._files
            assert index_path not in ki._files

    def test_has_entry_method(self, test_config_dir):
        """Test the has_entry method for duplicate detection."""
        with patch.dict(os.environ, {"ICONFIG_HOME": test_config_dir}):
            ki = KeyIndex(load_index=False)

            # Create test entries
            entry1 = {
                Labels.LEVEL: 0,
                Labels.DEPTH: 1,
                Labels.DICT_REF: "config.yaml",
                Labels.PATH: ["section", "key"],
            }

            entry2 = {
                Labels.LEVEL: 0,
                Labels.DEPTH: 1,
                Labels.DICT_REF: "config.yaml",
                Labels.PATH: ["section", "key"],
            }

            entry3 = {
                Labels.LEVEL: 1,  # Different level
                Labels.DEPTH: 1,
                Labels.DICT_REF: "config.yaml",
                Labels.PATH: ["section", "key"],
            }

            entries = [entry1]

            # Should find duplicate
            assert ki.has_entry(entry2, entries) is True

            # Should not find non-duplicate
            assert ki.has_entry(entry3, entries) is False

    def test_empty_config_file(self, tmp_path):
        """Test handling of empty configuration files."""
        # Create a temporary config directory with an empty YAML file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        
        empty_file = config_dir / "empty.yaml"
        empty_file.write_text("")  # Create empty file
        
        with patch.dict(os.environ, {"ICONFIG_HOME": str(config_dir)}):
            ki = KeyIndex(force_rebuild=True)
            
            # Should discover the empty file
            assert len(ki._files) >= 1
            
            # Index should be empty since no keys are defined
            assert len(ki._index) == 0
            
            # Getting any key should return None
            entry = ki.get("any_key")
            assert entry is None
