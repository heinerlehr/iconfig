"""String constants and labels used throughout the iConfig system.

This module defines the :class:`Labels` class that provides string constants
used as dictionary keys and identifiers throughout the configuration system.
Using a centralized Labels class ensures consistency and prevents typos in
string literals across the codebase.

The Labels class provides string constants that can be used as dictionary keys
and includes utility methods for introspection and iteration over the available
labels.

Example:
    Using Labels for consistent key access::

        from iconfig.labels import Labels

        # Use labels as dictionary keys
        entry = {
            Labels.FILE_PATH: '/path/to/config.yaml',
            Labels.LEVEL: 0,
            Labels.PATH: ['database']
        }

        # Access values using Labels
        file_path = entry[Labels.FILE_PATH]

Attributes:
    The module exports the :class:`Labels` class with all configuration constants.
"""


class Labels:
    """String constants for configuration system keys and identifiers.

    Provides string constants used as dictionary keys and identifiers throughout
    the iConfig system. The class includes both the constant definitions and
    utility methods for introspection and iteration.

    The Labels class serves as a centralized location for all string constants
    used in the configuration system, preventing typos and ensuring consistency
    across the codebase.

    Attributes:
        INDEX (str): Key for index data in persistent storage ('index').
        FILES (str): Key for file metadata in persistent storage ('files').
        LEVEL (str): Key for hierarchy level information ('level').
        DEPTH (str): Key for nesting depth information ('depth').
        DICT_REF (str): Key for dictionary reference identifiers ('dict_ref').
        PATH (str): Key for path context information ('path').
        FILE_PATH (str): Key for file path information ('file_path').
        MTIME (str): Key for modification time information ('mtime').

    Example:
        Using Labels in configuration entries::

            entry = {
                Labels.FILE_PATH: '/etc/myapp/config.yaml',
                Labels.LEVEL: 0,
                Labels.DEPTH: 2,
                Labels.PATH: ['database', 'connection'],
                Labels.DICT_REF: 'config_main'
            }

            # Access values using Labels
            path = entry[Labels.FILE_PATH]
            level = entry[Labels.LEVEL]

    Note:
        This is a regular class (not an enum) that provides string constants
        and utility methods for working with those constants.
    """

    # Keys for .index.yaml
    INDEX = "index"
    FILES = "files"
    # Keys for key entries
    LEVEL = "level"
    DEPTH = "depth"
    DICT_REF = "dict_ref"
    PATH = "path"
    # Keys for file entries
    FILE_PATH = "file_path"
    MTIME = "mtime"

    @classmethod
    def __iter__(cls):
        """Make the class iterable over its string constant values.

        Allows iteration over all string constants defined in the Labels class,
        excluding methods and special attributes. This enables convenient loops
        over all available labels.

        Yields:
            str: Each string constant value defined in the Labels class.

        Example:
            >>> for label in Labels():
            ...     print(label)
            index
            files
            level
            ...
        """
        # Get all class attributes that are strings (not methods/special attributes)
        for attr_name in dir(cls):
            if not attr_name.startswith("_") and isinstance(
                getattr(cls, attr_name), str
            ):
                yield getattr(cls, attr_name)

    @classmethod
    def values(cls):
        """Return all label string values as a list.

        Collects all string constants defined in the Labels class into a list,
        excluding methods and special attributes.

        Returns:
            list[str]: List of all string constant values.

        Example:
            >>> Labels.values()
            ['index', 'files', 'level', 'depth', 'dict_ref', 'path', 'file_path', 'mtime']
        """
        return [
            getattr(cls, attr)
            for attr in dir(cls)
            if not attr.startswith("_") and isinstance(getattr(cls, attr), str)
        ]

    @classmethod
    def names(cls):
        """Return all label constant names as a list.

        Collects all attribute names that correspond to string constants,
        excluding methods and special attributes.

        Returns:
            list[str]: List of all constant attribute names.

        Example:
            >>> Labels.names()
            ['INDEX', 'FILES', 'LEVEL', 'DEPTH', 'DICT_REF', 'PATH', 'FILE_PATH', 'MTIME']
        """
        return [
            attr
            for attr in dir(cls)
            if not attr.startswith("_") and isinstance(getattr(cls, attr), str)
        ]

    @classmethod
    def items(cls):
        """Return (name, value) pairs for all label constants.

        Provides a dictionary-like items() interface for the Labels class,
        returning tuples of (attribute_name, string_value) for all constants.

        Returns:
            list[tuple[str, str]]: List of (name, value) pairs for all constants.

        Example:
            >>> Labels.items()
            [('INDEX', 'index'), ('FILES', 'files'), ('LEVEL', 'level'), ...]
        """
        return [
            (attr, getattr(cls, attr))
            for attr in dir(cls)
            if not attr.startswith("_") and isinstance(getattr(cls, attr), str)
        ]


if __name__ == "__main__":
    print("=== Iteration Test ===")
    for label in Labels():
        print(f"Label: {label}")

    print("\n=== Class Methods ===")
    print("Values:", Labels.values())
    print("Names:", Labels.names())
    print("Items:", Labels.items())

    print("\n=== Dictionary Usage ===")
    test_dict = {Labels.FILES: "test", Labels.INDEX: "value"}
    print(f"Dict keys: {list(test_dict.keys())}")
    print(f"Type of Labels.FILES: {type(Labels.FILES)}")
