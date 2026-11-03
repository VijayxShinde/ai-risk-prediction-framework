"""
Pytest Configuration and Shared Fixtures
Global pytest setup, configuration, and reusable fixtures for all tests.
"""

import json
import os
from pathlib import Path
from typing import Dict, List

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Return the data directory path."""
    return project_root / "data"


@pytest.fixture(scope="session")
def github_issues_dataset(data_dir: Path) -> List[Dict]:
    """Load GitHub issues dataset for testing."""
    dataset_file = data_dir / "github_issues_tensorflow.json"
    if dataset_file.exists():
        with open(dataset_file, "r") as f:
            return json.load(f)
    return []


# Global pytest configuration
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "unit: marks tests as unit tests")
    config.addinivalue_line("markers", "benchmark: marks tests as benchmark tests")
