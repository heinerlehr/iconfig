
class Labels():
    """ Labels for keys in the key index and file entries. """
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
        """Make the class iterable over its string values."""
        # Get all class attributes that are strings (not methods/special attributes)
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and isinstance(getattr(cls, attr_name), str):
                yield getattr(cls, attr_name)
    
    @classmethod
    def values(cls):
        """Return all label values as a list."""
        return [getattr(cls, attr) for attr in dir(cls) 
                if not attr.startswith('_') and isinstance(getattr(cls, attr), str)]
    
    @classmethod
    def names(cls):
        """Return all label names as a list."""
        return [attr for attr in dir(cls) 
                if not attr.startswith('_') and isinstance(getattr(cls, attr), str)]
    
    @classmethod
    def items(cls):
        """Return (name, value) pairs."""
        return [(attr, getattr(cls, attr)) for attr in dir(cls)
                if not attr.startswith('_') and isinstance(getattr(cls, attr), str)]


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
    
