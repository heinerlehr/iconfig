.. iConfig documentation master file

iConfig
=======

A hierarchical configuration management system for Python applications that provides fast key-based lookups across multiple YAML configuration files.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api
   readthedocs-setup

OBJECTIVE
=========

``iconfig`` is designed to solve the problem of managing complex, hierarchical configuration in modern applications. It provides a clean, simple interface with powerful features underneath:

- **Simple API**: Just import ``iConfig`` and call ``config.get('key')`` - that's it!
- **Hierarchical Configuration Loading**: Automatically discovers and indexes YAML files across directory structures
- **Fast Key Lookups**: Build an index once, then perform O(1) key lookups without re-parsing files
- **Singleton Pattern**: One configuration instance per application (configurable)
- **Environment Variable Expansion**: Supports ``${VAR}`` syntax in configuration values
- **Level-based Overrides**: Higher-level configurations can override lower-level ones
- **Path-based Filtering**: Find keys within specific configuration contexts
- **Configuration Tracing**: Use ``whereis()`` to find exactly where a configuration value comes from

Perfect for applications that need to merge configuration from multiple sources (system-wide, user-specific, project-specific) with predictable override behavior and a clean, intuitive API.

INSTALLATION
============

Prerequisites
-------------

- Python 3.10+
- PyYAML
- python-dotenv (optional, for .env file support)

Install with uv (recommended)
------------------------------

.. code-block:: bash

   git clone https://github.com/heinerlehr/iconfig.git
   cd iconfig
   uv sync --dev
   uv pip install -e .

Install with pip
----------------

.. code-block:: bash

   git clone https://github.com/heinerlehr/iconfig.git
   cd iconfig
   pip install -e .

Dependencies
------------

.. code-block:: bash

   pip install pyyaml python-dotenv

Environment Variables
---------------------

Set these environment variables to customize behavior:

- ``INCONFIG_HOME``: Configuration directory (default: ``"config"``)
- ``INCONFIG_INDEXFN``: Index file name (default: ``".index.yaml"``)

USAGE
=====

Basic Usage
-----------

.. code-block:: python

   from iconfig import iConfig

   # Initialize with default config directory (or set INCONFIG_HOME)
   config = iConfig()

   # Get a configuration value
   app_name = config.get('app_name')
   database_port = config.get('port', path=['database'])

   # Get with fallback default
   api_timeout = config.get('timeout', default=30)

   # Use as a callable (shorthand)
   debug_mode = config('debug', default=False)

Environment Variable Expansion
------------------------------

Configuration values support environment variable expansion:

.. code-block:: yaml

   # config.yaml
   database:
     url: "${DATABASE_URL}"
     host: "${DB_HOST:-localhost}"    # With default value
   paths:
     data: "${HOME}/data"
     logs: "${LOG_DIR}/app.log"

Keys
----

Search can be carried out with a string key and a list of qualifier. In order to access ``key`` in this structure:

.. code-block:: yaml

   level1:
       level2:
           level3:
               key: value

all of the following calls will result in ``value``:

.. code-block:: python

   config = iConfig()
   # All equivalent
   value = config('key', path=['level1','level2','level3'])
   value = config('key', 'level1', 'level2', 'level3')
   value = config('level1.level2.level3.key')

Overwriting and search algorithm
--------------------------------

iConfig does not overwrite any (duplicate) key found in configuration files. Instead, it keeps all (used) configuration files separately in memory. 
With knowledge of the appropriate source, a developer can use the exact key wanted.

iConfig differentiates ``depth`` and ``level``. 

- ``level`` is the hierarchy level. Top level configuration files in ``ICONFIG_HOME`` receive ``level`` 0. YAML files found in subdirectories will receive level 1 and so forth.

- ``depth`` is the nesting level. Within a configuration file, top-level keys have ``depth`` 0. Subkeys have ``depth`` 1 and so forth. ``depth`` is equivalent to the length of ``path``.

- ``path`` is the "path" within the YAML file to the key. For the following example:

.. code-block:: yaml

   level1:
       level2:
           level3:
               key: value

the key ``key`` would have the path ``['level1', 'level2', 'level3]`` or ``level1.level2.level3`` in iConfig's special notation.

When not specifying ``level``, ``depth`` and ``path``, iConfig prefers:

- the highest level (i.e. deepest configuration file)
- the lowest depth (i.e. the lowest nesting)

If that is not unique (i.e. several keys at the same level and depth), a ``KeyError`` will be thrown. Users are then encouraged to specify
the path either explicitly ``['level1', 'level2', 'level3]``) or in iConfig's special notation (``level1.level2.level3``).

Example directory Structure
---------------------------

::

   your-project/
   ├── config/                    # Default config directory
   │   ├── global.yaml           # System-wide settings
   │   ├── app.yaml              # Application settings
   │   └── modules/              # Module-specific configs
   │       ├── database.yaml
   │       └── api.yaml
   ├── .env                      # Environment variables (optional)
   └── your_app.py

**config/global.yaml:**

.. code-block:: yaml

   app_name: "MyApp"
   version: "1.0.0"
   database:
     host: "localhost"
     port: 5432
     timeout: 30
   logging:
     level: "INFO"
     file: "/var/log/myapp.log"

**config/modules/database.yaml:**

.. code-block:: yaml

   database:
     pool_size: 10
     timeout: 60        # Overrides global timeout for database
     ssl_enabled: true

Advanced Usage
--------------

.. code-block:: python

   import os
   from iconfig import iConfig

   # Use custom configuration directory
   os.environ['INCONFIG_HOME'] = '/etc/myapp'
   config = iConfig()

   # Get values with path filtering
   db_host = config.get('host', path=['database'])
   api_host = config.get('host', path=['api'])

   # Get values at specific hierarchy levels
   global_timeout = config.get('timeout', level=0)    # Top-level files only
   module_timeout = config.get('timeout', level=1)    # Module-level files only

   # Get values at specific depths
   root_values = config.get('debug', depth=0)         # Top-level keys only
   nested_values = config.get('debug', depth=2)       # 2 levels deep

   # Handle ambiguous keys
   try:
       port = config.get('port')  # Returns None if not found
   except Exception:
       port = config.get('port', forcefirst=True)     # Take first match

   # Set configuration values in memory
   config.set('database_timeout', 120)

   # Find where a configuration key is defined
   location = config.whereis('app_name')
   print(f"app_name found in: {location}")

LIMITATIONS
===========

Current Limitations
-------------------

1. **YAML Only**: Currently only supports YAML configuration files (``.yaml``, ``.yml``)
2. **Read-Heavy Optimized**: Designed for read-heavy workloads; frequent updates require index rebuilds
3. **Memory Usage**: Keeps an in-memory index of all configuration keys
4. **File System Dependency**: Requires file system access; doesn't support remote configuration stores
5. **Limited Environment Variable Syntax**: Basic ``${VAR}`` expansion only; ``${VAR:-default}`` syntax requires custom implementation

Design Decisions
-----------------

- **Lazy Loading**: Configuration files are only parsed when their values are accessed
- **Index Persistence**: Index is saved to ``.index.yaml`` for faster startup times
- **Automatic Rebuilds**: Index automatically rebuilds when configuration files change
- **Level vs Depth**: 

  - **Level**: File hierarchy level (0=top-level files, 1=subdirectory files)
  - **Depth**: Key nesting depth within files (0=root keys, 1=nested once)

Performance Considerations
--------------------------

- Initial index building: O(n) where n = total keys across all files
- Key lookups: O(1) average case
- File watching: Uses file modification times, not real-time file system events
- Memory usage: Proportional to number of unique keys across all configuration files

ARCHITECTURE
============

Design Overview
---------------

``iconfig`` uses a two-layer architecture:

- **``iConfig``**: The user-facing API that provides a clean, simple interface
- **``KeyIndex``**: The internal engine that handles file discovery, indexing, and fast lookups

This separation allows for a simple user experience while maintaining powerful functionality under the hood.

.. code-block:: python

   # User interacts with iConfig
   from iconfig import iConfig
   config = iConfig()
   value = config.get('key')

   # iConfig internally uses KeyIndex for heavy lifting
   # KeyIndex handles file scanning, indexing, YAML parsing, etc.

Singleton Behavior
------------------

By default, ``iConfig`` uses a singleton pattern - all instances share the same configuration data. 

This can be controlled via configuration settings by including a section:

.. code-block:: yaml

   iconfig:
       singleton: false

in any *.yaml in the configuration path.

DEVELOPMENT
===========

Running Tests
-------------

.. code-block:: bash

   # Run all tests
   uv run pytest

   # Run with coverage
   uv run pytest --cov=iconfig

   # Run specific test file
   uv run pytest tests/test_iconfig.py -v

Project Structure
-----------------

::

   iconfig/
   ├── src/iconfig/
   │   ├── __init__.py        # Main exports (iConfig class)
   │   ├── iconfig.py         # Main iConfig user interface
   │   ├── keyindex.py        # Internal KeyIndex engine
   │   ├── labels.py          # String constants for keys
   │   └── utils.py           # Utility functions
   ├── tests/
   │   ├── conftest.py        # Pytest fixtures
   │   ├── test_iconfig.py    # Main iConfig interface tests
   │   ├── test_keyindex.py   # Internal KeyIndex tests
   │   └── fixtures/          # Test configuration files
   └── README.md

Documentation
-------------

Full API documentation is available online and can be built locally:

**Online Documentation:**

- **Read the Docs**: `iconfig.readthedocs.io <https://iconfig.readthedocs.io/>`_ (automatically updated)
- **GitHub Pages**: `heinerlehr.github.io/iconfig <https://heinerlehr.github.io/iconfig/>`_ (updated on each commit)

**Local Documentation:**

.. code-block:: bash

   # Build documentation
   make build-docs

   # Build and serve documentation locally
   make serve-docs

   # Build docs before committing (automatic via git hook)
   make commit

The documentation includes:

- Complete API reference for all classes and methods
- Usage examples and configuration patterns
- Architecture overview and design decisions

**Documentation Features:**

- 📚 Automatic builds on every commit via GitHub Actions
- 🔧 Pre-commit hooks ensure docs build successfully
- 🌐 Published to Read the Docs and GitHub Pages
- 📖 Built from docstrings and RST files in ``docs/`` directory

Contributing
------------

1. Fork the repository
2. Create a feature branch: ``git checkout -b feature-name``
3. Make changes and add tests
4. Run tests: ``uv run pytest``
5. Build documentation: ``make build-docs``
6. Submit a pull request

LICENSE
=======

This project is licensed under the MIT License - see the `LICENSE <https://github.com/heinerlehr/iconfig/blob/main/LICENSE>`_ file for details.

Copyright (c) 2025 Heiner Lehr

CHANGELOG
=========

v0.1.0
------

- Initial release
- Clean iConfig interface with simple ``get()``, ``set()``, ``whereis()`` methods
- Callable interface: ``config('key')`` shorthand
- Singleton pattern support (configurable)
- Basic hierarchical configuration loading
- YAML file support with anchors and aliases
- Environment variable expansion
- Index-based fast lookups with KeyIndex engine
- Configuration source tracing

AUTHORS
=======

- `heinerlehr <https://github.com/heinerlehr>`_

SUPPORT
=======

- **Issues**: `GitHub Issues <https://github.com/heinerlehr/iconfig/issues>`_
- **Documentation**: See this documentation and inline code documentation
- **Examples**: Check the ``tests/fixtures/`` directory for configuration examples

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

