#!/usr/bin/env python3
"""Script to bump version in both pyproject.toml and src/iconfig/__init__.py"""

import re
import sys

def bump_version(bump_type):
    """Bump version: 'patch', 'minor', or 'major'"""
    
    # Read pyproject.toml
    with open('pyproject.toml') as f:
        pyproject_content = f.read()
    
    # Extract current version
    match = re.search(r'version = "(\d+\.\d+\.\d+)"', pyproject_content)
    if not match:
        print("Error: Could not find version in pyproject.toml")
        sys.exit(1)
    
    current_version = match.group(1)
    parts = [int(x) for x in current_version.split('.')]
    
    # Bump version
    if bump_type == 'patch':
        parts[2] += 1
    elif bump_type == 'minor':
        parts[1] += 1
        parts[2] = 0
    elif bump_type == 'major':
        parts[0] += 1
        parts[1] = 0
        parts[2] = 0
    else:
        print(f"Error: Unknown bump type '{bump_type}'. Use 'patch', 'minor', or 'major'.")
        sys.exit(1)
    
    new_version = '.'.join(str(p) for p in parts)
    
    # Update pyproject.toml
    new_pyproject = re.sub(
        r'version = "\d+\.\d+\.\d+"',
        f'version = "{new_version}"',
        pyproject_content
    )
    with open('pyproject.toml', 'w') as f:
        f.write(new_pyproject)
    
    # Update __init__.py
    with open('src/iconfig/__init__.py') as f:
        init_content = f.read()
    
    new_init = re.sub(
        r'__version__ = "\d+\.\d+\.\d+"',
        f'__version__ = "{new_version}"',
        init_content
    )
    with open('src/iconfig/__init__.py', 'w') as f:
        f.write(new_init)
    
    print(f"Version bumped: {current_version} -> {new_version}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <patch|minor|major>")
        sys.exit(1)
    
    bump_version(sys.argv[1])
