"""
Unit tests for data processing functionality.
"""

import os
import pytest
import sys
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from semgrep_deps_export.data_processor import DataProcessor, ProcessedDependency, ProcessedVulnerability


class TestDataProcessor:
    """Test cases for DataProcessor."""
    
    @pytest.fixture
    def processor(self):
        """Create test data processor."""
        return DataProcessor()
    
    @pytest.fixture
    def sample_dependency(self):
        """Create sample dependency data."""
        return {
            "id": "dep-123",
            "name": "test-package",
            "version": "1.2.3",
            "ecosystem": "npm",
            "package_manager": "npm",
            "licenses": ["MIT", "Apache-2.0"],
            "vulnerabilities": [
                {
                    "id": "vuln-1",
                    "severity": "high",
                    "description": "High severity vulnerability"
                },
                {
                    "id": "vuln-2",
                    "severity": "medium",
                    "description": "Medium severity vulnerability"
                }
            ],
            "first_seen": "2023-01-01T10:00:00Z",
            "last_seen": "2023-12-01T15:30:00Z",
            "projects": ["project1", "project2"]
        }
    
    def test_process_dependency_success(self, processor, sample_dependency):
        """Test successful dependency processing."""
        result = processor.process_dependency(sample_dependency)
        
        assert isinstance(result, ProcessedDependency)
        assert result.id == "dep-123"
        assert result.name == "test-package"
        assert result.version == "1.2.3"
        assert result.ecosystem == "npm"
        assert result.package_manager == "npm"
        assert result.licenses == "MIT, Apache-2.0"
        assert result.vulnerability_count == 2
        assert result.high_vulns == 1
        assert result.medium_vulns == 1
        assert result.critical_vulns == 0
        assert result.low_vulns == 0
        assert "2023-01-01" in result.first_seen
        assert "2023-12-01" in result.last_seen
        assert result.projects == "project1, project2"
    
    def test_process_dependency_missing_fields(self, processor):
        """Test processing dependency with missing fields."""
        minimal_dep = {
            "id": "dep-456",
            "name": "minimal-package"
        }
        
        result = processor.process_dependency(minimal_dep)
        
        assert isinstance(result, ProcessedDependency)
        assert result.id == "dep-456"
        assert result.name == "minimal-package"
        assert result.version == "Unknown"
        assert result.ecosystem == "Unknown"
        assert result.licenses == "Unknown"
        assert result.vulnerability_count == 0
        assert result.projects == "Unknown"
    
    def test_process_dependency_null_values(self, processor):
        """Test processing dependency with null values."""
        null_dep = {
            "id": "dep-789",
            "name": "null-package",
            "version": None,
            "licenses": None,
            "vulnerabilities": None,
            "projects": None
        }
        
        result = processor.process_dependency(null_dep)
        
        assert isinstance(result, ProcessedDependency)
        assert result.version == "Unknown"
        assert result.licenses == "Unknown"
        assert result.vulnerability_count == 0
        assert result.projects == "Unknown"
    
    def test_count_vulnerabilities_by_severity(self, processor):
        """Test vulnerability severity counting."""
        vulnerabilities = [
            {"severity": "critical"},
            {"severity": "critical"},
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
            {"severity": "info"},
            {"severity": "unknown_severity"}
        ]
        
        counts = processor._count_vulnerabilities_by_severity(vulnerabilities)
        
        assert counts["critical"] == 2
        assert counts["high"] == 1
        assert counts["medium"] == 1
        assert counts["low"] == 1
        assert counts["info"] == 2  # 'info' + 'unknown_severity'
    
    def test_format_timestamp_iso(self, processor):
        """Test ISO timestamp formatting."""
        # ISO with Z
        result = processor._format_timestamp("2023-01-01T10:00:00Z")
        assert "2023-01-01 10:00:00 UTC" == result
        
        # ISO with timezone
        result = processor._format_timestamp("2023-01-01T10:00:00+00:00")
        assert "2023-01-01 10:00:00 UTC" == result
    
    def test_format_timestamp_invalid(self, processor):
        """Test invalid timestamp formatting."""
        result = processor._format_timestamp("invalid-timestamp")
        assert result == "invalid-timestamp"
        
        result = processor._format_timestamp(None)
        assert result == "Unknown"
        
        result = processor._format_timestamp("")
        assert result == "Unknown"
    
    def test_process_vulnerabilities(self, processor, sample_dependency):
        """Test vulnerability processing for vulnerabilities sheet."""
        processor.process_dependency(sample_dependency)
        
        vulns = processor.processed_vulnerabilities
        assert len(vulns) == 2
        
        vuln1 = vulns[0]
        assert isinstance(vuln1, ProcessedVulnerability)
        assert vuln1.dependency_name == "test-package"
        assert vuln1.dependency_version == "1.2.3"
        assert vuln1.vulnerability_id == "vuln-1"
        assert vuln1.severity == "High"  # Capitalized
        assert vuln1.description == "High severity vulnerability"
    
    def test_process_all_dependencies(self, processor):
        """Test processing multiple dependencies."""
        dependencies = [
            {"id": "dep1", "name": "pkg1", "vulnerabilities": []},
            {"id": "dep2", "name": "pkg2", "vulnerabilities": [{"severity": "high"}]},
            {"id": "dep3", "name": "pkg3", "vulnerabilities": []}
        ]
        
        processed_deps, processed_vulns = processor.process_all_dependencies(iter(dependencies))
        
        assert len(processed_deps) == 3
        assert len(processed_vulns) == 1
        assert processor.processing_stats["total_processed"] == 3
    
    def test_get_processing_summary(self, processor):
        """Test processing summary generation."""
        dependencies = [
            {"id": "dep1", "name": "pkg1", "vulnerabilities": []},
            {"id": "dep2", "name": "pkg2", "vulnerabilities": [
                {"severity": "critical"}, {"severity": "high"}
            ]}
        ]
        
        processor.process_all_dependencies(iter(dependencies))
        summary = processor.get_processing_summary()
        
        assert summary["dependencies"]["total"] == 2
        assert summary["dependencies"]["with_vulnerabilities"] == 1
        assert summary["dependencies"]["without_vulnerabilities"] == 1
        assert summary["vulnerabilities"]["total"] == 2
        assert summary["vulnerabilities"]["critical"] == 1
        assert summary["vulnerabilities"]["high"] == 1
    
    def test_error_handling(self, processor):
        """Test error handling during processing."""
        # Invalid dependency data that should cause errors
        invalid_dep = {
            "id": None,  # This might cause issues
            "name": 123,  # Wrong type
        }
        
        result = processor.process_dependency(invalid_dep)
        
        # Should handle gracefully and return None or valid result
        # The actual behavior depends on implementation details
        assert result is None or isinstance(result, ProcessedDependency)
    
    def test_get_field_safety(self, processor):
        """Test safe field extraction."""
        data = {
            "existing_field": "value",
            "null_field": None,
            "nested": {"key": "nested_value"}
        }
        
        # Existing field
        assert processor._get_field(data, "existing_field") == "value"
        
        # Missing field with default
        assert processor._get_field(data, "missing_field", "default") == "default"
        
        # Null field with default
        assert processor._get_field(data, "null_field", "default") == "default"
        
        # Missing field no default
        assert processor._get_field(data, "missing_field") is None
    
    def test_empty_lists_handling(self, processor):
        """Test handling of empty lists."""
        dep_with_empty_lists = {
            "id": "dep-empty",
            "name": "empty-package",
            "licenses": [],
            "vulnerabilities": [],
            "projects": []
        }
        
        result = processor.process_dependency(dep_with_empty_lists)
        
        assert result.licenses == "Unknown"
        assert result.vulnerability_count == 0
        assert result.projects == "Unknown"