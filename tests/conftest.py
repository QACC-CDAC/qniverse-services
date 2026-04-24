"""Pytest configuration and fixtures"""

import pytest
from typing import Generator
from fastapi.testclient import TestClient
from src.main import app
from src.config import get_settings


@pytest.fixture(scope="session")
def test_client() -> Generator:
    """Create test client"""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def api_key() -> str:
    """Get valid API key for testing"""
    settings = get_settings()
    return settings.API_KEYS[0] if settings.API_KEYS else "test-key"


@pytest.fixture
def sample_python_code() -> str:
    """Sample Python code for testing"""
    return """
def greet(name: str) -> str:
    return f"Hello, {name}!"

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
"""


@pytest.fixture
def sample_javascript_code() -> str:
    """Sample JavaScript code for testing"""
    return """
function greet(name) {
    return `Hello, ${name}!`;
}

class Calculator {
    add(a, b) {
        return a + b;
    }
}
"""