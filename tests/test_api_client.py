"""
Unit tests for Semgrep API client.
"""

import json
import os
import pytest
import responses
import sys
from unittest.mock import Mock, patch
import requests

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from semgrep_deps_export.config import Config
from semgrep_deps_export.api_client import SemgrepAPIClient, SemgrepAPIError


class TestSemgrepAPIClient:
    """Test cases for SemgrepAPIClient."""
    
    @pytest.fixture
    def config(self):
        """Create test configuration."""
        return Config(
            token="test_token_12345678901234567890",
            deployment_id="test_deployment_123",
            deployment_slug="test_org"
        )
    
    @pytest.fixture
    def client(self, config):
        """Create test API client."""
        return SemgrepAPIClient(config)
    
    def test_init(self, client):
        """Test client initialization."""
        assert client.config is not None
        assert client.session is not None
        assert "Authorization" in client.session.headers
        assert client.session.headers["Authorization"].startswith("Bearer ")
    
    def test_mask_token(self, client):
        """Test token masking for logging."""
        # Short token
        short_masked = client._mask_token("abc123")
        assert short_masked == "******"
        
        # Long token
        long_masked = client._mask_token("test_token_12345678901234567890")
        assert long_masked.startswith("test")
        assert long_masked.endswith("7890")
        assert "*" in long_masked
    
    @responses.activate
    def test_successful_request(self, client):
        """Test successful API request."""
        mock_response = {
            "dependencies": [
                {
                    "id": "dep1",
                    "name": "test-package",
                    "version": "1.0.0",
                    "ecosystem": "npm",
                    "vulnerabilities": []
                }
            ],
            "cursor": "next_cursor",
            "has_more": True
        }
        
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json=mock_response,
            status=200
        )
        
        result = client.get_dependencies_page()
        
        assert "dependencies" in result
        assert len(result["dependencies"]) == 1
        assert result["has_more"] is True
    
    @responses.activate
    def test_401_error(self, client):
        """Test 401 authentication error."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"message": "Invalid token"},
            status=401
        )
        
        with pytest.raises(SemgrepAPIError) as exc_info:
            client.get_dependencies_page()
        
        assert "Authentication failed" in str(exc_info.value)
        assert exc_info.value.status_code == 401
    
    @responses.activate
    def test_403_error(self, client):
        """Test 403 forbidden error."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"message": "Insufficient permissions"},
            status=403
        )
        
        with pytest.raises(SemgrepAPIError) as exc_info:
            client.get_dependencies_page()
        
        assert "Access forbidden" in str(exc_info.value)
        assert exc_info.value.status_code == 403
    
    @responses.activate
    def test_404_error(self, client):
        """Test 404 not found error."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"message": "Deployment not found"},
            status=404
        )
        
        with pytest.raises(SemgrepAPIError) as exc_info:
            client.get_dependencies_page()
        
        assert "Deployment not found" in str(exc_info.value)
        assert exc_info.value.status_code == 404
    
    @responses.activate
    def test_429_rate_limit(self, client):
        """Test 429 rate limit error."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"message": "Rate limit exceeded"},
            status=429
        )
        
        with pytest.raises(SemgrepAPIError) as exc_info:
            client.get_dependencies_page()
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.status_code == 429
    
    @responses.activate
    def test_500_server_error(self, client):
        """Test 500 server error."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"message": "Internal server error"},
            status=500
        )
        
        with pytest.raises(SemgrepAPIError) as exc_info:
            client.get_dependencies_page()
        
        assert "Server error" in str(exc_info.value)
        assert exc_info.value.status_code == 500
    
    @responses.activate
    def test_pagination_single_page(self, client):
        """Test pagination with single page."""
        mock_response = {
            "dependencies": [{"id": "dep1", "name": "package1"}],
            "has_more": False
        }
        
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json=mock_response,
            status=200
        )
        
        dependencies = list(client.get_all_dependencies())
        
        assert len(dependencies) == 1
        assert dependencies[0]["id"] == "dep1"
    
    @responses.activate
    def test_pagination_multiple_pages(self, client):
        """Test pagination with multiple pages."""
        # First page
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={
                "dependencies": [{"id": "dep1", "name": "package1"}],
                "cursor": "cursor_2",
                "has_more": True
            },
            status=200
        )
        
        # Second page
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={
                "dependencies": [{"id": "dep2", "name": "package2"}],
                "has_more": False
            },
            status=200
        )
        
        dependencies = list(client.get_all_dependencies())
        
        assert len(dependencies) == 2
        assert dependencies[0]["id"] == "dep1"
        assert dependencies[1]["id"] == "dep2"
    
    @responses.activate
    def test_test_connection_success(self, client):
        """Test successful connection test."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"dependencies": [], "has_more": False},
            status=200
        )
        
        result = client.test_connection()
        assert result is True
    
    @responses.activate
    def test_test_connection_failure(self, client):
        """Test failed connection test."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"message": "Authentication failed"},
            status=401
        )
        
        result = client.test_connection()
        assert result is False
    
    def test_network_error(self, client):
        """Test network error handling."""
        with patch.object(client.session, 'post', side_effect=requests.exceptions.ConnectionError("Network error")):
            with pytest.raises(SemgrepAPIError) as exc_info:
                client.get_dependencies_page()
            
            assert "Network error" in str(exc_info.value)
    
    @responses.activate
    def test_invalid_json_response(self, client):
        """Test invalid JSON response handling."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            body="Invalid JSON",
            status=200
        )
        
        with pytest.raises(SemgrepAPIError) as exc_info:
            client.get_dependencies_page()
        
        assert "Invalid JSON response" in str(exc_info.value)
    
    @responses.activate
    def test_pagination_with_cursor(self, client):
        """Test pagination request includes cursor."""
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json={"dependencies": [], "has_more": False},
            status=200
        )
        
        client.get_dependencies_page(cursor="test_cursor", limit=500)
        
        # Verify the request was made with correct parameters
        request = responses.calls[0].request
        request_data = json.loads(request.body)
        
        assert request_data["cursor"] == "test_cursor"
        assert request_data["limit"] == 500
    
    # Tests for new per-repository functionality
    
    @responses.activate
    def test_get_repositories_list_success(self, client):
        """Test successful retrieval of repositories list."""
        mock_projects_response = {
            "projects": [
                {
                    "id": 12345,
                    "name": "test-repo-1",
                    "url": "https://github.com/org/repo1",
                    "default_branch": "main"
                },
                {
                    "id": 67890,
                    "name": "test-repo-2", 
                    "url": "https://github.com/org/repo2",
                    "default_branch": "master"
                }
            ]
        }
        
        responses.add(
            responses.GET,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_org/projects",
            json=mock_projects_response,
            status=200
        )
        
        repositories = client.get_repositories_list()
        
        assert len(repositories) == 2
        assert repositories[0]["name"] == "test-repo-1"
        assert repositories[1]["id"] == 67890
    
    @responses.activate
    def test_get_repositories_list_pagination(self, client):
        """Test successful retrieval of repositories list with pagination."""
        # First page response
        mock_projects_page1 = {
            "projects": [
                {"id": 1, "name": "repo-1"},
                {"id": 2, "name": "repo-2"}
            ]
        }
        
        # Second page response (smaller than page_size, indicating last page)
        mock_projects_page2 = {
            "projects": [
                {"id": 3, "name": "repo-3"}
            ]
        }
        
        responses.add(
            responses.GET,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_org/projects",
            json=mock_projects_page1,
            status=200
        )
        
        responses.add(
            responses.GET,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_org/projects",
            json=mock_projects_page2,
            status=200
        )
        
        repositories = client.get_repositories_list(page_size=2)
        
        assert len(repositories) == 3
        assert repositories[0]["name"] == "repo-1"
        assert repositories[1]["name"] == "repo-2"
        assert repositories[2]["name"] == "repo-3"
        
        # Verify pagination parameters were sent correctly
        assert len(responses.calls) == 2
        
        # First call should have page=0, page_size=2
        first_call_params = responses.calls[0].request.params
        assert first_call_params["page"] == "0"
        assert first_call_params["page_size"] == "2"
        
        # Second call should have page=1, page_size=2
        second_call_params = responses.calls[1].request.params
        assert second_call_params["page"] == "1"
        assert second_call_params["page_size"] == "2"
    
    @responses.activate
    def test_get_repositories_list_empty_page(self, client):
        """Test repositories list pagination stops when empty page received."""
        # First page has repositories
        mock_projects_page1 = {
            "projects": [
                {"id": 1, "name": "repo-1"},
                {"id": 2, "name": "repo-2"}
            ]
        }
        
        # Second page is empty
        mock_projects_page2 = {
            "projects": []
        }
        
        responses.add(
            responses.GET,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_org/projects",
            json=mock_projects_page1,
            status=200
        )
        
        responses.add(
            responses.GET,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_org/projects",
            json=mock_projects_page2,
            status=200
        )
        
        repositories = client.get_repositories_list(page_size=2)
        
        assert len(repositories) == 2
        assert len(responses.calls) == 2  # Should stop after empty page
    
    @responses.activate
    def test_get_dependencies_for_repository_success(self, client):
        """Test successful retrieval of dependencies for specific repository."""
        mock_dependencies_response = {
            "dependencies": [
                {
                    "repositoryId": "12345",
                    "package": {"name": "requests", "versionSpecifier": "2.28.1"},
                    "ecosystem": "pypi",
                    "transitivity": "DIRECT",
                    "licenses": ["MIT"]
                }
            ],
            "hasMore": False
        }
        
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json=mock_dependencies_response,
            status=200
        )
        
        result = client.get_dependencies_for_repository("12345")
        
        assert len(result["dependencies"]) == 1
        assert result["dependencies"][0]["package"]["name"] == "requests"
        
        # Verify the request payload includes repository filter
        request = responses.calls[0].request
        request_data = json.loads(request.body)
        assert "dependencyFilter" in request_data
        assert request_data["dependencyFilter"]["repositoryId"] == ["12345"]
    
    @responses.activate
    def test_get_dependencies_for_repository_with_pagination(self, client):
        """Test repository dependencies with pagination."""
        mock_dependencies_response = {
            "dependencies": [
                {
                    "repositoryId": "12345",
                    "package": {"name": "requests", "versionSpecifier": "2.28.1"},
                    "ecosystem": "pypi",
                    "transitivity": "DIRECT",
                    "licenses": ["MIT"]
                }
            ],
            "hasMore": False,
            "cursor": "next_page_cursor"
        }
        
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json=mock_dependencies_response,
            status=200
        )
        
        result = client.get_dependencies_for_repository("12345", cursor="current_cursor", limit=500)
        
        # Verify the request includes cursor and repository filter
        request = responses.calls[0].request
        request_data = json.loads(request.body)
        assert request_data["cursor"] == "current_cursor"
        assert request_data["limit"] == 500
        assert request_data["dependencyFilter"]["repositoryId"] == ["12345"]
    
    @responses.activate
    def test_get_all_dependencies_by_repository_success(self, client):
        """Test successful retrieval of all dependencies by repository."""
        # Mock projects response
        mock_projects_response = {
            "projects": [
                {"id": 12345, "name": "test-repo-1", "url": "https://github.com/org/repo1"},
                {"id": 67890, "name": "test-repo-2", "url": "https://github.com/org/repo2"}
            ]
        }
        
        responses.add(
            responses.GET,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_org/projects",
            json=mock_projects_response,
            status=200
        )
        
        # Mock dependencies responses for each repository
        mock_deps_repo1 = {
            "dependencies": [
                {
                    "repositoryId": "12345",
                    "package": {"name": "requests", "versionSpecifier": "2.28.1"},
                    "ecosystem": "pypi",
                    "transitivity": "DIRECT",
                    "licenses": ["MIT"]
                }
            ],
            "hasMore": False
        }
        
        mock_deps_repo2 = {
            "dependencies": [
                {
                    "repositoryId": "67890", 
                    "package": {"name": "numpy", "versionSpecifier": "1.21.0"},
                    "ecosystem": "pypi",
                    "transitivity": "DIRECT",
                    "licenses": ["BSD"]
                }
            ],
            "hasMore": False
        }
        
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json=mock_deps_repo1,
            status=200
        )
        
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies", 
            json=mock_deps_repo2,
            status=200
        )
        
        dependencies = list(client.get_all_dependencies_by_repository())
        
        assert len(dependencies) == 2
        
        # Verify enrichment with repository details
        assert "repository_details" in dependencies[0]
        assert dependencies[0]["repository_details"]["name"] == "test-repo-1"
        assert dependencies[1]["repository_details"]["name"] == "test-repo-2"
        
        # Verify API calls were made correctly
        assert len(responses.calls) == 3  # 1 projects call + 2 dependencies calls
    
    @responses.activate  
    def test_get_all_dependencies_by_repository_fallback_on_error(self, client):
        """Test fallback to deployment-wide fetch when repository listing fails."""
        # Mock failed projects response
        responses.add(
            responses.GET,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_org/projects",
            json={"error": "Not found"},
            status=404
        )
        
        # Mock successful deployment-wide dependencies response (fallback)
        mock_dependencies_response = {
            "dependencies": [
                {
                    "repositoryId": "12345",
                    "package": {"name": "requests", "versionSpecifier": "2.28.1"},
                    "ecosystem": "pypi",
                    "transitivity": "DIRECT", 
                    "licenses": ["MIT"]
                }
            ],
            "hasMore": False
        }
        
        responses.add(
            responses.POST,
            f"{SemgrepAPIClient.BASE_URL}/deployments/test_deployment_123/dependencies",
            json=mock_dependencies_response,
            status=200
        )
        
        dependencies = list(client.get_all_dependencies_by_repository())
        
        assert len(dependencies) == 1
        assert dependencies[0]["package"]["name"] == "requests"
        # Should not have repository_details since it fell back to deployment-wide fetch
        assert "repository_details" not in dependencies[0]