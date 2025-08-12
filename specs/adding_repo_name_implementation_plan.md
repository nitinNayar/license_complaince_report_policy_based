# Repository Name Implementation Plan

## Overview
This document provides a detailed technical implementation plan for adding repository names to the Semgrep Dependencies Export Tool. Currently, the tool displays repository IDs which are not user-friendly. This enhancement will fetch repository names via the Semgrep Projects API and display them in both the data model and Excel export.

## Current System Analysis

### Current Data Flow
1. **Configuration**: Load deployment_id from CLI/env variables
2. **API Call**: Fetch dependencies from `/deployments/{deployment_id}/dependencies`
3. **Processing**: Transform raw dependency data to ProcessedDependency objects
4. **Export**: Generate Excel with 8 columns including "Repository ID"

### Current Data Structure
```python
@dataclass
class ProcessedDependency:
    repository_id: str  # Currently shows numeric ID (e.g., "1554601")
    name: str
    version: str
    ecosystem: str
    package_manager: str
    transitivity: str
    licenses: str
    bad_license: bool
```

### Current Excel Structure
| Column 1 | Column 2 | Column 3 | Column 4 | Column 5 | Column 6 | Column 7 | Column 8 |
|----------|----------|----------|----------|----------|----------|----------|----------|
| Repository ID | Name | Version | Ecosystem | Package Manager | Transitivity | Bad_License | Licenses |

## Requirements Analysis

### New API Integration
- **Endpoint**: `https://semgrep.dev/api/v1/deployments/{deployment_slug}/projects`
- **Authentication**: Same Bearer token as dependencies API
- **Response Format**:
```json
{
  "projects": [
    {
      "id": 1234567,
      "name": "returntocorp/semgrep",
      "url": "https://github.com/returntocorp/semgrep",
      "created_at": "2020-11-18 23:28:12.391807",
      "default_branch": "refs/heads/main",
      "primary_branch": "refs/heads/custom-main",
      "latest_scan_at": "2023-01-13T20:51:51.449081Z",
      "tags": ["tag"]
    }
  ]
}
```

### Key Requirements
1. **New Configuration Parameter**: deployment_slug (different from deployment_id)
2. **Repository Mapping**: Create id→name lookup table
3. **Enhanced Data Model**: Add repository_name field
4. **Improved UX**: Show repository names instead of/alongside IDs
5. **Error Handling**: Graceful fallback when repository names unavailable

## Technical Implementation Plan

### Phase 1: Configuration Enhancement

#### 1.1 Config Dataclass Updates
**File**: `src/semgrep_deps_export/config.py`

```python
@dataclass
class Config:
    token: str
    deployment_id: str
    deployment_slug: str  # NEW: Required for projects API
    # ... existing fields
    
    def __post_init__(self):
        if not self.token:
            raise ValueError("SEMGREP_APP_TOKEN is required")
        if not self.deployment_id:
            raise ValueError("deployment_id is required")
        if not self.deployment_slug:  # NEW validation
            raise ValueError("deployment_slug is required")
```

#### 1.2 CLI Arguments
Add new argument to argument parser:

```python
parser.add_argument(
    "--deployment-slug",
    help="Semgrep deployment slug for projects API (can also use SEMGREP_DEPLOYMENT_SLUG env var)"
)
```

#### 1.3 Environment Variable Support
```python
deployment_slug = args.deployment_slug or os.getenv("SEMGREP_DEPLOYMENT_SLUG")
```

#### 1.4 Configuration Updates
**File**: `.env.example`
```bash
# Required: Semgrep Deployment Slug  
# Used for fetching repository names via Projects API
# Find this in your Semgrep dashboard (different from deployment_id)
SEMGREP_DEPLOYMENT_SLUG=your_deployment_slug_here
```

### Phase 2: API Client Enhancement

#### 2.1 New Projects API Method
**File**: `src/semgrep_deps_export/api_client.py`

```python
def get_projects(self) -> Dict[str, Any]:
    """Get all projects/repositories for the deployment."""
    endpoint = f"/deployments/{self.config.deployment_slug}/projects"
    
    response = self._make_request("GET", endpoint)
    return response

def _build_repository_mapping(self) -> Dict[str, str]:
    """Build a mapping of repository_id -> repository_name."""
    try:
        logger.info("Fetching repository information...")
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
```

#### 2.2 Integration with Dependencies Workflow
```python
def get_repository_mapping(self) -> Dict[str, str]:
    """Public method to get repository mapping."""
    return self._build_repository_mapping()
```

### Phase 3: Data Model Enhancement

#### 3.1 ProcessedDependency Updates
**File**: `src/semgrep_deps_export/data_processor.py`

```python
@dataclass
class ProcessedDependency:
    id: str
    repository_id: str          # Keep for backwards compatibility
    repository_name: str        # NEW: Human-readable repository name
    name: str
    version: str
    ecosystem: str
    package_manager: str
    transitivity: str
    licenses: str
    bad_license: bool
    # ... other existing fields
```

#### 3.2 DataProcessor Enhancement
```python
class DataProcessor:
    def __init__(self, bad_license_types: Optional[List[str]] = None, 
                 repository_mapping: Optional[Dict[str, str]] = None):
        # ... existing initialization
        self.repository_mapping = repository_mapping or {}
    
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
    
    def _process_dependency(self, raw_dep: Dict[str, Any]) -> Optional[ProcessedDependency]:
        # ... existing processing logic
        
        repository_id = self._extract_field(raw_dep, "repositoryId", "")
        repository_name = self._get_repository_name(repository_id)
        
        return ProcessedDependency(
            # ... existing fields
            repository_id=repository_id,
            repository_name=repository_name,  # NEW field
            # ... rest of fields
        )
```

### Phase 4: Excel Export Enhancement

#### 4.1 Column Structure Decision
**Recommended Approach**: Replace "Repository ID" with "Repository Name" as first column

**New Excel Structure**:
| Column 1 | Column 2 | Column 3 | Column 4 | Column 5 | Column 6 | Column 7 | Column 8 |
|----------|----------|----------|----------|----------|----------|----------|----------|
| **Repository Name** | Name | Version | Ecosystem | Package Manager | Transitivity | Bad_License | Licenses |

#### 4.2 Excel Exporter Updates
**File**: `src/semgrep_deps_export/excel_exporter.py`

```python
def _create_dependencies_sheet(self, dependencies: List[ProcessedDependency]) -> Worksheet:
    # Define updated headers
    headers = [
        "Repository Name",    # CHANGED: was "Repository ID"
        "Name",
        "Version", 
        "Ecosystem",
        "Package Manager",
        "Transitivity",
        "Bad_License",
        "Licenses"
    ]
    
    # Add data with new column mapping
    for row, dep in enumerate(dependencies, 2):
        ws.cell(row=row, column=1, value=dep.repository_name)  # CHANGED: was repository_id
        ws.cell(row=row, column=2, value=dep.name)
        # ... rest of columns remain same
```

### Phase 5: Main Workflow Integration

#### 5.1 Updated Main Flow
**File**: `src/semgrep_deps_export/main.py`

```python
def run(self) -> bool:
    try:
        # Step 1: Test API connection (existing)
        if not self.api_client.test_connection():
            return False
            
        # Step 2: NEW - Fetch repository mapping
        with error_context("Fetching repository information"):
            repository_mapping = self.api_client.get_repository_mapping()
            logger.info(f"✓ Loaded {len(repository_mapping)} repository names")
        
        # Step 3: Update data processor with mapping
        self.data_processor = DataProcessor(
            bad_license_types=self.config.bad_license_types,
            repository_mapping=repository_mapping  # NEW parameter
        )
        
        # Step 4-6: Continue with existing flow (dependencies, processing, export)
        # ... existing code
```

### Phase 6: Error Handling & Edge Cases

#### 6.1 API Error Scenarios
```python
class RepositoryMappingError(SemgrepAPIError):
    """Exception for repository mapping failures."""
    pass

# Error handling strategies:
# 1. Projects API fails → Log warning, continue with repository IDs
# 2. Repository ID not found in mapping → Use "Repo-{ID}" format  
# 3. Empty projects response → Log warning, show all as "Unknown Repository"
# 4. Network timeout → Retry with exponential backoff
```

#### 6.2 Backwards Compatibility
- Keep repository_id field in data model for potential future use
- Ensure tool works even if projects API is unavailable
- Provide clear error messages when deployment_slug is missing

#### 6.3 Performance Considerations
```python
# Repository mapping is fetched once at startup
# Mapping stored in memory (typically <1MB for thousands of repos)
# No additional API calls during dependency processing
# Projects API call adds ~2-3 seconds to total runtime
```

### Phase 7: Configuration & Documentation

#### 7.1 Help Text Updates
```python
parser.add_argument(
    "--deployment-slug", 
    help="Semgrep deployment slug for repository names (required, different from deployment-id)"
)

epilog = """
Environment variables:
  SEMGREP_APP_TOKEN     - API token
  SEMGREP_DEPLOYMENT_ID - Deployment ID (for dependencies API)
  SEMGREP_DEPLOYMENT_SLUG - Deployment slug (for projects API)  # NEW
  ...
"""
```

#### 7.2 README.md Updates
- Update Requirements section to mention deployment_slug
- Add example showing repository names in output
- Update environment variables table
- Add troubleshooting section for repository name issues

## Implementation Sequence

### Priority 1: Core Functionality
1. Add deployment_slug to Config dataclass ✓
2. Add get_projects() method to API client ✓  
3. Add repository_name field to ProcessedDependency ✓
4. Update Excel export to show repository names ✓

### Priority 2: Integration & Error Handling
5. Update main workflow to fetch repository mapping ✓
6. Add comprehensive error handling ✓
7. Update data processor initialization ✓

### Priority 3: Configuration & UX
8. Add CLI argument and environment variable support ✓
9. Update .env.example and documentation ✓
10. Add logging and progress indicators ✓

### Priority 4: Testing & Validation
11. Test with various repository configurations
12. Validate error scenarios and fallbacks
13. Ensure backwards compatibility

## Risk Assessment & Mitigation

### High Risk
- **Projects API unavailable**: Mitigation → Graceful fallback to repository IDs
- **Invalid deployment_slug**: Mitigation → Clear error message, validation

### Medium Risk  
- **Performance impact**: Mitigation → Cache mapping, single API call
- **Memory usage**: Mitigation → Efficient storage, cleanup after use

### Low Risk
- **Column order confusion**: Mitigation → Clear headers, documentation
- **Repository name too long**: Mitigation → Excel auto-sizing, truncation if needed

## Success Criteria

### Functional Requirements
- ✅ Repository names displayed instead of IDs in Excel
- ✅ Tool works with new deployment_slug parameter
- ✅ Graceful fallback when repository names unavailable
- ✅ Backwards compatibility maintained

### Non-Functional Requirements
- ✅ Performance impact < 10% of total runtime
- ✅ Memory usage increase < 50MB
- ✅ Clear error messages for configuration issues
- ✅ Comprehensive documentation

### User Experience
- ✅ Repository names improve readability significantly
- ✅ Configuration process remains straightforward
- ✅ Error scenarios are clearly communicated

## Future Enhancements

### Potential Improvements
1. **Dual Display**: Show both repository name and ID
2. **Repository Details**: Add URL, tags, branch info as additional columns
3. **Caching**: Cache repository mapping to avoid repeated API calls
4. **Filtering**: Allow filtering dependencies by repository name
5. **Repository Groups**: Group dependencies by repository in Excel

This implementation plan provides a comprehensive roadmap for adding user-friendly repository names while maintaining system reliability and backwards compatibility.