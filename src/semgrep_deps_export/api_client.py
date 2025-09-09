"""
Semgrep API client for retrieving dependency data.

Handles authentication, API calls, pagination, and error handling.
"""

import json
import logging
import time
from typing import Dict, Any, Optional, Iterator, List
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
        
        # Check if this is an ecosystem filtering request for enhanced logging
        is_ecosystem_request = (
            "dependencyFilter" in data and 
            "ecosystem" in data.get("dependencyFilter", {})
        )
        
        if is_ecosystem_request:
            ecosystem = data["dependencyFilter"]["ecosystem"]
            logger.info(f"ECOSYSTEM API DEBUG: Making POST request to {url}")
            logger.info(f"ECOSYSTEM API DEBUG: Request headers: {dict(self.session.headers)}")
            logger.info(f"ECOSYSTEM API DEBUG: Full request payload: {json.dumps(data, indent=2)}")
        else:
            logger.debug(f"Making request to {url} with data: {json.dumps(data, indent=2)}")
        
        try:
            response = self.session.post(
                url,
                json=data,
                timeout=self.config.timeout
            )
            
            if is_ecosystem_request:
                logger.info(f"ECOSYSTEM API DEBUG: Response status: {response.status_code}")
                logger.info(f"ECOSYSTEM API DEBUG: Response headers: {dict(response.headers)}")
                logger.info(f"ECOSYSTEM API DEBUG: Raw response text: {response.text[:1000]}...")  # First 1000 chars
            
            if not response.ok:
                if is_ecosystem_request:
                    logger.error(f"ECOSYSTEM API DEBUG: Error response status: {response.status_code}")
                    logger.error(f"ECOSYSTEM API DEBUG: Error response text: {response.text}")
                self._handle_api_error(response)
            
            response_json = response.json()
            
            if is_ecosystem_request:
                logger.info(f"ECOSYSTEM API DEBUG: Parsed response keys: {list(response_json.keys())}")
                if "dependencies" in response_json:
                    logger.info(f"ECOSYSTEM API DEBUG: Dependencies array length: {len(response_json['dependencies'])}")
                if "error" in response_json:
                    logger.error(f"ECOSYSTEM API DEBUG: Error in response: {response_json['error']}")
            
            return response_json
            
        except requests.exceptions.RequestException as e:
            if is_ecosystem_request:
                logger.error(f"ECOSYSTEM API DEBUG: Network error: {str(e)}")
            logger.error(f"Network error: {str(e)}")
            raise SemgrepAPIError(f"Network error: {str(e)}")
        except json.JSONDecodeError as e:
            if is_ecosystem_request:
                logger.error(f"ECOSYSTEM API DEBUG: JSON decode error: {str(e)}")
                logger.error(f"ECOSYSTEM API DEBUG: Raw response that failed to decode: {response.text}")
            logger.error(f"Invalid JSON response: {str(e)}")
            raise SemgrepAPIError(f"Invalid JSON response: {str(e)}")
    
    def get_dependencies_page(self, cursor: Optional[str] = None, limit: int = 10000) -> Dict[str, Any]:
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
                response_data = self.get_dependencies_page(cursor=cursor, limit=10000)
                
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
    
    def get_projects(self, page: int = 0, page_size: int = 100) -> Dict[str, Any]:
        """Get projects/repositories for the deployment with pagination support.
        
        Args:
            page: Page number (0-based). Default: 0
            page_size: Maximum number of records per page. Default: 100
            
        Returns:
            Dictionary containing projects data and pagination info
        """
        if not self.config.deployment_slug:
            raise SemgrepAPIError("deployment_slug is required for fetching repository information")
            
        endpoint = f"/deployments/{self.config.deployment_slug}/projects"
        
        logger.info(f"Fetching projects for deployment slug: {self.config.deployment_slug} (page={page}, page_size={page_size})")
        
        try:
            params = {
                "page": page,
                "page_size": page_size
            }
            response = self.session.get(f"{self.BASE_URL}{endpoint}", params=params)
            
            if response.status_code == 200:
                response_data = response.json()
                projects = response_data.get("projects", [])
                logger.info(f"Retrieved {len(projects)} projects (page {page})")
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
            projects = self.get_repositories_list()
            
            repo_mapping = {}
            
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
    
    def get_repositories_list(self, page_size: int = 100) -> List[Dict[str, Any]]:
        """Get complete list of repositories for the deployment using pagination.
        
        Args:
            page_size: Maximum number of records per page. Default: 100
            
        Returns:
            Complete list of all repositories across all pages
        """
        try:
            all_repositories = []
            page = 0
            total_fetched = 0
            
            logger.info(f"Starting paginated fetch of repositories (page_size={page_size})")
            
            while True:
                logger.info(f"Fetching repositories page {page}...")
                
                projects_response = self.get_projects(page=page, page_size=page_size)
                repositories = projects_response.get("projects", [])
                
                if not repositories:
                    logger.info(f"No more repositories found on page {page}")
                    break
                    
                all_repositories.extend(repositories)
                total_fetched += len(repositories)
                
                logger.info(f"Page {page}: {len(repositories)} repositories (total: {total_fetched})")
                
                # If we received fewer repositories than the page size, we've reached the end
                if len(repositories) < page_size:
                    logger.info(f"Received {len(repositories)} < {page_size}, assuming last page")
                    break
                    
                page += 1
            
            logger.info(f"Retrieved {len(all_repositories)} total repositories across {page + 1} pages")
            return all_repositories
            
        except SemgrepAPIError as e:
            logger.error(f"Failed to fetch repositories list: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching repositories list: {e}")
            raise SemgrepAPIError(f"Unexpected error: {str(e)}")
    
    def get_dependencies_for_repository(self, repo_id: str, cursor: Optional[str] = None, limit: int = 10000) -> Dict[str, Any]:
        """Get dependencies for a specific repository."""
        endpoint = f"/deployments/{self.config.deployment_id}/dependencies"
        
        data = {
            "limit": limit,
            "dependencyFilter": {
                "repositoryId": [int(repo_id)]
            }
        }
        if cursor:
            data["cursor"] = cursor
        
        logger.debug(f"Fetching dependencies for repository {repo_id} (cursor: {cursor or 'None'}, limit: {limit})")
        
        response_data = self._make_request(endpoint, data)
        
        dependencies = response_data.get("dependencies", [])
        logger.debug(f"Retrieved {len(dependencies)} dependencies for repository {repo_id}")
        
        return response_data
    
    def get_dependencies_by_policy_filter(self, policy_setting: str, cursor: Optional[str] = None, limit: int = 10000) -> Dict[str, Any]:
        """Get dependencies filtered by license policy setting."""
        endpoint = f"/deployments/{self.config.deployment_id}/dependencies"
        
        data = {
            "pageSize": limit,
            "dependencyFilter": {
                "licensePolicySetting": policy_setting
            }
        }
        if cursor:
            data["cursor"] = cursor
        
        logger.debug(f"Fetching dependencies for policy setting {policy_setting} (cursor: {cursor or 'None'}, limit: {limit})")
        
        response_data = self._make_request(endpoint, data)
        
        dependencies = response_data.get("dependencies", [])
        logger.debug(f"Retrieved {len(dependencies)} dependencies for policy setting {policy_setting}")
        
        return response_data
    
    def get_all_dependencies_by_policy(self, policy_setting: str) -> Iterator[Dict[str, Any]]:
        """Get all dependencies for a specific license policy setting using pagination."""
        cursor = None
        page_count = 0
        total_dependencies = 0
        
        logger.info(f"Starting to fetch all dependencies for policy setting {policy_setting}")
        
        while True:
            page_count += 1
            logger.info(f"Fetching page {page_count} for policy {policy_setting}...")
            
            try:
                response_data = self.get_dependencies_by_policy_filter(policy_setting, cursor=cursor, limit=10000)
                
                dependencies = response_data.get("dependencies", [])
                page_count_deps = len(dependencies)
                total_dependencies += page_count_deps
                
                logger.info(f"Page {page_count}: {page_count_deps} dependencies (total: {total_dependencies})")
                
                # Yield each dependency
                for dependency in dependencies:
                    yield dependency
                
                # Check if there are more pages
                has_more = response_data.get("hasMore", response_data.get("has_more", False))
                if not has_more:
                    logger.info(f"Completed fetching all dependencies for policy {policy_setting}. Total: {total_dependencies} across {page_count} pages")
                    break
                
                # Get cursor for next page
                cursor = response_data.get("cursor")
                if not cursor:
                    logger.warning(f"has_more=true but no cursor provided for policy {policy_setting}, stopping pagination")
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
                logger.error(f"Unexpected error on page {page_count} for policy {policy_setting}: {str(e)}")
                raise SemgrepAPIError(f"Unexpected error: {str(e)}")
    
    def get_dependencies_by_ecosystem_filter(self, ecosystem: str, cursor: Optional[str] = None, limit: int = 10000) -> Dict[str, Any]:
        """Get dependencies filtered by ecosystem."""
        endpoint = f"/deployments/{self.config.deployment_id}/dependencies"
        
        data = {
            "pageSize": limit,
            "dependencyFilter": {
                "ecosystem": [ecosystem]
            }
        }
        if cursor:
            data["cursor"] = cursor
        
        # Enhanced logging for ecosystem filtering debugging
        logger.info(f"ECOSYSTEM FILTER DEBUG: Attempting to fetch dependencies for ecosystem '{ecosystem}'")
        logger.info(f"ECOSYSTEM FILTER DEBUG: Full request data: {data}")
        logger.info(f"ECOSYSTEM FILTER DEBUG: Endpoint: {endpoint}")
        
        try:
            response_data = self._make_request(endpoint, data)
            logger.info(f"ECOSYSTEM FILTER DEBUG: Request successful for ecosystem '{ecosystem}'")
            logger.info(f"ECOSYSTEM FILTER DEBUG: Response keys: {list(response_data.keys())}")
            logger.info(f"ECOSYSTEM FILTER DEBUG: Dependencies count: {len(response_data.get('dependencies', []))}")
        except SemgrepAPIError as e:
            logger.error(f"ECOSYSTEM FILTER DEBUG: API Error for ecosystem '{ecosystem}'")
            logger.error(f"ECOSYSTEM FILTER DEBUG: Status code: {e.status_code}")
            logger.error(f"ECOSYSTEM FILTER DEBUG: Error message: {str(e)}")
            logger.error(f"ECOSYSTEM FILTER DEBUG: Request data was: {data}")
            
            if e.status_code == 400:
                logger.warning(f"Ecosystem filtering appears to be unsupported by the Semgrep API for ecosystem '{ecosystem}'. "
                             f"This may be because the 'ecosystem' filter parameter is not available in the current API version.")
                logger.info(f"Consider using alternative approaches or contact Semgrep support for ecosystem filtering capabilities.")
                # Return empty result to gracefully handle unsupported filtering
                return {"dependencies": [], "hasMore": False, "cursor": None}
            else:
                raise
        
        dependencies = response_data.get("dependencies", [])
        logger.debug(f"Retrieved {len(dependencies)} dependencies for ecosystem {ecosystem}")
        
        return response_data
    
    def get_all_dependencies_by_ecosystem(self, ecosystem: str) -> Iterator[Dict[str, Any]]:
        """Get all dependencies for a specific ecosystem using pagination."""
        cursor = None
        page_count = 0
        total_dependencies = 0
        
        logger.info(f"Starting to fetch all dependencies for ecosystem {ecosystem}")
        
        while True:
            page_count += 1
            logger.info(f"Fetching page {page_count} for ecosystem {ecosystem}...")
            
            try:
                response_data = self.get_dependencies_by_ecosystem_filter(ecosystem, cursor=cursor, limit=10000)
                
                dependencies = response_data.get("dependencies", [])
                page_count_deps = len(dependencies)
                total_dependencies += page_count_deps
                
                logger.info(f"Page {page_count}: {page_count_deps} dependencies (total: {total_dependencies})")
                
                # Yield each dependency
                for dependency in dependencies:
                    yield dependency
                
                # Check if there are more pages
                has_more = response_data.get("hasMore", response_data.get("has_more", False))
                if not has_more:
                    logger.info(f"Completed fetching all dependencies for ecosystem {ecosystem}. Total: {total_dependencies} across {page_count} pages")
                    break
                
                # Get cursor for next page
                cursor = response_data.get("cursor")
                if not cursor:
                    logger.warning(f"has_more=true but no cursor provided for ecosystem {ecosystem}, stopping pagination")
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
                logger.error(f"Unexpected error on page {page_count} for ecosystem {ecosystem}: {str(e)}")
                raise SemgrepAPIError(f"Unexpected error: {str(e)}")
    
    def get_all_dependencies_by_repository(self) -> Iterator[Dict[str, Any]]:
        """Get all dependencies by iterating over repositories."""
        logger.info("Starting per-repository dependency fetching mode")
        
        # Step 1: Get list of repositories
        try:
            repositories = self.get_repositories_list()
        except Exception as e:
            logger.error(f"Failed to fetch repositories list, falling back to deployment-wide fetch: {e}")
            logger.info("Falling back to deployment-wide dependency fetch")
            yield from self.get_all_dependencies()
            return
        
        if not repositories:
            logger.warning("No repositories found, falling back to deployment-wide fetch")
            yield from self.get_all_dependencies()
            return
        
        # Create repository mapping for enrichment
        repo_mapping = {}
        for repo in repositories:
            repo_id = str(repo.get("id"))
            repo_mapping[repo_id] = {
                "name": repo.get("name", f"Unknown-{repo_id}"),
                "url": repo.get("url", ""),
                "default_branch": repo.get("default_branch", ""),
                "primary_branch": repo.get("primary_branch", "")
            }
        
        total_dependencies = 0
        processed_repos = 0
        failed_repos = 0
        
        # Step 2: Iterate over repositories and fetch dependencies
        for repo in repositories:
            repo_id = str(repo.get("id"))
            repo_name = repo.get("name", f"Unknown-{repo_id}")
            processed_repos += 1
            
            logger.info(f"Processing repository {processed_repos}/{len(repositories)}: {repo_name} (ID: {repo_id})")
            
            try:
                cursor = None
                repo_dep_count = 0
                
                while True:
                    try:
                        response_data = self.get_dependencies_for_repository(repo_id, cursor)
                        dependencies = response_data.get("dependencies", [])
                        
                        # Enrich each dependency with repository details
                        for dependency in dependencies:
                            # Add repository information to the dependency
                            dependency["repository_details"] = repo_mapping.get(repo_id, {
                                "name": repo_name,
                                "url": "",
                                "default_branch": "",
                                "primary_branch": ""
                            })
                            
                            yield dependency
                            repo_dep_count += 1
                            total_dependencies += 1
                        
                        # Check pagination
                        has_more = response_data.get("hasMore", response_data.get("has_more", False))
                        if not has_more:
                            break
                        
                        cursor = response_data.get("cursor")
                        if not cursor:
                            logger.warning(f"has_more=true but no cursor for repository {repo_name}, stopping pagination")
                            break
                            
                    except SemgrepAPIError as e:
                        if e.status_code == 429:  # Rate limited
                            wait_time = 2 ** (processed_repos - 1) if processed_repos <= 5 else 32
                            logger.warning(f"Rate limited on repository {repo_name}, waiting {wait_time} seconds...")
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.error(f"API error fetching dependencies for repository {repo_name}: {e}")
                            failed_repos += 1
                            break
                    except Exception as e:
                        logger.error(f"Unexpected error fetching dependencies for repository {repo_name}: {e}")
                        failed_repos += 1
                        break
                
                logger.info(f"✓ Repository {repo_name}: {repo_dep_count} dependencies")
                
            except Exception as e:
                logger.error(f"Failed to process repository {repo_name}: {e}")
                failed_repos += 1
                continue
        
        # Final summary
        logger.info(f"Per-repository fetch completed:")
        logger.info(f"  Repositories processed: {processed_repos}/{len(repositories)}")
        logger.info(f"  Repositories failed: {failed_repos}")
        logger.info(f"  Total dependencies: {total_dependencies}")
        
        if failed_repos > 0:
            logger.warning(f"{failed_repos} repositories failed to process. Check logs for details.")
    
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