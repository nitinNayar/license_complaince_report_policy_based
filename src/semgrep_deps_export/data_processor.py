"""
Data processing and transformation for Semgrep dependencies.

Handles data validation, transformation, and formatting for Excel export.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


logger = logging.getLogger(__name__)


@dataclass
class ProcessedDependency:
    """Processed dependency data for Excel export."""
    
    id: str
    repository_id: str
    repository_name: str
    name: str
    version: str
    ecosystem: str
    package_manager: str
    transitivity: str
    licenses: str
    bad_license: bool
    review_license: bool
    vulnerability_count: int
    critical_vulns: int
    high_vulns: int
    medium_vulns: int
    low_vulns: int
    first_seen: str
    last_seen: str
    projects: str


@dataclass
class ProcessedVulnerability:
    """Processed vulnerability data for Excel export."""
    
    dependency_name: str
    dependency_version: str
    vulnerability_id: str
    severity: str
    description: str


class DataProcessor:
    """Processes raw API data for Excel export."""
    
    SEVERITY_LEVELS = ["critical", "high", "medium", "low", "info"]
    
    # Mapping from ecosystem to package manager
    ECOSYSTEM_TO_PACKAGE_MANAGER = {
        "npm": "npm",
        "pypi": "pip", 
        "maven": "maven",
        "gradle": "gradle",
        "cargo": "cargo",
        "go": "go",
        "nuget": "nuget",
        "composer": "composer",
        "gem": "gem",
        "cocoapods": "cocoapods",
        "swift": "swift",
        "pub": "pub"
    }
    
    def __init__(self, bad_license_types: Optional[List[str]] = None, 
                 review_license_types: Optional[List[str]] = None,
                 repository_mapping: Optional[Dict[str, str]] = None):
        self.bad_license_types = [license.lower() for license in bad_license_types] if bad_license_types else []
        self.review_license_types = [license.lower() for license in review_license_types] if review_license_types else []
        self.repository_mapping = repository_mapping or {}
        self.processed_dependencies: List[ProcessedDependency] = []
        self.processed_vulnerabilities: List[ProcessedVulnerability] = []
        self.processing_stats = {
            "total_processed": 0,
            "validation_errors": 0,
            "transformation_errors": 0
        }
    
    def reset_state(self) -> None:
        """Reset processor state to prevent data accumulation across multiple calls."""
        self.processed_dependencies = []
        self.processed_vulnerabilities = []
        self.processing_stats = {
            "total_processed": 0,
            "validation_errors": 0,
            "transformation_errors": 0
        }
    
    def _get_repository_name(self, repository_id: str) -> str:
        """Get repository name from ID, with fallback."""
        if not repository_id:
            return "Unknown Repository"
            
        # Try to get name from mapping
        repo_name = self.repository_mapping.get(repository_id)
        if repo_name:
            return repo_name
            
        # Fallback to showing ID with prefix
        return f"Repo-{repository_id}"
    
    def _get_repository_name_enhanced(self, raw_dependency: Dict[str, Any], repository_id: str) -> str:
        """Get repository name with enhanced support for per-repository mode data."""
        # First check if there are enhanced repository details (from per-repository mode)
        repository_details = raw_dependency.get("repository_details")
        if repository_details:
            repo_name = repository_details.get("name")
            if repo_name:
                logger.debug(f"Using enhanced repository name: {repo_name}")
                return repo_name
        
        # Fall back to standard repository mapping
        return self._get_repository_name(repository_id)
    
    def process_dependency(self, raw_dependency: Dict[str, Any]) -> Optional[ProcessedDependency]:
        """Process a single dependency from raw API data."""
        try:
            # Extract basic fields using actual API structure
            dep_id = self._get_field(raw_dependency, "repositoryId", "")
            repository_id = self._get_field(raw_dependency, "repositoryId", "Unknown")
            name = self._get_field(raw_dependency, "package.name", "Unknown")
            version = self._get_field(raw_dependency, "package.versionSpecifier", "Unknown")
            ecosystem = self._get_field(raw_dependency, "ecosystem", "Unknown")
            transitivity = self._get_field(raw_dependency, "transitivity", "Unknown")
            
            # Map ecosystem to package manager
            package_manager = self.ECOSYSTEM_TO_PACKAGE_MANAGER.get(ecosystem.lower(), ecosystem)
            
            # Process licenses
            licenses_list = self._get_field(raw_dependency, "licenses", [])
            licenses = ", ".join(licenses_list) if licenses_list else "Unknown"
            bad_license = self._check_bad_license(licenses_list)
            review_license = self._check_review_license(licenses_list)
            
            # Process vulnerabilities (may not exist in API response)
            vulnerabilities = self._get_field(raw_dependency, "vulnerabilities", [])
            vuln_counts = self._count_vulnerabilities_by_severity(vulnerabilities)
            
            # Process timestamps (may not exist in API response)
            first_seen = self._format_timestamp(self._get_field(raw_dependency, "first_seen"))
            last_seen = self._format_timestamp(self._get_field(raw_dependency, "last_seen"))
            
            # Process projects (may not exist in API response)
            projects_list = self._get_field(raw_dependency, "projects", [])
            projects = ", ".join(projects_list) if projects_list else "No project data"
            
            # Get repository name from mapping or enhanced repository details
            repository_name = self._get_repository_name_enhanced(raw_dependency, repository_id)
            
            processed = ProcessedDependency(
                id=dep_id,
                repository_id=repository_id,
                repository_name=repository_name,
                name=name,
                version=version,
                ecosystem=ecosystem,
                package_manager=package_manager,
                transitivity=transitivity,
                licenses=licenses,
                bad_license=bad_license,
                review_license=review_license,
                vulnerability_count=len(vulnerabilities),
                critical_vulns=vuln_counts["critical"],
                high_vulns=vuln_counts["high"],
                medium_vulns=vuln_counts["medium"],
                low_vulns=vuln_counts["low"],
                first_seen=first_seen,
                last_seen=last_seen,
                projects=projects
            )
            
            # Log first few dependencies for verification
            if self.processing_stats["total_processed"] < 3:
                logger.info(f"Sample dependency {self.processing_stats['total_processed'] + 1}: {name} v{version} ({ecosystem}) - {transitivity} - Repo ID: {repository_id}")
            
            # Process individual vulnerabilities for the vulnerabilities sheet
            self._process_vulnerabilities(name, version, vulnerabilities)
            
            self.processing_stats["total_processed"] += 1
            return processed
            
        except Exception as e:
            logger.error(f"Error processing dependency {raw_dependency.get('name', 'unknown')}: {str(e)}")
            self.processing_stats["transformation_errors"] += 1
            return None
    
    def _get_field(self, data: Dict[str, Any], field: str, default: Any = None) -> Any:
        """Safely get a field from a dictionary with default value.
        
        Supports nested field access using dot notation (e.g., 'package.name').
        """
        try:
            # Handle nested field access
            if '.' in field:
                keys = field.split('.')
                current = data
                for key in keys:
                    if isinstance(current, dict) and key in current:
                        current = current[key]
                    else:
                        return default
                return current if current is not None else default
            else:
                # Simple field access
                value = data.get(field, default)
                return value if value is not None else default
        except (AttributeError, KeyError, TypeError):
            return default
    
    def _check_bad_license(self, licenses_list: List[str]) -> bool:
        """Check if any license in the list is considered bad."""
        if not self.bad_license_types or not licenses_list:
            return False
        
        # Convert licenses to lowercase for case-insensitive comparison
        normalized_licenses = [license.lower().strip() for license in licenses_list]
        
        # Check if any license matches bad license list
        return any(license in self.bad_license_types for license in normalized_licenses)
    
    def _check_review_license(self, licenses_list: List[str]) -> bool:
        """Check if any license in the list requires review."""
        if not self.review_license_types or not licenses_list:
            return False
        
        # Convert licenses to lowercase for case-insensitive comparison
        normalized_licenses = [license.lower().strip() for license in licenses_list]
        
        # Check if any license matches review license list
        return any(license in self.review_license_types for license in normalized_licenses)
    
    def _count_vulnerabilities_by_severity(self, vulnerabilities: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count vulnerabilities by severity level."""
        counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for vuln in vulnerabilities:
            severity = self._get_field(vuln, "severity", "").lower()
            if severity in counts:
                counts[severity] += 1
            else:
                # Handle any other severity values as 'info'
                counts["info"] += 1
        
        return counts
    
    def _format_timestamp(self, timestamp: Optional[str]) -> str:
        """Format timestamp to human-readable format."""
        if not timestamp:
            return "Unknown"
        
        try:
            # Try to parse common ISO formats
            if timestamp.endswith('Z'):
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            else:
                dt = datetime.fromisoformat(timestamp)
            
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
            
        except (ValueError, AttributeError) as e:
            logger.warning(f"Could not parse timestamp '{timestamp}': {str(e)}")
            return str(timestamp) if timestamp else "Unknown"
    
    def _process_vulnerabilities(self, dep_name: str, dep_version: str, vulnerabilities: List[Dict[str, Any]]) -> None:
        """Process vulnerabilities for the vulnerabilities sheet."""
        for vuln in vulnerabilities:
            try:
                processed_vuln = ProcessedVulnerability(
                    dependency_name=dep_name,
                    dependency_version=dep_version,
                    vulnerability_id=self._get_field(vuln, "id", "Unknown"),
                    severity=self._get_field(vuln, "severity", "Unknown").title(),
                    description=self._get_field(vuln, "description", "No description available")
                )
                
                self.processed_vulnerabilities.append(processed_vuln)
                
            except Exception as e:
                logger.error(f"Error processing vulnerability for {dep_name}:{dep_version}: {str(e)}")
    
    def process_all_dependencies(self, dependencies_iterator) -> Tuple[List[ProcessedDependency], List[ProcessedVulnerability]]:
        """Process all dependencies from an iterator."""
        logger.info("Starting data processing...")
        
        for raw_dependency in dependencies_iterator:
            processed = self.process_dependency(raw_dependency)
            if processed:
                self.processed_dependencies.append(processed)
        
        logger.info(f"Data processing completed:")
        logger.info(f"  - Total dependencies processed: {self.processing_stats['total_processed']}")
        logger.info(f"  - Validation errors: {self.processing_stats['validation_errors']}")
        logger.info(f"  - Transformation errors: {self.processing_stats['transformation_errors']}")
        logger.info(f"  - Total vulnerabilities found: {len(self.processed_vulnerabilities)}")
        
        return self.processed_dependencies, self.processed_vulnerabilities
    
    def get_processing_summary(self) -> Dict[str, Any]:
        """Get a summary of processing statistics."""
        vuln_severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        
        for vuln in self.processed_vulnerabilities:
            severity = vuln.severity.lower()
            if severity in vuln_severity_counts:
                vuln_severity_counts[severity] += 1
        
        # Calculate bad license statistics
        bad_license_count = sum(1 for dep in self.processed_dependencies if dep.bad_license)
        
        # Calculate review license statistics
        review_license_count = sum(1 for dep in self.processed_dependencies if dep.review_license)
        
        return {
            "dependencies": {
                "total": len(self.processed_dependencies),
                "with_vulnerabilities": sum(1 for dep in self.processed_dependencies if dep.vulnerability_count > 0),
                "without_vulnerabilities": sum(1 for dep in self.processed_dependencies if dep.vulnerability_count == 0),
                "with_bad_licenses": bad_license_count,
                "without_bad_licenses": len(self.processed_dependencies) - bad_license_count,
                "with_review_licenses": review_license_count,
                "without_review_licenses": len(self.processed_dependencies) - review_license_count
            },
            "vulnerabilities": {
                "total": len(self.processed_vulnerabilities),
                **vuln_severity_counts
            },
            "processing": self.processing_stats
        }