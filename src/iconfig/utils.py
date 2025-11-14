"""Utility functions for configuration file discovery and key path processing.

This module provides essential utility functions used throughout the iConfig system
for file system operations and key path manipulation. These functions support the
core functionality of hierarchical configuration management.

The module includes functions for:
- Discovering YAML configuration files in directory structures
- Processing and normalizing key paths with dot notation support
- File metadata collection for change detection

Example:
    Basic usage of utility functions::

        from pathlib import Path
        from iconfig.utils import discover_config_files, get_key_path

        # Discover configuration files
        config_dir = Path("config")
        files = discover_config_files(config_dir)

        # Process key paths
        key, path = get_key_path("database.host", ["production"])

Functions:
    discover_config_files: Recursively find YAML files with metadata
    get_key_path: Parse and normalize key paths with dot notation
"""

from pathlib import Path

from typing import Tuple

import yaml

from iconfig.labels import Labels


def discover_config_files(
    base_path: Path, pattern: str = "*.yaml"
) -> dict[str, dict[str, str | float]]:
    """Recursively discover configuration files with metadata collection.

    Scans the specified directory tree for files matching the given pattern
    and collects metadata including file paths, modification times, and
    hierarchy levels. This information is used for index building and
    change detection.

    Args:
        base_path (Path): Root directory to search for configuration files.
        pattern (str, optional): Glob pattern for file matching. Defaults to "*.yaml".

    Returns:
        dict[str, dict[str, str|float]]: Dictionary mapping relative file paths
        to metadata dictionaries containing:

        - file_path (str): Absolute path to the configuration file
        - mtime (float): File modification time as timestamp
        - level (int): Hierarchy level based on directory depth

    Example:
        Discovering configuration files::

            config_dir = Path("config")
            files = discover_config_files(config_dir)

            # Result structure:
            # {
            #     "database.yaml": {
            #         "file_path": "/path/to/config/database.yaml",
            #         "mtime": 1699123456.789,
            #         "level": 0
            #     },
            #     "api/settings.yaml": {
            #         "file_path": "/path/to/config/api/settings.yaml",
            #         "mtime": 1699123457.123,
            #         "level": 1
            #     }
            # }

    Note:
        The hierarchy level is calculated based on directory depth relative
        to the base path, with 0 representing files in the root directory.
    """
    files = list(base_path.rglob(pattern))
    ret = {}
    for file in files:
        if file.is_file():
            dict_ref = str(file.resolve().relative_to(base_path.resolve()))
            ret[dict_ref] = {
                Labels.FILE_PATH: str(file.resolve()),
                Labels.MTIME: file.stat().st_mtime,
                Labels.LEVEL: len(file.relative_to(base_path).parents) - 1,
            }
    return ret


def get_key_path(key: str, path: list) -> Tuple[str, list[str]]:
    """Parse and normalize key paths with dot notation support.

    Processes configuration keys that may contain dot notation (e.g., "database.host")
    and combines them with existing path contexts to create normalized key and path
    components. This enables flexible key specification and hierarchical access.

    Args:
        key (str): Configuration key, potentially with dot notation.
        path (list): Existing path context as a list of strings.

    Returns:
        Tuple[str, list[str]]: A tuple containing:

        - key (str): The final key component (rightmost part after dots)
        - path (list[str]): Combined path context including dot notation parts

    Example:
        Processing keys with dot notation::

            # Simple key without dots
            key, path = get_key_path("host", ["database"])
            # Result: ("host", ["database"])

            # Key with dot notation
            key, path = get_key_path("database.host", [])
            # Result: ("host", ["database"])

            # Combining dot notation with existing path
            key, path = get_key_path("connection.timeout", ["api"])
            # Result: ("timeout", ["connection", "api"])

            # String path converted to list
            key, path = get_key_path("port", "database")
            # Result: ("port", ["database"])

    Note:
        When dot notation is present, the key is split and the rightmost
        component becomes the key while preceding components are prepended
        to the path context.
    """
    if "." in key:
        parts = key.split(".")
        key = parts[-1]
        path_parts = parts[:-1]

        if not path:
            path = path_parts
        else:
            if isinstance(path, str):
                path = [path]
            path = path_parts + path

    return key, path


def singleton_or_not(class_):
    """Decorator that conditionally implements the singleton pattern.

    Provides a sophisticated singleton implementation that can be controlled
    through configuration settings. The singleton behavior is determined by
    a configuration key '<class_name>.singleton' - when True, the class
    behaves as a singleton; when False, new instances are created each time.

    This allows applications to control singleton behavior through configuration
    without code changes, enabling different patterns for different environments
    (e.g., singleton in production, new instances in testing).

    Args:
        class_: The class to decorate with conditional singleton behavior.

    Returns:
        function: A wrapper function that manages instance creation according
        to the singleton configuration setting.

    Example:
        Using the conditional singleton decorator::

            @singleton_or_not
            class MyConfig:
                def __init__(self):
                    pass

            # Behavior depends on 'myconfig.singleton' configuration:
            # If True (default): same instance returned
            # If False: new instance created each time
            config1 = MyConfig()
            config2 = MyConfig()  # Same or different based on config

    Note:
        The decorator maintains an internal instances dictionary to track
        singleton objects. The singleton check is performed on each instantiation
        to allow dynamic behavior changes through configuration updates.
    """
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instance_ = class_(*args, **kwargs)
            instances[class_] = instance_
        else:
            instance_ = instances[class_]
            if (class_name := instance_.__class__.__name__) == "iConfig":
                if not instance_.get(f"{class_name.lower()}.singleton", default=True):
                    instances[class_] = class_(*args, **kwargs)
        return instances[class_]

    return getinstance

def _load_config(dict_ref: str, files: dict) -> dict:
    """Load and parse a YAML configuration file from the files registry.

    Internal utility function that loads a specific configuration file
    identified by its dictionary reference. The function performs file
    existence validation and YAML parsing with proper error handling.

    Args:
        dict_ref (str): Dictionary reference key identifying the configuration
            file in the files registry. This is typically a relative path
            like "config.yaml" or "database/settings.yaml".
        files (dict): Files registry dictionary mapping dict_ref keys to
            file metadata dictionaries containing file paths and other
            metadata information.

    Returns:
        dict: Parsed YAML configuration data as a Python dictionary.
        Returns the complete configuration structure from the file.

    Raises:
        FileNotFoundError: If the configuration file specified by dict_ref
            does not exist in the files registry or on the file system.
        yaml.YAMLError: If the YAML file contains syntax errors or cannot
            be parsed properly.
        PermissionError: If the file exists but cannot be read due to
            permission restrictions.

    Example:
        Loading a configuration file::

            files = {
                "config.yaml": {
                    "file_path": "/path/to/config.yaml",
                    "mtime": 1699123456.789,
                    "level": 0
                }
            }
            
            # Load the configuration
            config_data = _load_config("config.yaml", files)
            # Returns: {"app_name": "MyApp", "debug": True, ...}

    Note:
        This is an internal function primarily used by the KeyIndex system
        for lazy loading of configuration files. The function includes
        redundant file existence checks for additional safety, though this
        may be optimized in future versions.
    """
    if not (
        file_path := Path(files.get(dict_ref, {}).get(Labels.FILE_PATH))
    ).exists():
        raise FileNotFoundError(f"Configuration file '{dict_ref}' not found")
    if not file_path.exists():
        raise FileNotFoundError(f"Configuration file '{dict_ref}' not found")
    with open(file_path, "r") as f:
        return yaml.safe_load(f)