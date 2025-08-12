# Technical Requirements Specification
## Semgrep Dependencies Export Tool

**Document Version:** 1.0  
**Date:** August 12, 2025  
**Status:** Draft

---

## 1. Executive Summary

### 1.1 Purpose
This document specifies the technical requirements for a Python application that retrieves dependency information from the Semgrep Supply Chain API and exports the data to an Excel (XLSX) file.

### 1.2 Scope
The application will:
- Authenticate with the Semgrep API using provided credentials
- Retrieve all dependencies from a specified deployment
- Handle API pagination to ensure complete data retrieval
- Export the dependency data to a formatted Excel file

### 1.3 Target Users
- Security engineers
- DevOps teams
- Compliance officers
- Software developers managing application dependencies

---

## 2. Functional Requirements

### 2.1 Authentication
- **FR-001**: The application SHALL accept a SEMGREP_APP_TOKEN as input
- **FR-002**: The application SHALL accept a deployment_id as input
- **FR-003**: The token MUST have API scope permissions for accessing the Supply Chain API

### 2.2 Data Retrieval
- **FR-004**: The application SHALL retrieve dependency data from the Semgrep Supply Chain API endpoint
- **FR-005**: The application SHALL handle pagination to retrieve all available dependencies
- **FR-006**: The application SHALL process all pages of results until no more data is available

### 2.3 Data Export
- **FR-007**: The application SHALL export retrieved dependencies to an XLSX file format
- **FR-008**: The application SHALL allow users to specify the output file location
- **FR-009**: The application SHALL provide a default output location if none is specified

---

## 3. Technical Requirements

### 3.1 Platform Requirements
- **TR-001**: Python version 3.8 or higher
- **TR-002**: Compatible with Windows, macOS, and Linux operating systems

### 3.2 Dependencies
Required Python packages:
- **TR-003**: `requests` - For HTTP API calls
- **TR-004**: `openpyxl` or `xlsxwriter` - For Excel file generation
- **TR-005**: `python-dotenv` (optional) - For environment variable management
- **TR-006**: `typing` - For type hints (included in Python 3.8+)

### 3.3 Configuration
- **TR-007**: Support configuration via command-line arguments
- **TR-008**: Support configuration via environment variables
- **TR-009**: Support configuration via configuration file (optional)

---

## 4. API Integration Specifications

### 4.1 Endpoint Details
- **Base URL**: `https://semgrep.dev/api/v1`
- **Endpoint**: `/deployments/{deploymentId}/dependencies`
- **HTTP Method**: POST
- **Full URL Template**: `https://semgrep.dev/api/v1/deployments/{deploymentId}/dependencies`

### 4.2 Authentication
- **Header Name**: `Authorization`
- **Header Format**: `Bearer {SEMGREP_APP_TOKEN}`

### 4.3 Request Specification
```json
{
  "cursor": "string (optional)",
  "limit": "integer (optional, default: 100, max: 1000)"
}
```

### 4.4 Response Specification
Expected response structure:
```json
{
  "dependencies": [
    {
      "id": "string",
      "name": "string",
      "version": "string",
      "ecosystem": "string",
      "package_manager": "string",
      "licenses": ["string"],
      "vulnerabilities": [
        {
          "id": "string",
          "severity": "string",
          "description": "string"
        }
      ],
      "last_seen": "timestamp",
      "first_seen": "timestamp",
      "projects": ["string"]
    }
  ],
  "cursor": "string (for pagination)",
  "has_more": "boolean"
}
```

### 4.5 Pagination Logic
- **PAG-001**: Initial request SHALL be made with no cursor or cursor=null
- **PAG-002**: Continue requests while `has_more` is true
- **PAG-003**: Use the `cursor` from each response for the next request
- **PAG-004**: Aggregate all dependencies from multiple pages

---

## 5. Data Processing Requirements

### 5.1 Data Validation
- **DV-001**: Validate API token format before making requests
- **DV-002**: Validate deployment_id format
- **DV-003**: Handle and log malformed API responses gracefully

### 5.2 Data Transformation
- **DT-001**: Flatten nested vulnerability data for Excel export
- **DT-002**: Convert timestamps to human-readable format
- **DT-003**: Handle null/missing fields appropriately

---

## 6. Output Requirements

### 6.1 Excel File Structure
The XLSX file SHALL contain the following worksheets:

#### 6.1.1 Dependencies Sheet
Columns:
- Dependency ID
- Name
- Version
- Ecosystem
- Package Manager
- Licenses (comma-separated)
- Vulnerability Count
- Critical Vulnerabilities
- High Vulnerabilities
- Medium Vulnerabilities
- Low Vulnerabilities
- First Seen
- Last Seen
- Projects (comma-separated)

#### 6.1.2 Vulnerabilities Sheet (Optional)
Columns:
- Dependency Name
- Dependency Version
- Vulnerability ID
- Severity
- Description

### 6.2 File Naming Convention
- **Default Pattern**: `semgrep_dependencies_{deployment_id}_{timestamp}.xlsx`
- **Timestamp Format**: `YYYYMMDD_HHMMSS`

### 6.3 File Location
- **Default Location**: Current working directory
- **Custom Location**: User-specified path via command-line argument or configuration

---

## 7. Error Handling Requirements

### 7.1 API Errors
- **EH-001**: Handle HTTP 401 (Unauthorized) - Invalid token
- **EH-002**: Handle HTTP 403 (Forbidden) - Insufficient permissions
- **EH-003**: Handle HTTP 404 (Not Found) - Invalid deployment_id
- **EH-004**: Handle HTTP 429 (Rate Limited) - Implement exponential backoff
- **EH-005**: Handle HTTP 5xx errors - Server errors with retry logic

### 7.2 File System Errors
- **EH-006**: Handle insufficient disk space
- **EH-007**: Handle write permission errors
- **EH-008**: Handle invalid file path specifications

### 7.3 Network Errors
- **EH-009**: Handle connection timeouts
- **EH-010**: Handle DNS resolution failures
- **EH-011**: Handle SSL/TLS certificate errors

---

## 8. Security Requirements

### 8.1 Credential Management
- **SEC-001**: Never log or print the SEMGREP_APP_TOKEN in plain text
- **SEC-002**: Support reading token from environment variables
- **SEC-003**: Mask token in any error messages or logs
- **SEC-004**: Clear token from memory after use

### 8.2 Data Security
- **SEC-005**: Use HTTPS for all API communications
- **SEC-006**: Validate SSL certificates
- **SEC-007**: No sensitive data in log files

---

## 9. Performance Requirements

### 9.1 Response Time
- **PERF-001**: Complete execution within 5 minutes for up to 10,000 dependencies
- **PERF-002**: Implement progress indicators for long-running operations

### 9.2 Resource Usage
- **PERF-003**: Memory usage SHALL not exceed 500MB for typical operations
- **PERF-004**: Implement streaming/chunking for large datasets

---

## 10. Logging Requirements

### 10.1 Log Levels
- **LOG-001**: Support configurable log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **LOG-002**: Default log level SHALL be INFO

### 10.2 Log Content
- **LOG-003**: Log API request attempts (without sensitive data)
- **LOG-004**: Log pagination progress
- **LOG-005**: Log file creation success/failure
- **LOG-006**: Log total dependencies processed

---

## 11. Testing Requirements

### 11.1 Unit Tests
- **TEST-001**: Test token validation logic
- **TEST-002**: Test pagination handling
- **TEST-003**: Test data transformation functions
- **TEST-004**: Test Excel file generation

### 11.2 Integration Tests
- **TEST-005**: Test end-to-end flow with mock API
- **TEST-006**: Test error handling scenarios
- **TEST-007**: Test large dataset handling

### 11.3 Acceptance Criteria
- **AC-001**: Successfully authenticate with valid token
- **AC-002**: Retrieve all dependencies (handling pagination)
- **AC-003**: Generate valid XLSX file
- **AC-004**: Handle common error scenarios gracefully

---

## 12. User Interface Requirements

### 12.1 Command-Line Interface
```bash
python semgrep_deps_export.py \
  --token SEMGREP_APP_TOKEN \
  --deployment-id DEPLOYMENT_ID \
  --output /path/to/output.xlsx \
  --log-level INFO
```

### 12.2 Environment Variables
- `SEMGREP_APP_TOKEN`: API token
- `SEMGREP_DEPLOYMENT_ID`: Deployment ID
- `SEMGREP_OUTPUT_PATH`: Output file path

### 12.3 Output Messages
- Clear progress indicators
- Success confirmation with file location
- Descriptive error messages with remediation suggestions

---

## 13. Implementation Timeline

### Phase 1: Core Functionality (Week 1)
- API authentication
- Basic API calls
- Simple data export

### Phase 2: Robustness (Week 2)
- Pagination handling
- Error handling
- Retry logic

### Phase 3: Enhancement (Week 3)
- Excel formatting
- Progress indicators
- Comprehensive logging

### Phase 4: Testing & Documentation (Week 4)
- Unit tests
- Integration tests
- User documentation

---

## 14. Future Enhancements (Out of Scope)

- GUI interface
- Scheduled/automated runs
- Multiple deployment support in single execution
- Differential exports (only new/changed dependencies)
- Integration with CI/CD pipelines
- Custom filtering options
- Multiple output formats (CSV, JSON, etc.)

---

## 15. Appendices

### Appendix A: Sample Configuration File
```yaml
semgrep:
  token: ${SEMGREP_APP_TOKEN}
  deployment_id: ${SEMGREP_DEPLOYMENT_ID}
  
output:
  path: ./exports/
  format: xlsx
  
logging:
  level: INFO
  file: ./logs/semgrep_export.log
```

### Appendix B: Error Code Reference
- E001: Authentication Failed
- E002: Invalid Deployment ID
- E003: Rate Limit Exceeded
- E004: Network Error
- E005: File Write Error
- E006: Data Processing Error

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-08-12 | - | Initial draft |
