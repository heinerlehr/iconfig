"""
Shared test fixtures and configuration for feedbackdigester tests.
"""
import os
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from a .env file for tests
load_dotenv(dotenv_path=Path(__file__) / '.env.test')

