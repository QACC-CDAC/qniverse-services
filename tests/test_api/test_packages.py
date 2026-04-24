"""Tests for package installation endpoints"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


class TestPackageEndpoints:
    """Test suite for package installation endpoints"""
    
    def test_install_packages_success(self, test_client: TestClient, api_key: str):
        """Test successful package installation request"""
        response = test_client.post(
            "/api/v1/packages/install",
            json={
                "username": "test_user",
                "packages": ["requests", "numpy"]
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "queued"
        assert "job_id" in data
        assert data["username"] == "test_user"
        assert len(data["packages"]) == 2
    
    def test_install_packages_invalid_username(self, test_client: TestClient, api_key: str):
        """Test with invalid username (path traversal attempt)"""
        response = test_client.post(
            "/api/v1/packages/install",
            json={
                "username": "../../etc/passwd",
                "packages": ["requests"]
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 400
    
    def test_install_packages_empty_list(self, test_client: TestClient, api_key: str):
        """Test with empty packages list"""
        response = test_client.post(
            "/api/v1/packages/install",
            json={
                "username": "test_user",
                "packages": []
            },
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 422
    
    def test_get_job_status_not_found(self, test_client: TestClient, api_key: str):
        """Test getting status of non-existent job"""
        response = test_client.get(
            "/api/v1/packages/status/invalid-job-id",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 404
    
    def test_list_user_jobs(self, test_client: TestClient, api_key: str):
        """Test listing jobs for a user"""
        # First create a job
        install_response = test_client.post(
            "/api/v1/packages/install",
            json={
                "username": "test_list_user",
                "packages": ["requests"]
            },
            headers={"X-API-Key": api_key}
        )
        
        # Then list jobs
        response = test_client.get(
            "/api/v1/packages/user/test_list_user/jobs?limit=5",
            headers={"X-API-Key": api_key}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_install_packages_missing_auth(self, test_client: TestClient):
        """Test without API key"""
        response = test_client.post(
            "/api/v1/packages/install",
            json={
                "username": "test_user",
                "packages": ["requests"]
            }
        )
        
        assert response.status_code == 401