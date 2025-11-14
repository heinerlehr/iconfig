import os
from pathlib import Path
import yaml
from typing import Any

from iconfig.labels import Labels
from iconfig.utils import discover_config_files, get_key_path

class KeyIndex:

    _base: str = "config"
    _fn:str = ".index.yaml"

    def __init__(self, load_index: bool = True):
        self._index = {}
        self._files = {}
        self._cfg = {}

        if (base:=os.getenv("INCONFIG_HOME")) is not None:
            self._base = base
        if (fn:=os.getenv("INCONFIG_INDEXFN")) is not None:
            self._fn = fn

        if load_index:
            self._load()

    ##################################################################################
    # (De)serialization
    ##################################################################################
    
    def _load(self):
        """Load index from persistent storage."""
        file_path = Path(self._base) / self._fn
        if not file_path.exists():
            self._build()
        else:
            try:
                with open(file_path, 'r') as f:
                    data = yaml.safe_load(f)
                    self._index = data.get(Labels.INDEX, {})
                    self._files = data.get(Labels.FILES, {})
            except Exception:
                self._build()
            
            # Make sure index is up to date
            self._update()

    def _save(self):
        """Save index to persistent storage."""
        data = {
            Labels.INDEX: self._index,
            Labels.FILES: self._files,
        }
        # Save to YAML file
        file_path = Path(self._base) / self._fn
        with open(file_path, 'w') as f:
            yaml.dump(data, f)

    ##################################################################################
    # Main access functions
    ##################################################################################

    def get(self, key:str, path:list[str]|str|None=None, level:int=-1, depth:int=-1, 
            forcefirst:bool=False, default: Any=None) -> Any:
        
        key, path = get_key_path(key, path)
        return self._find(key=key, path=path, level=level, depth=depth, forcefirst=forcefirst)

    def whereis(self, key:str, path:list[str]|str|None=None, level:int=-1, depth:int=-1) -> list|None:
        """Return the index entry for the given key."""

        if not (entries := self._find(key=key, path=path, level=level, depth=depth, 
                                      forcefirst=False, return_all=True)):
            return None
        ret = []
        if not isinstance(entries, list):
            entries = [entries]
        for entry in entries:
            ret.append({
                Labels.LEVEL: entry[Labels.LEVEL],
                Labels.PATH: entry[Labels.PATH],
            })
        return ret
    
    ##################################################################################
    # Internal helper function for finding/updating entries
    ##################################################################################

    def _find(self, key:str, path:list[str]|str|None=None, level:int=-1, depth:int=-1, 
             forcefirst:bool=False, return_all:bool=False) -> Any:
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
            for i in range(3):
                msg += f"\n{'/'.join(entries[i][Labels.PATH])}"
            raise KeyError(
                f"Ambiguous key '{key}': {length} entries at same level/depth"
            )


    ##################################################################################
    # Index building
    ##################################################################################
    def _build(self):
        """Build the index from scratch by scanning configuration files."""

        self._files = discover_config_files(Path(self._base))
        self._files.pop(self._fn, None)  # Remove index file itself if present
        self._files.pop(str(Path(self._base) / self._fn), None)

        for dict_ref, file_info in self._files.items():
            try:
                cfg = self._load_config(dict_ref)
            except Exception as e:
                print(f"Warning: Failed to load config '{dict_ref}': {e}")
                continue
            
            # Recursively index keys
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
                
    
    def _index_config(self, cfg:dict, dict_ref:str):
        """Recursively index keys in the configuration dictionary."""
        def recurse(sub_cfg:dict, current_path:list[str], level:int):
            for key, value in sub_cfg.items():
                if isinstance(value, dict):
                    # Recurse into nested dictionary
                    recurse(value, current_path + [key], level)
                else:
                    # Add key to index
                    self.add(
                        key=key,
                        level=self._files[dict_ref][Labels.LEVEL] if Labels.LEVEL in self._files[dict_ref] else 0,
                        depth=len(current_path),
                        dict_ref=dict_ref,
                        path=current_path,
                    )
        
        recurse(sub_cfg=cfg, current_path=[], level=0)

    def add(self, key:str, level:int, depth:int, dict_ref:str, path: str|list[str]) -> None:
        newentry = {
            Labels.LEVEL: level,
            Labels.DEPTH: depth,
            Labels.DICT_REF: dict_ref,
            Labels.PATH: list(path) if isinstance(path, list) else [path],  # Create new list instance
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

    def _is_same_entry(self, entry1:dict, entry2:dict) -> bool:
        return (entry1[Labels.LEVEL] == entry2[Labels.LEVEL] and
                entry1[Labels.DEPTH] == entry2[Labels.DEPTH] and
                entry1[Labels.DICT_REF] == entry2[Labels.DICT_REF] and
                entry1[Labels.PATH] == entry2[Labels.PATH])