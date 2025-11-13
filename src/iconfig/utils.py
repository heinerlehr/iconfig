from pathlib import Path

from iconfig.labels import Labels

def discover_config_files(base_path: Path, pattern: str = "*.yaml") -> dict[str, dict[str, str|float]]:
    """Discover configuration files in the given base path matching the pattern."""
    files = list(base_path.rglob(pattern))
    ret = {}
    for file in files:
        if file.is_file():
            dict_ref = str(file.resolve().relative_to(base_path.resolve()))
            ret[dict_ref] = {
                Labels.FILE_PATH: str(file.resolve()),
                Labels.MTIME: file.stat().st_mtime,
                Labels.LEVEL: len(file.relative_to(base_path).parents) - 1
            }
    return ret

