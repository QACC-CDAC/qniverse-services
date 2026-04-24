"""Tests for health check endpoints"""

import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Test suite for health check endpoints"""
    
    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint"""
        response = test_client.get("/api/v1/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "version" in data
        assert "services" in data
    
    def test_readiness_check(self, test_client: TestClient):
        """Test readiness probe"""
        response = test_client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
    
    def test_liveness_check(self, test_client: TestClient):
        """Test liveness probe"""
        response = test_client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] == True
        assert "timestamp" in data