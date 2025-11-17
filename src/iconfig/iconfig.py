"""Main user interface for hierarchical configuration management.

This module provides the primary :class:`iConfig` class that serves as the main
entry point for users to interact with hierarchical configuration data. It includes
a sophisticated singleton decorator and the core configuration access interface.

The module combines file-based configuration management with in-memory caching,
environment variable expansion, and flexible access patterns. The singleton pattern
ensures consistent configuration state across an application while allowing
opt-out behavior when needed.

Key Features:
    - Conditional singleton pattern with configuration-based control
    - Hierarchical configuration access with path filtering
    - Environment variable expansion in configuration values
    - Lazy loading of configuration files for performance
    - Type-safe overloaded methods for better IDE support

Example:
    Basic usage of the iConfig interface::

        from iconfig import iConfig

        # Initialize configuration (singleton by default)
        config = iConfig()

        # Get configuration values
        app_name = config.get('app_name')
        db_port = config.get('port', path=['database'])

        # Use with defaults and type hints
        timeout = config.get('timeout', default=30)

        # Callable interface
        debug = config('debug', default=False)

        # Set values (in-memory)
        config.set('new_setting', value=True)

Classes:
    iConfig: Main configuration interface with singleton support

Functions:
    singleton_or_not: Decorator for conditional singleton behavior
"""

import os
from pathlib import Path
from typing import Any, Tuple, overload, TypeVar

from .labels import Labels
from .keyindex import KeyIndex
from .utils import get_key_path, singleton_or_not, _load_config

T = TypeVar("T")


@singleton_or_not
class iConfig:
    """Main configuration interface for hierarchical configuration management.

    The :class:`iConfig` class provides a comprehensive, user-friendly interface for
    accessing hierarchical configuration data stored in YAML files. It automatically
    discovers configuration files, builds fast lookup indexes, and provides flexible
    access patterns with environment variable expansion.

    The class uses a conditional singleton pattern (controlled by configuration)
    to ensure consistent configuration access throughout an application while
    allowing different behavior in testing environments.

    Key Features:
        - Hierarchical configuration access with path filtering
        - Lazy loading and caching of configuration files
        - Environment variable expansion in configuration values
        - Type-safe method overloads for better IDE support
        - Configurable singleton behavior
        - In-memory configuration updates

    Attributes:
        _base (str): Base directory for configuration files (default: "config").
        _cfg (dict): In-memory cache of loaded configuration files.
        _ki (KeyIndex): Internal KeyIndex instance for fast lookups.

    Example:
        Comprehensive configuration usage::

            # Initialize (singleton by default)
            config = iConfig()

            # Simple key access
            app_name = config.get('app_name')

            # Path-filtered access
            db_host = config.get('host', path=['database'])
            api_host = config.get('host', path=['api'])

            # With defaults and type safety
            timeout = config.get('timeout', default=30)

            # Callable interface (shorthand)
            debug = config('debug', default=False)

            # Set values (in-memory only)
            config.set('runtime_flag', value=True)

            # Find configuration sources
            location = config.whereis('app_name')
            print(f"app_name defined in: {location}")

    Note:
        Configuration changes made with :meth:`set` are stored in memory only
        and do not persist to files. The singleton behavior can be controlled
        through the 'iconfig.singleton' configuration setting.
    """

    def __init__(self, force_rebuild: bool = False):
        """Initialize the iConfig instance.

        Sets up the configuration system by initializing internal data structures
        and creating a KeyIndex for fast configuration lookups. The base directory
        for configuration files can be controlled through the INCONFIG_HOME
        environment variable.

        Environment Variables:
            INCONFIG_HOME: Override the default 'config' directory path.

        Note:
            The KeyIndex is initialized during construction and will automatically
            discover and index configuration files in the specified directory.
        """
        # Holds the actual configuration files
        self._cfg = {}

        # Load base directory from environment variable or use "config" as default
        self._base = os.getenv("INCONFIG_HOME", "config")
        if not Path(self._base).exists():
            raise FileNotFoundError(f"Configuration base directory '{self._base}' does not exist."
                                    "Please set the INCONFIG_HOME environment variable to a valid path.")
        self._ki = KeyIndex(force_rebuild=force_rebuild)

    # When no default is provided, it might raise KeyError or return Any
    @overload
    def get(self, key: str, **kwargs: str | list[str]) -> Any: ...

    # When default is provided, return type is T | None
    @overload
    def get(self, key: str, *, default: T, **kwargs: str | list[str]) -> T|Any: ...

    # When default is None, return type could be Any or None
    @overload
    def get(
        self, key: str, *, default: None, **kwargs: str | list[str]
    ) -> Any | None: ...

    def __call__(
        self,
        *args: str | list[str],
        default: T | None = None,
        **kwargs: str | list[str],
    ) -> T | Any | None:
        """Callable interface for convenient configuration access.

        Provides a shorthand syntax for getting configuration values by making
        the iConfig instance itself callable. This is equivalent to calling
        the :meth:`get` method but with more concise syntax.

        Args:
            *args: Positional arguments passed to :meth:`get`.
            default: Default value to return if key is not found.
            **kwargs: Keyword arguments passed to :meth:`get`.

        Returns:
            The configuration value following the same rules as :meth:`get`.

        Example:
            Using the callable interface::

                config = iConfig()

                # These are equivalent:
                app_name1 = config.get('app_name')
                app_name2 = config('app_name')

                # With arguments:
                port1 = config.get('port', path=['database'], default=5432)
                port2 = config('port', path=['database'], default=5432)

        Note:
            The callable interface is particularly useful for one-off configuration
            lookups where the shorter syntax improves code readability.
        """
        # Forwards to get method
        return self.get(*args, default=default, **kwargs)

    ##################################################################################
    # Main access functions
    ##################################################################################

    def get(
        self,
        key: str,
        *args: str | list[str],
        default: T | None = None,
        **kwargs: str | list[str],
    ) -> Any:
        """Retrieve a configuration value with flexible filtering options.

        Performs hierarchical configuration lookup using the indexed configuration
        system. Supports path filtering, level restrictions, depth limitations,
        and environment variable expansion. The method uses lazy loading to
        optimize performance.

        Args:
            key (str): The configuration key to search for.
            *args: Additional path components for filtering.
            default: Default value to return if key is not found.
            **kwargs: Keyword arguments for advanced filtering:

                - path (str|list[str]): Filter to keys within this path context
                - level (int): Restrict search to specific hierarchy levels
                - depth (int): Limit search to specific nesting depths
                - forcefirst (bool): Return first match instead of best match

        Returns:
            Any: The configuration value with environment variables expanded,
            or the default value if the key is not found.

        Example:
            Various configuration access patterns::

                config = iConfig()

                # Simple key lookup
                app_name = config.get('app_name')

                # Path-filtered access
                db_port = config.get('port', path=['database'])
                api_port = config.get('port', path=['api'])

                # With default value
                timeout = config.get('timeout', default=30)

                # Level-specific (top-level files only)
                global_debug = config.get('debug', level=0)

                # Force first match for ambiguous keys
                first_port = config.get('port', forcefirst=True)

        Note:
            Environment variables in configuration values (e.g., "$HOME/data")
            are automatically expanded. The method uses the KeyIndex for fast
            lookup and only loads configuration files when needed.
        """

        path, level, depth, forcefirst = self._prep_args(*args, **kwargs)
        key, path = get_key_path(key, path)

        if not (
            entry := self._ki.get(
                key=key, path=path, level=level, depth=depth, forcefirst=forcefirst
            )
        ):
            return default
        else:
            return self._lookup(key=key, entry=entry, default=default)

    def set(
        self, key: str, *args: str | list[str], value: Any, **kwargs: str | list[str]
    ) -> None:
        """Set a configuration value in the in-memory cache.

        Updates a configuration value in the in-memory configuration store.
        Changes are not persisted to disk and exist only during the current
        runtime session. The method supports the same filtering options as
        :meth:`get` to target specific configuration contexts.

        Args:
            key (str): The configuration key to set.
            *args: Additional path components for context.
            value (Any): The value to assign to the key.
            **kwargs: Keyword arguments for filtering (same as :meth:`get`):

                - path (str|list[str]): Target specific path context
                - level (int): Target specific hierarchy level
                - depth (int): Target specific nesting depth
                - forcefirst (bool): Use first match instead of best match

        Returns:
            None

        Example:
            Setting configuration values::

                config = iConfig()

                # Set a simple value
                config.set('debug', value=True)

                # Set with path context
                config.set('timeout', value=60, path=['api'])

                # Verify the change
                assert config.get('debug') is True
                assert config.get('timeout', path=['api']) == 60

        Note:
            Changes made with :meth:`set` are stored in memory only and do not
            persist to configuration files. The configuration files on disk
            remain unchanged. Values set this way take precedence over file-based
            configuration during the current session.
        """

        path, level, depth, forcefirst = self._prep_args(*args, **kwargs)
        key, path = get_key_path(key, path)

        if not (
            entry := self._ki.get(
                key=key, path=path, level=level, depth=depth, forcefirst=forcefirst
            )
        ):
            return
        else:
            return self._update_nested(key=key, entry=entry, value=value)

    def whereis(
        self, key: str, *args: str | list[str], **kwargs: str | list[str]
    ) -> list | None:
        """Find the source locations of a configuration key.

        Locates where a specific configuration key is defined in the file system,
        providing detailed metadata about all matching locations. This is useful
        for debugging configuration issues, understanding configuration hierarchy,
        and verifying configuration sources.

        Args:
            key (str): The configuration key to locate.
            *args: Additional path components for filtering.
            **kwargs: Keyword arguments for filtering (same as :meth:`get`):

                - path (str|list[str]): Filter to specific path contexts
                - level (int): Filter by hierarchy level
                - depth (int): Filter by nesting depth

        Returns:
            list[dict] | None: List of location dictionaries, each containing
            metadata about where the key is defined. Returns None if the key
            is not found. Each dictionary may include:

            - Information about the source file and location
            - Hierarchy level and nesting context
            - Path information for the key

        Example:
            Finding configuration sources::

                config = iConfig()

                # Locate a key
                locations = config.whereis('app_name')
                if locations:
                    print(f"app_name found in {len(locations)} location(s)")
                    for loc in locations:
                        print(f"  Level: {loc.get('level', 'unknown')}")

                # Check if key exists anywhere
                if config.whereis('unknown_key') is None:
                    print("Key not found in any configuration")

        Note:
            This method is particularly useful for debugging configuration
            conflicts and understanding which configuration files are providing
            specific values in a hierarchical setup.
        """

        path, level, depth, _ = self._prep_args(*args, **kwargs)
        key, path = get_key_path(key, path)
        return self._ki.whereis(key=key, path=path, level=level, depth=depth)

    def reload(self, force_rebuild: bool = False) -> None:
        """Reload the configuration index and clear cached configurations.

        Rebuilds the internal KeyIndex to reflect any changes in the configuration
        files on disk. Also clears the in-memory cache of loaded configuration
        files to ensure that subsequent accesses load the latest data.

        Args:
            force_rebuild (bool): If True, forces a complete rebuild of the
            KeyIndex even if it appears up-to-date. Defaults to False.

        Returns:
            None
        """
        self._ki = KeyIndex(force_rebuild=force_rebuild)
        self._cfg = {}

    ##################################################################################
    # Internal helper function for finding/updating entries
    ##################################################################################

    def _prep_args(self, *args, **kwargs) -> Tuple[str, list[str], dict]:
        path = args
        if "path" in kwargs:
            path = kwargs.pop("path")
        level = kwargs.pop("level", -1)
        depth = kwargs.pop("depth", -1)
        forcefirst = kwargs.pop("forcefirst", False)
        return path, level, depth, forcefirst

    def _lookup(self, key: str, entry: dict, default: Any = None) -> Any:
        """Lazy lookup up of entries."""
        dict_ref = entry[Labels.DICT_REF]
        path = entry[Labels.PATH]

        if dict_ref not in self._cfg:
            try:
                self._cfg[dict_ref] = _load_config(dict_ref=dict_ref, files=self._ki._files)
            except Exception as e:
                raise RuntimeError(f"Failed to load config for {dict_ref}: {e}")

        entry = self._get_nested(data=self._cfg[dict_ref], path=path)
        return self.expand_env(entry[key]) if key in entry else self.expand_env(default)

    def _get_nested(self, data: dict, path: list[str]) -> Any:
        """Retrieve nested value from dictionary based on path."""
        current = data
        for p in path:
            if p in current:
                current = current[p]
            else:
                None
        return current

    def expand_env(self, obj):
        if isinstance(obj, str):
            return os.path.expandvars(obj)
        elif isinstance(obj, list):
            return [self.expand_env(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: self.expand_env(v) for k, v in obj.items()}
        else:
            return obj

    def _update_nested(self, key: str, entry: dict, value: Any) -> None:
        """Lazy update of entries."""
        dict_ref = entry[Labels.DICT_REF]
        path = entry[Labels.PATH]

        if dict_ref not in self._cfg:
            try:
                self._cfg[dict_ref] = _load_config(dict_ref=dict_ref, files=self._ki._files)
            except Exception as e:
                raise RuntimeError(f"Failed to load config for {dict_ref}: {e}")

        self._set_nested(data=self._cfg[dict_ref], path=path, key=key, value=value)

    def _set_nested(self, data: dict, path: list[str], key: str, value: Any) -> None:
        """Set nested value in dictionary based on path."""
        current = data
        for p in path:
            if p not in current or not isinstance(current[p], dict):
                current[p] = {}
            current = current[p]
        current[key] = value

if __name__ == "__main__":
    os.environ["INCONFIG_HOME"] = "/home/heiner/software/iconfig/tests/fixtures/test2"
    config = iConfig()