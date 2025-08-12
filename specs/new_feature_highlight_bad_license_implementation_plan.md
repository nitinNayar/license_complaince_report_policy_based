# Implementation Plan: Bad License Highlighting Feature

**Document Version:** 1.0  
**Date:** August 12, 2025  
**Status:** Implementation Plan

---

## Executive Summary

This document provides a detailed implementation plan for adding bad license detection and highlighting functionality to the Semgrep Dependencies Export Tool. The feature will allow users to specify problematic license types, automatically detect dependencies using these licenses, and visually highlight them in red in the Excel output.

---

## 1. Feature Requirements Analysis

### 1.1 Core Requirements
- **FR-001**: Accept a configurable list of "bad" license types from the user
- **FR-002**: Check each dependency's licenses against the bad license list
- **FR-003**: Add a `bad_license` boolean attribute to dependency data model  
- **FR-004**: Add a "Bad_License" column to Excel dependencies sheet
- **FR-005**: Apply red background color to rows with bad licenses
- **FR-006**: Support case-insensitive license matching
- **FR-007**: Handle multiple licenses per dependency (list evaluation)

### 1.2 Configuration Requirements
- **CFG-001**: Support CLI argument `--bad-licenses` with comma-separated list
- **CFG-002**: Support environment variable `SEMGREP_BAD_LICENSES`
- **CFG-003**: Provide sensible defaults for common problematic licenses
- **CFG-004**: Support empty/null configuration (no bad license checking)

---

## 2. Technical Architecture

### 2.1 Component Dependencies
```
Config → DataProcessor → ExcelExporter
   ↓         ↓              ↓
[Bad License List] → [License Check] → [Visual Formatting]
```

### 2.2 Data Flow Changes
1. **Configuration Loading**: CLI args/env vars parsed into bad license list
2. **Data Processing**: Each dependency checked against bad license list
3. **Excel Export**: Bad license dependencies highlighted in red

---

## 3. Implementation Details by Component

### 3.1 Configuration Management (config.py)

#### 3.1.1 Config Dataclass Extension
```python
@dataclass
class Config:
    # ... existing fields ...
    bad_license_types: Optional[List[str]] = None
```

#### 3.1.2 CLI Argument Addition
```python
parser.add_argument(
    "--bad-licenses",
    help="Comma-separated list of bad license types to highlight (e.g., 'GPL-3.0,AGPL-3.0')"
)
```

#### 3.1.3 Environment Variable Support
```python
# In load_config method
bad_licenses_str = args.bad_licenses or os.getenv("SEMGREP_BAD_LICENSES")
bad_license_types = self._parse_license_list(bad_licenses_str) if bad_licenses_str else None
```

#### 3.1.4 License List Parsing
```python
def _parse_license_list(self, license_str: str) -> List[str]:
    """Parse comma-separated license list with validation."""
    licenses = [license.strip() for license in license_str.split(',')]
    # Remove empty strings and normalize case
    return [license for license in licenses if license]
```

### 3.2 Data Processing Enhancement (data_processor.py)

#### 3.2.1 ProcessedDependency Extension
```python
@dataclass
class ProcessedDependency:
    # ... existing fields ...
    bad_license: bool = False
```

#### 3.2.2 DataProcessor Constructor Update
```python
def __init__(self, bad_license_types: Optional[List[str]] = None):
    self.bad_license_types = [license.lower() for license in bad_license_types] if bad_license_types else []
    # ... existing initialization ...
```

#### 3.2.3 Bad License Detection Logic
```python
def _check_bad_license(self, licenses_list: List[str]) -> bool:
    """Check if any license in the list is considered bad."""
    if not self.bad_license_types or not licenses_list:
        return False
    
    # Convert licenses to lowercase for case-insensitive comparison
    normalized_licenses = [license.lower().strip() for license in licenses_list]
    
    # Check if any license matches bad license list
    return any(license in self.bad_license_types for license in normalized_licenses)
```

#### 3.2.4 Process Dependency Update
```python
def process_dependency(self, raw_dependency: Dict[str, Any]) -> Optional[ProcessedDependency]:
    # ... existing processing ...
    
    # Process licenses (keep original list for bad license checking)
    licenses_list = self._get_field(raw_dependency, "licenses", [])
    licenses = ", ".join(licenses_list) if licenses_list else "Unknown"
    bad_license = self._check_bad_license(licenses_list)
    
    processed = ProcessedDependency(
        # ... existing fields ...
        licenses=licenses,
        bad_license=bad_license,
        # ... remaining fields ...
    )
```

#### 3.2.5 Statistics Enhancement
```python
def get_processing_summary(self) -> Dict[str, Any]:
    bad_license_count = sum(1 for dep in self.processed_dependencies if dep.bad_license)
    
    return {
        "dependencies": {
            # ... existing stats ...
            "with_bad_licenses": bad_license_count,
            "without_bad_licenses": len(self.processed_dependencies) - bad_license_count
        },
        # ... existing sections ...
    }
```

### 3.3 Excel Export Enhancement (excel_exporter.py)

#### 3.3.1 Headers Update
```python
headers = [
    "Repository ID",
    "Name", 
    "Version",
    "Ecosystem",
    "Package Manager",
    "Transitivity",
    "Bad_License",    # NEW COLUMN
    "Licenses",
    # ... remaining headers ...
]
```

#### 3.3.2 Data Row Writing Update
```python
def _create_dependencies_sheet(self, dependencies: List[ProcessedDependency]) -> Worksheet:
    # ... header creation ...
    
    for row, dep in enumerate(dependencies, 2):
        # ... existing column assignments ...
        ws.cell(row=row, column=7, value=dep.bad_license)  # Bad_License column
        ws.cell(row=row, column=8, value=dep.licenses)     # Licenses column (shifted)
        # ... remaining columns shifted by 1 ...
        
        # Apply conditional formatting for bad licenses
        if dep.bad_license:
            self._apply_bad_license_formatting(ws, row, len(headers))
```

#### 3.3.3 Bad License Row Formatting
```python
def _apply_bad_license_formatting(self, ws: Worksheet, row: int, num_cols: int) -> None:
    """Apply red background formatting to bad license rows."""
    bad_license_fill = PatternFill(
        start_color="FFCCCC",  # Light red background
        end_color="FFCCCC",
        fill_type="solid"
    )
    
    # Apply to all cells in the row
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row, column=col)
        cell.fill = bad_license_fill
```

### 3.4 Main Application Integration (main.py)

#### 3.4.1 DataProcessor Initialization Update
```python
def __init__(self, config: Config):
    self.config = config
    self.api_client = SemgrepAPIClient(config)
    self.data_processor = DataProcessor(bad_license_types=config.bad_license_types)  # Updated
    self.excel_exporter = ExcelExporter(config)
```

#### 3.4.2 Summary Logging Enhancement
```python
def _log_summary(self, summary: dict) -> None:
    logger.info("Processing Summary:")
    logger.info(f"  Dependencies:")
    logger.info(f"    Total: {summary['dependencies']['total']}")
    logger.info(f"    With bad licenses: {summary['dependencies']['with_bad_licenses']}")  # NEW
    logger.info(f"    Without bad licenses: {summary['dependencies']['without_bad_licenses']}")  # NEW
    # ... existing logging ...
```

---

## 4. Configuration Examples

### 4.1 Command-Line Usage
```bash
# Basic usage with bad licenses
python src/semgrep_deps_export.py --bad-licenses "GPL-3.0,AGPL-3.0,Commercial"

# Combined with other options
python src/semgrep_deps_export.py \
  --deployment-id 37285 \
  --bad-licenses "GPL-3.0,AGPL-3.0,LGPL-2.1,Commercial" \
  --output-dir ./compliance-reports
```

### 4.2 Environment Variable
```bash
# .env file
SEMGREP_BAD_LICENSES=GPL-3.0,AGPL-3.0,Commercial,Proprietary

# Command line export
export SEMGREP_BAD_LICENSES="GPL-3.0,AGPL-3.0,Commercial"
python src/semgrep_deps_export.py
```

### 4.3 Common Bad License Lists
```bash
# Copyleft licenses
SEMGREP_BAD_LICENSES="GPL-2.0,GPL-3.0,AGPL-3.0,LGPL-2.1,LGPL-3.0"

# Commercial/Proprietary licenses  
SEMGREP_BAD_LICENSES="Commercial,Proprietary,Custom"

# Comprehensive list
SEMGREP_BAD_LICENSES="GPL-2.0,GPL-3.0,AGPL-3.0,LGPL-2.1,LGPL-3.0,Commercial,Proprietary"
```

---

## 5. Visual Design Specifications

### 5.1 Excel Formatting
- **Bad License Column**: Boolean values (True/False)
- **Column Position**: After "Transitivity", before "Licenses" 
- **Red Row Highlighting**: Light red background (#FFCCCC) for entire row
- **Text Contrast**: Dark text maintained for readability

### 5.2 Column Layout (Updated)
| Position | Column Name | Description |
|----------|-------------|-------------|
| 1 | Repository ID | Unique repository identifier |
| 2 | Name | Dependency package name |
| 3 | Version | Package version |
| 4 | Ecosystem | Package ecosystem (npm, pypi, etc.) |
| 5 | Package Manager | Derived package manager |
| 6 | Transitivity | DIRECT or TRANSITIVE |
| **7** | **Bad_License** | **True/False (NEW)** |
| 8 | Licenses | Comma-separated license list |
| 9+ | ... | Remaining vulnerability and metadata columns |

---

## 6. Testing Strategy

### 6.1 Unit Tests
- **License Parsing**: Test comma-separated list parsing and validation
- **Bad License Detection**: Test case-insensitive matching logic
- **Configuration Loading**: Test CLI args and environment variables
- **Data Processing**: Test bad_license field population

### 6.2 Integration Tests  
- **End-to-End**: Test complete workflow with sample bad licenses
- **Excel Output**: Verify Bad_License column creation and formatting
- **Visual Formatting**: Test red row highlighting application
- **Performance**: Ensure no significant performance impact

### 6.3 Manual Testing Scenarios
```bash
# Test Case 1: No bad licenses specified
python src/semgrep_deps_export.py

# Test Case 2: GPL licenses marked as bad
python src/semgrep_deps_export.py --bad-licenses "GPL-3.0"

# Test Case 3: Multiple bad licenses with mixed case
python src/semgrep_deps_export.py --bad-licenses "gpl-3.0,AGPL-3.0,commercial"

# Test Case 4: Environment variable override
SEMGREP_BAD_LICENSES="MIT" python src/semgrep_deps_export.py --bad-licenses "GPL-3.0"
```

---

## 7. Implementation Phases

### Phase 1: Configuration Framework (30 minutes)
- ✅ Update Config dataclass
- ✅ Add CLI argument parsing
- ✅ Add environment variable support
- ✅ Implement license list parsing

### Phase 2: Data Processing Logic (45 minutes)  
- ✅ Extend ProcessedDependency dataclass
- ✅ Update DataProcessor constructor
- ✅ Implement bad license detection logic
- ✅ Update processing statistics

### Phase 3: Excel Export Enhancement (30 minutes)
- ✅ Add Bad_License column to headers
- ✅ Update data row writing logic
- ✅ Implement red row highlighting
- ✅ Test column positioning and formatting

### Phase 4: Integration and Testing (15 minutes)
- ✅ Update main.py integration
- ✅ Update .env.example
- ✅ Manual testing with sample data
- ✅ Verify end-to-end functionality

**Total Estimated Time: 2 hours**

---

## 8. Risk Assessment and Mitigation

### 8.1 Potential Risks
| Risk | Impact | Mitigation |
|------|---------|------------|
| **Performance Impact** | License checking adds processing overhead | Use efficient list operations and caching |
| **Memory Usage** | Additional data field increases memory | Minimal impact due to boolean field type |
| **Excel Formatting** | Complex conditional formatting | Implement robust error handling |
| **Configuration Complexity** | Users may struggle with license names | Provide clear documentation and examples |

### 8.2 Backwards Compatibility
- **No Breaking Changes**: Feature is opt-in via configuration
- **Default Behavior**: No bad license checking when not configured  
- **Existing Exports**: Continue to work without modification

---

## 9. Success Criteria

### 9.1 Functional Requirements
- ✅ Users can specify bad licenses via CLI or environment variables
- ✅ Dependencies with bad licenses are correctly identified
- ✅ Bad_License column appears in Excel output with correct True/False values
- ✅ Rows with bad licenses are highlighted in red
- ✅ Processing statistics include bad license counts

### 9.2 Quality Requirements
- ✅ Case-insensitive license matching works correctly
- ✅ Multiple licenses per dependency handled properly
- ✅ No performance degradation on large datasets (33k+ dependencies)
- ✅ Excel formatting maintains professional appearance

### 9.3 Usability Requirements  
- ✅ Clear documentation and examples provided
- ✅ Intuitive CLI argument naming and help text
- ✅ Meaningful error messages for invalid configurations

---

## 10. Future Enhancements (Out of Scope)

### 10.1 Advanced Features
- **License File Import**: Support reading bad licenses from file
- **License Categorization**: Group licenses by risk level (high/medium/low)
- **Custom Color Coding**: User-configurable colors for different risk levels
- **License Recommendations**: Suggest alternative licenses for bad ones
- **Regex Pattern Matching**: Support pattern matching for license detection

### 10.2 Integration Opportunities
- **Policy Enforcement**: Integration with CI/CD pipelines for license gates
- **Compliance Reporting**: Generate compliance summaries by license type
- **Dashboard Integration**: Real-time bad license monitoring
- **Notification Systems**: Alert on new bad licenses detected

---

## Conclusion

This implementation plan provides a comprehensive approach to adding bad license detection and highlighting functionality to the Semgrep Dependencies Export Tool. The feature enhances compliance capabilities while maintaining the tool's performance and usability characteristics. The modular implementation ensures easy testing and maintenance while providing clear value to users managing license compliance requirements.