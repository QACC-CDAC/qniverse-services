"""Tests for transpilation endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestTranspileEndpoint:
    """Test suite for transpile endpoint"""
    
    def test_transpile_success(self, test_client: TestClient, api_key: str, sample_python_code: str):
        """Test successful transpilation"""
        response = test_client.post(
            "/api/v1/transpile",
            json={
                "source_code": sample_python_code,
                "source_lang": "python",
                "target_lang": "javascript",
                "options": {}
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "transpiled_code" in data
        assert data["source_lang"] == "python"
        assert data["target_lang"] == "javascript"
    
    def test_transpile_invalid_language(self, test_client: TestClient, api_key: str):
        """Test with invalid language"""
        response = test_client.post(
            "/api/v1/transpile",
            json={
                "source_code": "print('hello')",
                "source_lang": "invalid_lang",
                "target_lang": "javascript"
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 422
    
    def test_transpile_empty_code(self, test_client: TestClient, api_key: str):
        """Test with empty source code"""
        response = test_client.post(
            "/api/v1/transpile",
            json={
                "source_code": "",
                "source_lang": "python",
                "target_lang": "javascript"
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 422
    
    def test_transpile_no_api_key(self, test_client: TestClient):
        """Test without API key"""
        response = test_client.post(
            "/api/v1/transpile",
            json={
                "source_code": "print('hello')",
                "source_lang": "python",
                "target_lang": "javascript"
            }
        )
        
        assert response.status_code == 401
    
    def test_transpile_invalid_api_key(self, test_client: TestClient):
        """Test with invalid API key"""
        response = test_client.post(
            "/api/v1/transpile",
            json={
                "source_code": "print('hello')",
                "source_lang": "python",
                "target_lang": "javascript"
            },
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401