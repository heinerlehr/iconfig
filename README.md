# iconfig

A hierarchical configuration management system for Python applications that provides fast key-based lookups across multiple YAML configuration files.

## OBJECTIVE

`iconfig` is designed to solve the problem of managing complex, hierarchical configuration in modern applications. It provides a clean, simple interface with powerful features underneath:

- **Simple API**: Just import `iConfig` and call `config.get('key')` - that's it!
- **Hierarchical Configuration Loading**: Automatically discovers and indexes YAML files across directory structures
- **Fast Key Lookups**: Build an index once, then perform O(1) key lookups without re-parsing files
- **Singleton Pattern**: One configuration instance per application (configurable)
- **Environment Variable Expansion**: Supports `${VAR}` syntax in configuration values
- **Level-based Overrides**: Higher-level configurations can override lower-level ones
- **Path-based Filtering**: Find keys within specific configuration contexts
- **Configuration Tracing**: Use `whereis()` to find exactly where a configuration value comes from

Perfect for applications that need to merge configuration from multiple sources (system-wide, user-specific, project-specific) with predictable override behavior and a clean, intuitive API.

## INSTALLATION

### Prerequisites

- Python 3.12+
- PyYAML
- python-dotenv (optional, for .env file support)

### Install with uv (recommended)

```bash
git clone https://github.com/heinerlehr/iconfig.git
cd iconfig
uv sync --dev
uv pip install -e .
```

### Install with pip

```bash
git clone https://github.com/heinerlehr/iconfig.git
cd iconfig
pip install -e .
```

### Dependencies

```bash
pip install pyyaml python-dotenv
```

## USAGE

### Basic Usage

```python
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
```

### Directory Structure

```
your-project/
├── config/                    # Default config directory
│   ├── global.yaml           # System-wide settings
│   ├── app.yaml              # Application settings
│   └── modules/              # Module-specific configs
│       ├── database.yaml
│       └── api.yaml
├── .env                      # Environment variables (optional)
└── your_app.py
```

### Configuration Examples

**config/global.yaml:**
```yaml
app_name: "MyApp"
version: "1.0.0"
database:
  host: "localhost"
  port: 5432
  timeout: 30
logging:
  level: "INFO"
  file: "/var/log/myapp.log"
```

**config/modules/database.yaml:**
```yaml
database:
  pool_size: 10
  timeout: 60        # Overrides global timeout for database
  ssl_enabled: true
```

### Advanced Usage

```python
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
```

### Environment Variables

Set these environment variables to customize behavior:

- `INCONFIG_HOME`: Configuration directory (default: `"config"`)
- `INCONFIG_INDEXFN`: Index file name (default: `".index.yaml"`)

### Environment Variable Expansion

Configuration values support environment variable expansion:

```yaml
# config.yaml
database:
  url: "${DATABASE_URL}"
  host: "${DB_HOST:-localhost}"    # With default value
paths:
  data: "${HOME}/data"
  logs: "${LOG_DIR}/app.log"
```

## LIMITATIONS

### Current Limitations

1. **YAML Only**: Currently only supports YAML configuration files (`.yaml`, `.yml`)
2. **Read-Heavy Optimized**: Designed for read-heavy workloads; frequent updates require index rebuilds
3. **Memory Usage**: Keeps an in-memory index of all configuration keys
4. **File System Dependency**: Requires file system access; doesn't support remote configuration stores
5. **Limited Environment Variable Syntax**: Basic `${VAR}` expansion only; `${VAR:-default}` syntax requires custom implementation

### Design Decisions

- **Lazy Loading**: Configuration files are only parsed when their values are accessed
- **Index Persistence**: Index is saved to `.index.yaml` for faster startup times
- **Automatic Rebuilds**: Index automatically rebuilds when configuration files change
- **Level vs Depth**: 
  - **Level**: File hierarchy level (0=top-level files, 1=subdirectory files)
  - **Depth**: Key nesting depth within files (0=root keys, 1=nested once)

### Performance Considerations

- Initial index building: O(n) where n = total keys across all files
- Key lookups: O(1) average case
- File watching: Uses file modification times, not real-time file system events
- Memory usage: Proportional to number of unique keys across all configuration files

## ARCHITECTURE

### Design Overview

`iconfig` uses a two-layer architecture:

- **`iConfig`**: The user-facing API that provides a clean, simple interface
- **`KeyIndex`**: The internal engine that handles file discovery, indexing, and fast lookups

This separation allows for a simple user experience while maintaining powerful functionality under the hood.

```python
# User interacts with iConfig
from iconfig import iConfig
config = iConfig()
value = config.get('key')

# iConfig internally uses KeyIndex for heavy lifting
# KeyIndex handles file scanning, indexing, YAML parsing, etc.
```

### Singleton Behavior

By default, `iConfig` uses a singleton pattern - all instances share the same configuration data. This can be controlled via configuration settings.

```python
config1 = iConfig()
config2 = iConfig()
assert config1 is config2  # Same instance
```

## DEVELOPMENT

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=iconfig

# Run specific test file
uv run pytest tests/test_iconfig.py -v
```

### Project Structure

```
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
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make changes and add tests
4. Run tests: `uv run pytest`
5. Submit a pull request

## LICENSE

[Add your license here]

## CHANGELOG

### v0.1.0
- Initial release
- Clean iConfig interface with simple `get()`, `set()`, `whereis()` methods
- Callable interface: `config('key')` shorthand
- Singleton pattern support (configurable)
- Basic hierarchical configuration loading
- YAML file support with anchors and aliases
- Environment variable expansion
- Index-based fast lookups with KeyIndex engine
- Configuration source tracing

## AUTHORS

- [heinerlehr](https://github.com/heinerlehr)

## SUPPORT

- **Issues**: [GitHub Issues](https://github.com/heinerlehr/iconfig/issues)
- **Documentation**: See this README and inline code documentation
- **Examples**: Check the `tests/fixtures/` directory for configuration examples
