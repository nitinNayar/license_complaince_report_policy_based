"""
Semgrep API client for retrieving dependency data.

Handles authentication, API calls, pagination, and error handling.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Iterator
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .config import Config


logger = logging.getLogger(__name__)


class SemgrepAPIError(Exception):
    """Custom exception for Semgrep API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class SemgrepAPIClient:
    """Client for interacting with the Semgrep Supply Chain API."""
    
    BASE_URL = "https://semgrep.dev/api/v1"
    
    def __init__(self, config: Config):
        """Initialize the API client with configuration."""
        self.config = config
        self.session = self._create_session()
        self._masked_token = self._mask_token(config.token)
    
    def _create_session(self) -> requests.Session:
        """Create a configured requests session."""
        session = requests.Session()
        
        # Set headers
        session.headers.update({
            "Authorization": f"Bearer {self.config.token}",
            "Content-Type": "application/json",
            "User-Agent": "semgrep-deps-export/1.0.0"
        })
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.config.max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _mask_token(self, token: str) -> str:
        """Mask the token for logging purposes."""
        if len(token) <= 8:
            return "*" * len(token)
        return f"{token[:4]}{'*' * (len(token) - 8)}{token[-4:]}"
    
    def _handle_api_error(self, response: requests.Response) -> None:
        """Handle API error responses."""
        status_code = response.status_code
        
        try:
            error_data = response.json()
            error_message = error_data.get("message", "Unknown error")
        except (json.JSONDecodeError, AttributeError):
            error_message = response.text or f"HTTP {status_code} error"
        
        if status_code == 401:
            raise SemgrepAPIError(
                f"Authentication failed. Please check your token ({self._masked_token})",
                status_code
            )
        elif status_code == 403:
            raise SemgrepAPIError(
                "Access forbidden. Token may not have required permissions for Supply Chain API",
                status_code
            )
        elif status_code == 404:
            raise SemgrepAPIError(
                f"Deployment not found: {self.config.deployment_id}",
                status_code
            )
        elif status_code == 429:
            raise SemgrepAPIError(
                "Rate limit exceeded. Please try again later",
                status_code
            )
        elif 500 <= status_code < 600:
            raise SemgrepAPIError(
                f"Server error ({status_code}): {error_message}",
                status_code
            )
        else:
            raise SemgrepAPIError(
                f"API request failed ({status_code}): {error_message}",
                status_code
            )
    
    def _make_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the API with error handling."""
        url = f"{self.BASE_URL}{endpoint}"
        
        logger.debug(f"Making request to {url} with data: {json.dumps(data, indent=2)}")
        
        try:
            response = self.session.post(
                url,
                json=data,
                timeout=self.config.timeout
            )
            
            if not response.ok:
                self._handle_api_error(response)
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {str(e)}")
            raise SemgrepAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {str(e)}")
            raise SemgrepAPIError(f"Invalid JSON response: {str(e)}")
    
    def get_dependencies_page(self, cursor: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
        """Get a single page of dependencies."""
        endpoint = f"/deployments/{self.config.deployment_id}/dependencies"
        
        data = {"limit": limit}
        if cursor:
            data["cursor"] = cursor
        
        logger.info(f"Fetching dependencies page (cursor: {cursor or 'None'}, limit: {limit})")
        
        response_data = self._make_request(endpoint, data)
        
        dependencies = response_data.get("dependencies", [])
        logger.info(f"Retrieved {len(dependencies)} dependencies")
        
        # Debug: Log pagination fields from response (can be removed in production)
        logger.debug(f"Pagination - hasMore: {response_data.get('hasMore')}, cursor: {response_data.get('cursor')}")
        
        return response_data
    
    def get_all_dependencies(self) -> Iterator[Dict[str, Any]]:
        """Get all dependencies using pagination."""
        cursor = None
        page_count = 0
        total_dependencies = 0
        
        logger.info(f"Starting to fetch all dependencies for deployment {self.config.deployment_id}")
        
        while True:
            page_count += 1
            logger.info(f"Fetching page {page_count}...")
            
            try:
                response_data = self.get_dependencies_page(cursor)
                
                dependencies = response_data.get("dependencies", [])
                page_count_deps = len(dependencies)
                total_dependencies += page_count_deps
                
                logger.info(f"Page {page_count}: {page_count_deps} dependencies (total: {total_dependencies})")
                
                # Yield each dependency
                for dependency in dependencies:
                    yield dependency
                
                # Check if there are more pages (handle both hasMore and has_more field names)
                has_more = response_data.get("hasMore", response_data.get("has_more", False))
                if not has_more:
                    logger.info(f"Completed fetching all dependencies. Total: {total_dependencies} across {page_count} pages")
                    break
                
                # Get cursor for next page
                cursor = response_data.get("cursor")
                if not cursor:
                    logger.warning("has_more=true but no cursor provided, stopping pagination")
                    break
                    
            except SemgrepAPIError as e:
                if e.status_code == 429:  # Rate limited
                    wait_time = 2 ** (page_count - 1)  # Exponential backoff
                    logger.warning(f"Rate limited, waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                else:
                    raise
            except Exception as e:
                logger.error(f"Unexpected error on page {page_count}: {str(e)}")
                raise SemgrepAPIError(f"Unexpected error: {str(e)}")
    
    def get_projects(self) -> Dict[str, Any]:
        """Get all projects/repositories for the deployment."""
        endpoint = f"/deployments/{self.config.deployment_slug}/projects"
        
        logger.info(f"Fetching projects for deployment slug: {self.config.deployment_slug}")
        
        try:
            response = self.session.get(f"{self.BASE_URL}{endpoint}")
            
            if response.status_code == 200:
                response_data = response.json()
                projects = response_data.get("projects", [])
                logger.info(f"Retrieved {len(projects)} projects")
                return response_data
            else:
                error_message = f"Failed to fetch projects: HTTP {response.status_code}"
                try:
                    error_detail = response.json().get("message", response.text)
                    error_message = f"Failed to fetch projects: {error_detail}"
                except:
                    pass
                raise SemgrepAPIError(error_message, response.status_code)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching projects: {str(e)}")
            raise SemgrepAPIError(f"Network error: {str(e)}")
    
    def get_repository_mapping(self) -> Dict[str, str]:
        """Get a mapping of repository_id -> repository_name."""
        try:
            logger.info("Building repository mapping...")
            projects_response = self.get_projects()
            
            repo_mapping = {}
            projects = projects_response.get("projects", [])
            
            for project in projects:
                repo_id = str(project.get("id"))  # Convert to string for consistency
                repo_name = project.get("name", f"Unknown-{repo_id}")
                repo_mapping[repo_id] = repo_name
                
            logger.info(f"Built repository mapping for {len(repo_mapping)} repositories")
            return repo_mapping
            
        except SemgrepAPIError as e:
            logger.warning(f"Failed to fetch repository information: {e}")
            return {}
        except Exception as e:
            logger.warning(f"Unexpected error fetching repositories: {e}")
            return {}
    
    def test_connection(self) -> bool:
        """Test the API connection and authentication."""
        try:
            logger.info(f"Testing connection with token {self._masked_token}")
            self.get_dependencies_page(limit=1)
            logger.info("Connection test successful")
            return True
        except SemgrepAPIError as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False