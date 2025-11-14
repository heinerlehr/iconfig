.. iConfig documentation master file, created by
   sphinx-quickstart on Fri Nov 14 09:26:43 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to iConfig's documentation!
===================================

iConfig is a hierarchical configuration management system for Python applications that provides fast key-based lookups across multiple YAML configuration files.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   api
   readthedocs-setup

Quick Start
===========

Installation
------------

.. code-block:: bash

   pip install iconfig

Basic Usage
-----------

.. code-block:: python

   from iconfig import iConfig
   
   # Initialize configuration
   config = iConfig()
   
   # Get configuration values
   app_name = config.get('app_name')
   db_port = config.get('port', path=['database'])
   
   # Use with defaults
   timeout = config.get('timeout', default=30)
   
   # Callable interface
   debug = config('debug', default=False)

Features
========

* **Simple API**: Just import iConfig and call config.get('key')
* **Hierarchical Configuration Loading**: Automatically discovers YAML files
* **Fast Key Lookups**: O(1) lookups with built-in indexing
* **Environment Variable Expansion**: Supports ${VAR} syntax
* **Configuration Tracing**: Find where values come from with whereis()
* **Singleton Pattern**: One configuration instance per application

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

