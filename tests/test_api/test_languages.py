"""Tests for languages endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestLanguagesEndpoint:
    """Test suite for languages endpoints"""
    
    def test_get_languages(self, test_client: TestClient):
        """Test get supported languages"""
        response = test_client.get("/api/v1/languages")
        
        assert response.status_code == 200
        data = response.json()
        assert "languages" in data
        assert len(data["languages"]) > 0
    
    def test_get_target_languages(self, test_client: TestClient):
        """Test get target languages for a source"""
        response = test_client.get("/api/v1/languages/python/targets")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert "javascript" in data
    
    def test_get_language_pairs(self, test_client: TestClient):
        """Test get all language pairs"""
        response = test_client.get("/api/v1/languages/pairs")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0