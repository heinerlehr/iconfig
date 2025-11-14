"""iConfig: Hierarchical configuration management for Python applications.

This package provides a simple, powerful interface for managing hierarchical
configuration data across multiple YAML files with fast key-based lookups.

Example:
    Basic usage::

        from iconfig import iConfig

        config = iConfig()
        app_name = config.get('app_name')
        db_host = config.get('host', path=['database'])
"""

__version__ = "0.1.4"
__all__ = ["iConfig", "Labels"]

def main() -> None:
    """CLI entry point for iconfig package."""
    print("iConfig: Hierarchical configuration management")
    print(f"Version: {__version__}")
    print("Usage: from iconfig import iConfig")
