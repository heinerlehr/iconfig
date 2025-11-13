import os
import pytest
from pathlib import Path
from unittest.mock import patch

from iconfig.keyindex import KeyIndex


class TestKeyIndex:
    """Test cases for the KeyIndex class."""
    
    @pytest.fixture
    def test_config_dir(self):
        """Use existing test fixtures directory."""
        return os.getenv("INCONFIG_HOME", "tests/fixtures/test1")

    def test_init_default(self):
        """Test KeyIndex initialization with defaults."""
        with patch.dict(os.environ, {}, clear=True):
            ki = KeyIndex(load_index=False)
            assert ki._base == "config"
            assert ki._fn == ".index.yaml"
            assert isinstance(ki._index, dict)
            assert isinstance(ki._files, dict)
            assert isinstance(ki._cfg, dict)
    
    def test_init_with_env_vars(self):
        """Test KeyIndex initialization with environment variables."""
        with patch.dict(os.environ, {
            'INCONFIG_HOME': '/custom/path',
            'INCONFIG_INDEXFN': 'custom_index.yaml'
        }):
            ki = KeyIndex(load_index=False)
            assert ki._base == '/custom/path'
            assert ki._fn == 'custom_index.yaml'
    
    def test_build(self, test_config_dir):
        """Test building index from scratch."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Check that files were discovered
            assert len(ki._files) > 0
            
            # Check that index contains expected keys from your fixtures
            assert 'app_name' in ki._index
            assert 'port' in ki._index  # appears in database and server sections
            assert 'host' in ki._index  # appears in server section
            assert 'timeout' in ki._index  # appears in database and defaults sections
            assert 'enabled' in ki._index  # appears in features.search and server.ssl
            
            # Check index structure for a nested key
            timeout_entries = ki._index['timeout']
            assert len(timeout_entries) >= 1  # Should find timeout in multiple places
    
    def test_get_simple_key(self, test_config_dir):
        """Test getting a simple key value."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Should get the app_name from config1.yaml
            result = ki.get('app_name')
            assert result == 'iconfig'
    
    def test_get_nested_key(self, test_config_dir):
        """Test getting a nested key value."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test getting nested values from your fixtures
            result = ki.get('debug')
            assert result is True
            # This key is repeated at depth 1
            with pytest.raises(KeyError) as exc_info:
                result = ki.get('debug', depth=1)
            assert "Ambiguous" in str(exc_info.value)
    
    def test_get_key_not_found(self, test_config_dir):
        """Test getting a non-existent key."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            result = ki.get('nonexistent')
            assert result is None
    
    def test_get_with_default(self, test_config_dir):
        """Test getting a key with default value."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            result = ki.get('nonexistent', default='default_value')
            assert result == 'default_value'
    
    def test_get_with_path_filter(self, test_config_dir):
        """Test getting a key filtered by path."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Get port from database context
            result = ki.get('port', path=['database'])
            assert result == 5432
            
            # Get port from server context  
            result = ki.get('port', path=['server'])
            assert result == 8080
    
    def test_get_deep_nested_key(self, test_config_dir):
        """Test getting deeply nested keys."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test deep nesting from your fixtures
            result = ki.get('deep_setting')
            assert result in ['found_it', 'found_it in level 2']
            
            # Test getting delta from deeply nested structure
            result = ki.get('delta')
            assert result in ['deepest', 'deepest in level 2']
    
    def test_get_with_level_filter(self, test_config_dir):
        """Test getting a key filtered by level."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Get entries at specific levels
            result = ki.get('debug', level=0)  # Top level
            assert result is True
    
    def test_get_hierarchical_override(self, test_config_dir):
        """Test hierarchical configuration override behavior."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test that higher level configs override lower ones
            # Based on your fixtures, log_level appears in multiple places
            result = ki.whereis('log_level')
            assert len(result) >= 1
            for entry in result:
                assert entry['path'][0] in ['defaults', 'base_config', 'development', 'production']
    
    def test_get_array_values(self, test_config_dir):
        """Test getting array values from configuration."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test getting array values
            result = ki.get('supported_formats')
            assert isinstance(result, list)
            assert 'yaml' in result
            assert 'json' in result
    
    def test_update_key(self, test_config_dir):
        """Test updating a key value."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Update timeout value
            ki.update('algorithms', value=['sha256', 'md5'])
            
            # Verify the update
            result = ki.get('algorithms')
            assert result == ['sha256', 'md5']
    
    def test_save_and_load(self, test_config_dir):
        """Test saving and loading index."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Create new instance and load
            ki2 = KeyIndex()
            
            # Should have same index
            assert ki2._index.keys() == ki._index.keys()
            assert ki2._files.keys() == ki._files.keys()
            
            # Should be able to get values
            result = ki2.get('app_name')
            assert result == 'iconfig'
    
    def test_load_without_index_file(self, test_config_dir):
        """Test load when index file doesn't exist (should build)."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            
            # Ensure no index file exists
            index_path = Path(test_config_dir) / '.index.yaml'
            if index_path.exists():
                index_path.unlink()
            
            ki = KeyIndex()
            
            # Should have built index
            assert len(ki._index) > 0
            assert 'app_name' in ki._index
    
    def test_special_yaml_values(self, test_config_dir):
        """Test handling of special YAML values from your fixtures."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test null values
            result = ki.get('optional_setting')
            assert result is None
            
            result = ki.get('unused_feature')
            assert result is None
            
            # Test boolean variations
            result = ki.get('feature_a')
            assert result is True
            
            result = ki.get('feature_b')
            assert result is False
    
    def test_numeric_values(self, test_config_dir):
        """Test various numeric value types from your fixtures."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test float value
            result = ki.get('float_value')
            assert abs(result - 3.14159) < 0.0001
            
            # Test scientific notation
            result = ki.get('scientific')
            assert abs(result - 1.23e-4) < 1e-6
            
            # Test hex value
            result = ki.get('hexadecimal')
            assert result == 0xFF
    
    def test_anchors_and_aliases(self, test_config_dir):
        """Test YAML anchors and aliases from your fixtures."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test that anchor values are accessible
            result = ki.get('retries')  # From defaults anchor
            assert result == 3
            
            # Test inherited values in services
            result = ki.get('workers')  # From web_server
            assert result == 4
            
            result = ki.get('concurrency')  # From background_worker  
            assert result == 2
    
    def test_multiline_strings(self, test_config_dir):
        """Test multiline string handling from your fixtures."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Test literal block scalar (|)
            help_text = ki.get('help_text')
            assert isinstance(help_text, str)
            assert 'multi-line' in help_text
            assert '\n' in help_text  # Should preserve line breaks
            
            # Test folded scalar (>)
            sql_query = ki.get('sql_query')
            assert isinstance(sql_query, str)
            assert 'SELECT' in sql_query
    
    def test_hierarchical_config_files(self, test_config_dir):
        """Test that subconfig files are also indexed."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):
            ki = KeyIndex()
            
            # Should find keys from subconfig files too
            result = ki.get('extra_setting')  # From subconfig1.yaml
            assert result == 'extra_found'
            
            # Test that we get hierarchical results
            # deep_setting appears in both main config and subconfig with different values
            result = ki.get('deep_setting')
            assert result in ['found_it', 'found_it in level 2']
        
    def test_expansion(self, test_config_dir):
        """Test environment variable expansion in configuration values."""
        with patch.dict(os.environ, {'INCONFIG_HOME': test_config_dir}):

            testval = '/home/testuser'
            os.environ['TEST_DIR'] = testval

            ki = KeyIndex()
            
            # Test expansion of $HOME
            result = ki.get('test_expand.dir')

            assert result == testval
            
            # Test expansion of ${HOME}
            result = ki.get('test_expand.other_locations')
            assert isinstance(result, list)
            assert testval in result
