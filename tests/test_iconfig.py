import os
import pytest
from pathlib import Path
from unittest.mock import patch

from iconfig.iconfig import iConfig


class TestiConfig:
    """Test cases for the iConfig class - main configuration access point."""

    @pytest.fixture
    def test_config_dir(self):
        """Use existing test fixtures directory."""
        return str(Path(__file__).parent / "fixtures" / "test1")

    def test_init_default(self):
        """Test iConfig initialization without INCONFIG_HOME nor default folder "config"."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(Exception) as excinfo:
                iConfig()

            # Check the actual exception type
            print(f"Exception type: {excinfo.type.__name__}")
            print(f"Exception message: {str(excinfo.value)}")

            # Assert specific behavior based on actual exception type
            assert excinfo.type in [FileNotFoundError, RuntimeError, OSError]

    def test_get_simple_key(self, test_config_dir):
        """Test getting a simple configuration value."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Should get the app_name from config1.yaml
            result = config.get("app_name")
            assert result == "iconfig"

    def test_get_nested_key(self, test_config_dir):
        """Test getting nested configuration values."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test getting nested values from your fixtures
            result = config.get("debug")
            assert result is True

            # No resolution possible as key exists several times at the same depth and level
            with pytest.raises(Exception) as excinfo:
                result = config.get("enabled")  # From features.search.enabled
            assert excinfo.type in [KeyError]

    def test_get_with_path_filter(self, test_config_dir):
        """Test getting configuration values with path filtering."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Get port from database context
            result = config.get("port", path=["database"])
            assert result == 5432

            # Get port from server context
            result = config.get("port", path=["server"])
            assert result == 8080

    def test_get_with_default(self, test_config_dir):
        """Test getting configuration values with default fallback."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Non-existent key with default
            result = config.get("nonexistent", default="default_value")
            assert result == "default_value"

            # Existing key should not use default
            result = config.get("app_name", default="not_used")
            assert result == "iconfig"

    def test_get_key_not_found(self, test_config_dir):
        """Test getting a non-existent key without default."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            result = config.get("nonexistent")
            assert result is None  # Should return None when not found

    def test_get_with_level_filter(self, test_config_dir):
        """Test getting configuration values filtered by level."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Get entries at specific levels
            result = config.get("debug", level=0)  # Top level
            assert result is True

    def test_get_with_depth_filter(self, test_config_dir):
        """Test getting configuration values filtered by depth."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test getting values at specific depths
            result = config.whereis("timeout", depth=1)  # Should find timeout somewhere
            assert len(result) == 8

    def test_get_with_forcefirst(self, test_config_dir):
        """Test getting configuration values with forcefirst option."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test with forcefirst for potentially ambiguous keys
            result = config.get("timeout", forcefirst=True)
            assert result is not None

    def test_callable_interface(self, test_config_dir):
        """Test using iConfig as a callable."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test callable interface
            result = config("app_name")
            assert result == "iconfig"

            # Test callable with default
            result = config("nonexistent", default="default_value")
            assert result == "default_value"

    def test_set_configuration_value(self, test_config_dir):
        """Test setting configuration values."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Set a new value
            config.set("debug", value=False)

            # Verify the change
            result = config.get("debug")
            assert result is False

    def test_whereis_method(self, test_config_dir):
        """Test the whereis method to find configuration sources."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Find where a key is defined
            location = config.whereis("app_name")
            assert location is not None
            assert isinstance(location, list)
            # Should contain metadata about where the key was found

    def test_environment_variable_expansion(self, test_config_dir):
        """Test environment variable expansion in configuration values."""
        with patch.dict(
            os.environ, {"INCONFIG_HOME": test_config_dir, "TEST_VAR": "expanded_value"}
        ):
            config = iConfig()

            # This would test if config values contain ${TEST_VAR} syntax
            # Depends on your test fixtures having such values
            result = config.get("home")  # From paths.home: "${HOME}"
            assert result is not None
            # Should be expanded environment variable, not literal "${HOME}"

    def test_special_yaml_values(self, test_config_dir):
        """Test handling of special YAML values."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test null values
            result = config.get("optional_setting")
            assert result is None

            result = config.get("unused_feature")
            assert result is None

            # Test boolean variations
            result = config.get("feature_a")
            assert result is True

            result = config.get("feature_b")
            assert result is False

    def test_numeric_values(self, test_config_dir):
        """Test various numeric value types."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test float value
            result = config.get("float_value")
            assert abs(result - 3.14159) < 0.0001

            # Test scientific notation
            result = config.get("scientific")
            assert abs(result - 1.23e-4) < 1e-6

            # Test hex value
            result = config.get("hexadecimal")
            assert result == 0xFF

    def test_array_values(self, test_config_dir):
        """Test getting array/list configuration values."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test getting array values
            result = config.get("supported_formats")
            assert isinstance(result, list)
            assert "yaml" in result
            assert "json" in result

    def test_anchors_and_aliases(self, test_config_dir):
        """Test YAML anchors and aliases functionality."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test that anchor values are accessible
            result = config.get("retries")  # From defaults anchor
            assert result == 3

            # Test inherited values in services
            result = config.get("workers")  # From web_server
            assert result == 4

            result = config.get("concurrency")  # From background_worker
            assert result == 2

    def test_deep_nested_keys(self, test_config_dir):
        """Test accessing deeply nested configuration keys."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test deep nesting from your fixtures
            result = config.get("deep_setting")
            assert result in ["found_it", "found_it in level 2"]

            # Test getting delta from deeply nested structure
            result = config.get("delta")
            assert result in ["deepest", "deepest in level 2"]

    def test_hierarchical_config_files(self, test_config_dir):
        """Test that subconfig files are properly integrated."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Should find keys from subconfig files too
            result = config.get("extra_setting")  # From subconfig1.yaml
            assert result == "extra_found"

            # Test hierarchical override behavior
            result = config.get("deep_setting")
            assert result in ["found_it", "found_it in level 2"]

    def test_multiline_strings(self, test_config_dir):
        """Test multiline string handling."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            config = iConfig()

            # Test literal block scalar (|)
            help_text = config.get("help_text")
            assert isinstance(help_text, str)
            assert "multi-line" in help_text
            assert "\n" in help_text  # Should preserve line breaks

            # Test folded scalar (>)
            sql_query = config.get("sql_query")
            assert isinstance(sql_query, str)
            assert "SELECT" in sql_query

    def test_singleton_decorator_behavior(self, test_config_dir):
        """Test singleton decorator functionality."""
        with patch.dict(os.environ, {"INCONFIG_HOME": test_config_dir}):
            # Create two instances
            config1 = iConfig()
            config2 = iConfig()

            # Should be same instance due to singleton decorator
            assert config1 is config2

            # Test configuration-controlled singleton behavior
            # This depends on having iConfig.singleton setting in your test configs
