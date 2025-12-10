"""Internal indexing engine for fast hierarchical configuration lookups.

This module provides the :class:`KeyIndex` class which serves as the core indexing
engine for the iConfig system. It handles file discovery, builds searchable indexes
of configuration keys, and provides fast lookups across multiple YAML files.

The KeyIndex class is designed for performance, building an in-memory index of all
configuration keys with metadata about their locations, hierarchy levels, and file
sources. This allows for O(1) key lookups without re-parsing configuration files.

Example:
    Using KeyIndex for configuration management::

        from iconfig.keyindex import KeyIndex

        # Initialize and build index
        ki = KeyIndex()

        # Get configuration values with filtering
        result = ki.get('port', path=['database'])

        # Add new configuration entry
        ki.add('new_key', 'value', path=['section'], level=0)

        # Save index to disk
        ki.save()

Classes:
    KeyIndex: Main indexing engine for hierarchical configuration management.

Note:
    This is an internal module. End users should typically use the iConfig
    class which provides a simpler interface wrapping KeyIndex functionality.
"""

import os
from pathlib import Path
import yaml
from typing import Any

from .labels import Labels
from .utils import discover_config_files, get_key_path, _load_config


class KeyIndex:
    """Core indexing engine for hierarchical configuration management.

    The KeyIndex class provides the internal engine that powers the iConfig system.
    It discovers configuration files, builds searchable indexes, and provides fast
    lookups with support for hierarchical filtering by path, level, and depth.

    The class maintains three main data structures:
    - ``_index``: Maps configuration keys to their metadata and locations
    - ``_files``: Tracks discovered configuration files and their properties
    - ``_cfg``: Runtime cache of loaded configuration file contents

    Args:
        load_index (bool, optional): Whether to automatically load/build the index
            on initialization. Defaults to True.

    Attributes:
        _base (str): Base configuration directory path.
        _fn (str): Index file name for persistence.
        _index (dict): Main key-to-metadata mapping.
        _files (dict): File discovery and metadata cache.
        _cfg (dict): Runtime configuration file content cache.

    Example:
        Basic KeyIndex operations::

            # Initialize with automatic index building
            ki = KeyIndex()

            # Search for configuration keys
            port_entries = ki.get('port')
            db_port = ki.get('port', path=['database'])

            # Get metadata about key locations
            location = ki.whereis('app_name')

            # Add new configuration entries
            ki.add('timeout', 30, path=['api'], level=1)

            # Persist changes
            ki.save()

    Note:
        The KeyIndex automatically discovers YAML files in the configuration
        directory and builds/maintains an index for fast lookups. The index
        is persisted to disk for quick startup times on subsequent runs.
    """

    _base: str = "config"
    _fn: str = ".index.yaml"

    def __init__(self, config_home: str = None, load_index: bool = True, force_rebuild: bool = False):
        """Initialize the KeyIndex with configuration directory and options.

        Sets up the internal data structures and optionally loads or builds
        the configuration index from the specified directory.

        Args:
            config_home (str, optional): Path to configuration directory.
                If not provided, uses ICONFIG_HOME environment variable
                or defaults to 'config'.
            load_index (bool, optional): Whether to automatically load/build
                the index on initialization. Defaults to True.
        """
        self._index = {}
        self._files = {}
        self._cfg = {}

        # Set base directory
        if config_home:
            self._base = config_home
        elif (base := os.getenv("ICONFIG_HOME")) is not None:
            self._base = base
        else:
            self._base = "config"

        # Set index filename
        if (fn := os.getenv("ICONFIG_INDEXFN")) is not None:
            self._fn = fn
        else:
            self._fn = ".index.yaml"

        if force_rebuild:
            self._build()

        if load_index:
            self._load()

    ##################################################################################
    # (De)serialization
    ##################################################################################

    def _load(self):
        """Load index from persistent storage or build new index.

        Attempts to load a previously saved index from disk. If the index file
        doesn't exist or cannot be loaded, automatically builds a fresh index
        by scanning the configuration directory. Also updates the index to
        ensure it reflects current file states.

        The method handles errors gracefully by falling back to building a
        new index if the saved index is corrupted or incompatible.
        """
        file_path = Path(self._base) / self._fn
        if not file_path.exists():
            self._build()
        else:
            try:
                with open(file_path, "r") as f:
                    data = yaml.safe_load(f)
                    self._index = data.get(Labels.INDEX, {})
                    self._files = data.get(Labels.FILES, {})
            except Exception:
                self._build()

            # Make sure index is up to date
            self._update()

    def _save(self):
        """Save the current index to persistent storage.

        Serializes the current index and file metadata to a YAML file in the
        configuration directory. This allows for fast startup times on subsequent
        runs by avoiding the need to rebuild the index from scratch.

        The saved index includes both the key-to-metadata mappings and file
        discovery information with modification times for change detection.

        Raises:
            OSError: If the index file cannot be written due to permissions
                or disk space issues.
        """
        data = {
            Labels.INDEX: self._index,
            Labels.FILES: self._files,
        }
        # Save to YAML file
        file_path = Path(self._base) / self._fn
        with open(file_path, "w") as f:
            yaml.dump(data, f)

    ##################################################################################
    # Main access functions
    ##################################################################################

    def get(
        self,
        key: str,
        path: list[str] | str | None = None,
        level: int = -1,
        depth: int = -1,
        forcefirst: bool = False,
        default: Any = None,
    ) -> Any:
        """Retrieve a configuration value by its key.

        Performs fast O(1) lookup of configuration values using the pre-built
        index. If the key exists in multiple files, returns the value from the
        file with the highest priority (lowest hierarchy level).

        Args:
            key (str): The configuration key to look up.
            path (list[str] | str | None): Optional path filter to narrow search.
            level (int): Filter by hierarchy level (-1 for any level).
            depth (int): Filter by nesting depth (-1 for any depth).
            forcefirst (bool): Return first match instead of highest priority.
            default (Any): Default value if key not found.

        Returns:
            Any: The configuration value associated with the key, or default if
            the key is not found.

        Example:
            >>> index = KeyIndex()
            >>> value = index.get('database.host')
            >>> print(value)  # 'localhost'
        """
        key, path = get_key_path(key, path)
        return self._find(key=key, path=path, level=level, depth=depth, forcefirst=forcefirst)

    def whereis(
        self,
        key: str,
        path: list[str] | str | None = None,
        level: int = -1,
        depth: int = -1,
    ) -> list | None:
        """Find the file location and metadata for a configuration key.

        Returns detailed information about where a configuration key is defined,
        including the hierarchy level and nesting path. This is useful for
        debugging configuration issues and understanding the configuration structure.

        Args:
            key (str): The configuration key to locate.
            path (list[str] | str | None): Optional path filter to narrow search.
            level (int): Filter by hierarchy level (-1 for any level).
            depth (int): Filter by nesting depth (-1 for any depth).

        Returns:
            list[dict] | None: A list of dictionaries containing metadata about
            the key's locations, each with:
                - 'level': Hierarchy level (0 for root files)
                - 'path': The full key path as a list
                Returns None if the key is not found.

        Example:
            >>> index = KeyIndex()
            >>> locations = index.whereis('database.host')
            >>> print(locations)
            # [{'level': 0, 'path': ['database', 'host']}]
        """

        if not (
            entries := self._find(
                key=key,
                path=path,
                level=level,
                depth=depth,
                forcefirst=False,
                return_all=True,
            )
        ):
            return None
        ret = []
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            ret.append(
                {
                    Labels.LEVEL: entry[Labels.LEVEL],
                    Labels.PATH: entry[Labels.PATH],
                }
            )
        return ret

    ##################################################################################
    # Internal helper function for finding/updating entries
    ##################################################################################

    def _find(
        self,
        key: str,
        path: list[str] | str | None = None,
        level: int = -1,
        depth: int = -1,
        forcefirst: bool = False,
        return_all: bool = False,
    ) -> Any:
        """Return the entry at the highest level & smallest depth."""

        # Special case of key notation
        key, path = get_key_path(key, path)

        if key not in self._index:
            return None

        entries = self._index[key]

        # search for key with matching (partial) path
        if path:
            if isinstance(path, str):
                if "/" in path:
                    path = path.split("/")
                else:
                    path = [path]

            filtered_entries = []
            for e in entries:
                if all(p in e[Labels.PATH] for p in path):
                    filtered_entries.append(e)
            entries = filtered_entries
            if not entries:
                return None
        # filter by level
        if level >= 0:
            entries = [e for e in entries if e[Labels.LEVEL] == level]
            if not entries:
                return None
        else:
            # Find maximal level first, then minimal depth
            best_level = max(e[Labels.LEVEL] for e in entries)
            entries = [e for e in entries if e[Labels.LEVEL] == best_level]

        # filter by depth
        if depth >= 0:
            entries = [e for e in entries if e[Labels.DEPTH] == depth]
            if not entries:
                raise KeyError(f"Key '{key}' with depth '{depth}' not found")
        else:
            best_depth = min(e[Labels.DEPTH] for e in entries)
            entries = [e for e in entries if e[Labels.DEPTH] == best_depth]

        if len(entries) == 1:
            return entries[0]
        elif forcefirst and entries:
            return entries[0]
        elif return_all:
            return entries
        else:
            length = len(entries)
            msg = f"Ambiguous key '{key}': {length} entries at same level/depth:"
            for i in range(length):
                msg += f"\n{'/'.join(entries[i][Labels.PATH])}"
            raise KeyError(
                f"Ambiguous key '{key}': {length} entries at same level/depth"
            )

    ##################################################################################
    # Index building
    ##################################################################################
    def _build(self):
        """Build index by discovering and parsing configuration files.

        Scans the configuration directory tree for YAML files and builds
        a comprehensive index mapping each configuration key to its location,
        nesting level, and containing file. The index enables O(1) lookup
        performance for configuration access.

        The build process:
        1. Discovers all YAML files in the directory tree
        2. Parses each file and extracts all configuration keys
        3. Records metadata including file path, nesting depth, and hierarchy level
        4. Handles nested dictionaries and lists appropriately
        5. Stores file modification times for incremental updates

        Files are processed in a deterministic order to ensure consistent
        behavior across different environments.
        """

        self._files = discover_config_files(Path(self._base))
        self._files.pop(self._fn, None)  # Remove index file itself if present
        self._files.pop(str(Path(self._base) / self._fn), None)

        for dict_ref, _ in self._files.items():
            try:
                cfg = _load_config(dict_ref=dict_ref, files=self._files)
            except Exception as e:
                print(f"Warning: Failed to load config '{dict_ref}': {e}")
                continue

            # Recursively index keys
            if cfg:
                self._index_config(cfg, dict_ref)

        self._save()

    def _update(self):
        """Update the index if any files were added/modified or removed."""

        files = discover_config_files(Path(self._base))
        files.pop(self._fn, None)  # Remove index file itself if present
        files.pop(str(Path(self._base) / self._fn), None)

        rebuild_needed = False

        # Find out if any files were added/removed or modified
        for dict_ref, file_info in files.items():
            if dict_ref not in self._files:
                rebuild_needed = True
                break
            elif file_info[Labels.MTIME] != self._files[dict_ref][Labels.MTIME]:
                rebuild_needed = True
                break
        # Check for removed configuration files
        if not rebuild_needed:
            if set(self._files.keys()) != set(files.keys()):
                rebuild_needed = True

        if rebuild_needed:
            self._build()

    def _index_config(self, cfg: dict, dict_ref: str):
        """Recursively index keys in the configuration dictionary."""

        def recurse(sub_cfg: dict, current_path: list[str], level: int):
            for key, value in sub_cfg.items():
                # Add key to index
                self.add(
                    key=key,
                    level=(
                        self._files[dict_ref][Labels.LEVEL]
                        if Labels.LEVEL in self._files[dict_ref]
                        else 0
                    ),
                    depth=len(current_path),
                    dict_ref=dict_ref,
                    path=current_path,
                )
                if isinstance(value, dict):
                    # Recurse into nested dictionary
                    recurse(value, current_path + [key], level)

        recurse(sub_cfg=cfg, current_path=[], level=0)

    def add(
        self, key: str, level: int, depth: int, dict_ref: str, path: str | list[str]
    ) -> None:
        """Add a configuration key entry to the index.

        Adds metadata for a configuration key to the internal index, including
        its hierarchy level, nesting depth, source file, and path information.
        This method is typically called during index building.

        Args:
            key (str): The configuration key to add.
            level (int): Hierarchy level (0 for root files, higher for subdirectories).
            depth (int): Nesting depth within the configuration structure.
            dict_ref (str): Reference to the source file containing this key.
            path (str | list[str]): The path to this key within the configuration.

        Example:
            >>> index = KeyIndex()
            >>> index.add('host', 0, 1, 'config/db.yaml', ['database', 'host'])
        """
        newentry = {
            Labels.LEVEL: level,
            Labels.DEPTH: depth,
            Labels.DICT_REF: dict_ref,
            Labels.PATH: (
                list(path) if isinstance(path, list) else [path]
            ),  # Create new list instance
        }

        if key not in self._index:
            self._index[key] = [newentry]
        elif not self.has_entry(newentry, self._index[key]):
            self._index[key].append(newentry)

    def has_entry(self, entry: dict, list_of_entries: list[dict]) -> bool:
        for e in list_of_entries:
            if self._is_same_entry(entry, e):
                return True
        return False

    def _is_same_entry(self, entry1: dict, entry2: dict) -> bool:
        return (
            entry1[Labels.LEVEL] == entry2[Labels.LEVEL]
            and entry1[Labels.DEPTH] == entry2[Labels.DEPTH]
            and entry1[Labels.DICT_REF] == entry2[Labels.DICT_REF]
            and entry1[Labels.PATH] == entry2[Labels.PATH]
        )
