import os
from pathlib import Path
import yaml
from typing import Any, Tuple, overload, TypeVar

from iconfig.labels import Labels
from iconfig.keyindex import KeyIndex
from iconfig.utils import get_key_path

T = TypeVar('T')

def singleton_or_not(class_):
    """
    A decorator that conditionally implements the singleton pattern for a class.

    In the configuration files, a setting '<class_name>.singleton' can be specified if true,
    the class will behave as a singleton (only one instance exists). If false, a new instance
    will be created each time.

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

@singleton_or_not
class iConfig:
    """Class to handle iconfig configuration files."""

    _base: str = "config"  
    
    def __init__(self):
        # Holds the actual configuration files
        self._cfg={}

        if (base:=os.getenv("INCONFIG_HOME")) is not None:
            self._base = base
        self._ki = KeyIndex()

    # When no default is provided, it might raise KeyError or return Any
    @overload
    def get(self, key:str, **kwargs:str|list[str]) -> Any: ...
    
    # When default is provided, return type is T | None
    @overload 
    def get(self, key:str, *, default:T, **kwargs:str|list[str]) -> T: ...
    
    # When default is None, return type could be Any or None
    @overload
    def get(self, key:str, *, default:None, **kwargs: str|list[str]) -> Any|None: ...

    def __call__(self, *args: str|list[str], default:T|None=None, **kwargs:str|list[str]) -> T|Any|None:
        # Forwards to get method
        return self.get(*args, default=default, **kwargs)
    
    ##################################################################################
    # Main access functions
    ##################################################################################
    
    def get(self, key:str, *args: str|list[str], default:T|None=None, **kwargs:str|list[str]) -> Any:
        """Get a configuration value by key/path.

        Args:
            *args: Positional arguments representing the key or path.
            default: Default value to return if key is not found.
            **kwargs: Keyword arguments representing key/path pairs.
        Returns:
            The configuration value or default if not found.
    """

        path, level, depth, forcefirst = self._prep_args(*args, **kwargs)
        key, path = get_key_path(key, path)

        if not (entry := self._ki.get(key=key, path=path, level=level, depth=depth, forcefirst=forcefirst)):
            return default
        else:
            return self._lookup(key=key, entry=entry, default=default)

    def set(self, key:str, *args: str|list[str], value: Any, **kwargs:str|list[str]) -> None:
        """Get a configuration value by key/path.

        Args:
            *args: Positional arguments representing the key or path.
            default: Default value to return if key is not found.
            **kwargs: Keyword arguments representing key/path pairs.
        Returns:
            The configuration value or default if not found.
    """
        
        path, level, depth, forcefirst = self._prep_args(*args, **kwargs)
        key, path = get_key_path(key, path)

        if not (entry := self._ki.get(key=key, path=path, level=level, depth=depth, forcefirst=forcefirst)):
            return 
        else:
            return self._update_nested(key=key, entry=entry, value=value)
        
    def whereis(self, key:str, *args: str|list[str], **kwargs:str|list[str]) -> list|None:
        """Return the index entry for the given key."""

        path, level, depth, _ = self._prep_args(*args, **kwargs)
        key, path = get_key_path(key, path)
        return self._ki.whereis(key=key, path=path, level=level, depth=depth)
    
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
    
    def _lookup(self, key:str, entry:dict, default: Any=None) -> Any:
        """ Lazy lookup up of entries. """
        dict_ref = entry[Labels.DICT_REF]
        path = entry[Labels.PATH]

        if dict_ref not in self._cfg:
            try:
                self._cfg[dict_ref] = self._load_config(dict_ref)
            except Exception as e:
                raise RuntimeError(f"Failed to load config for {dict_ref}: {e}")
        
        entry = self._get_nested(data=self._cfg[dict_ref], path=path)
        return self.expand_env(entry[key]) if key in entry else self.expand_env(default)
    
    def _get_nested(self, data:dict, path:list[str]) -> Any:
        """Retrieve nested value from dictionary based on path."""
        current = data
        for p in path:
            if p in current:
                current = current[p]
            else:
                None
        return current

    def expand_env(self,obj):
        if isinstance(obj, str):
            return os.path.expandvars(obj)
        elif isinstance(obj, list):
            return [self.expand_env(x) for x in obj]
        elif isinstance(obj, dict):
            return {k: self.expand_env(v) for k, v in obj.items()}
        else:
            return obj
    
    def _update_nested(self, key:str, entry:dict, value:Any) -> None:
        """ Lazy update of entries. """
        dict_ref = entry[Labels.DICT_REF]
        path = entry[Labels.PATH]

        if dict_ref not in self._cfg:
            try:
                self._cfg[dict_ref] = self._load_config(dict_ref)
            except Exception as e:
                raise RuntimeError(f"Failed to load config for {dict_ref}: {e}")
        
        self._set_nested(data=self._cfg[dict_ref], path=path, key=key, value=value)

    def _set_nested(self, data:dict, path:list[str], key:str, value:Any) -> None:
        """Set nested value in dictionary based on path."""
        current = data
        for p in path:
            if p not in current or not isinstance(current[p], dict):
                current[p] = {}
            current = current[p]
        current[key] = value

    def _load_config(self, dict_ref:str) -> dict:
        """Load configuration file given its dict_ref."""
        if not (file_path := Path(self._ki._files.get(dict_ref, {}).get(Labels.FILE_PATH))).exists():
            raise FileNotFoundError(f"Configuration file '{dict_ref}' not found")       
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file '{dict_ref}' not found")
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)
    
        
    