"""
Unit tests for utility functions.
"""

import logging
import os
import pytest
import sys
import time
from unittest.mock import patch, MagicMock

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from semgrep_deps_export.utils import (
    setup_logging, ProgressTracker, error_context, safe_get_nested,
    validate_deployment_id, validate_token_format, format_file_size,
    chunk_iterator, mask_sensitive_data
)


class TestSetupLogging:
    """Test cases for setup_logging function."""
    
    def test_setup_logging_default(self):
        """Test setup_logging with defaults."""
        setup_logging()
        
        # Check that root logger is configured
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO
    
    def test_setup_logging_custom_level(self):
        """Test setup_logging with custom level."""
        setup_logging(level="DEBUG")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.DEBUG
    
    def test_setup_logging_invalid_level(self):
        """Test setup_logging with invalid level defaults to INFO."""
        setup_logging(level="INVALID")
        
        root_logger = logging.getLogger()
        assert root_logger.level == logging.INFO


class TestProgressTracker:
    """Test cases for ProgressTracker."""
    
    def test_progress_tracker_init(self):
        """Test ProgressTracker initialization."""
        tracker = ProgressTracker(total=100, description="Testing")
        
        assert tracker.total == 100
        assert tracker.description == "Testing"
        assert tracker.current == 0
    
    def test_progress_tracker_update(self):
        """Test ProgressTracker update."""
        tracker = ProgressTracker(total=10)
        
        tracker.update(5)
        assert tracker.current == 5
        
        tracker.update(2)
        assert tracker.current == 7
    
    def test_progress_tracker_set_total(self):
        """Test setting total after initialization."""
        tracker = ProgressTracker()
        assert tracker.total is None
        
        tracker.set_total(50)
        assert tracker.total == 50
    
    @patch('semgrep_deps_export.utils.logging.getLogger')
    def test_progress_tracker_logging(self, mock_get_logger):
        """Test ProgressTracker logging."""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        tracker = ProgressTracker(total=10, description="Test Progress")
        
        # Force immediate update by setting last_update to 0
        tracker.last_update = 0
        tracker.update_interval = 0
        
        tracker.update(5)
        
        # Should have logged progress
        mock_logger.info.assert_called()
    
    def test_format_duration(self):
        """Test duration formatting."""
        tracker = ProgressTracker()
        
        assert tracker._format_duration(30) == "30.0s"
        assert tracker._format_duration(90) == "1.5m"
        assert tracker._format_duration(7200) == "2.0h"


class TestErrorContext:
    """Test cases for error_context."""
    
    def test_error_context_success(self):
        """Test error_context with successful operation."""
        mock_logger = MagicMock()
        
        with error_context("Test Operation", logger=mock_logger):
            pass  # Successful operation
        
        mock_logger.debug.assert_any_call("Starting: Test Operation")
        mock_logger.debug.assert_any_call("Completed: Test Operation")
        mock_logger.error.assert_not_called()
    
    def test_error_context_failure(self):
        """Test error_context with failed operation."""
        mock_logger = MagicMock()
        
        with pytest.raises(ValueError):
            with error_context("Test Operation", logger=mock_logger):
                raise ValueError("Test error")
        
        mock_logger.debug.assert_any_call("Starting: Test Operation")
        mock_logger.error.assert_called_with("Failed: Test Operation - Test error")


class TestSafeGetNested:
    """Test cases for safe_get_nested function."""
    
    def test_safe_get_nested_success(self):
        """Test successful nested value retrieval."""
        data = {
            "level1": {
                "level2": {
                    "level3": "target_value"
                }
            }
        }
        
        result = safe_get_nested(data, "level1.level2.level3")
        assert result == "target_value"
    
    def test_safe_get_nested_missing_key(self):
        """Test missing key returns default."""
        data = {"level1": {"level2": "value"}}
        
        result = safe_get_nested(data, "level1.missing.key", default="default")
        assert result == "default"
    
    def test_safe_get_nested_partial_path(self):
        """Test partial path returns default."""
        data = {"level1": "not_dict"}
        
        result = safe_get_nested(data, "level1.level2", default="default")
        assert result == "default"
    
    def test_safe_get_nested_none_data(self):
        """Test None data returns default."""
        result = safe_get_nested(None, "any.path", default="default")
        assert result == "default"


class TestValidationFunctions:
    """Test cases for validation functions."""
    
    def test_validate_deployment_id_valid(self):
        """Test valid deployment IDs."""
        assert validate_deployment_id("abc123def") is True
        assert validate_deployment_id("deployment-123") is True
        assert validate_deployment_id("deploy_456") is True
        assert validate_deployment_id("12345678") is True
    
    def test_validate_deployment_id_invalid(self):
        """Test invalid deployment IDs."""
        assert validate_deployment_id("") is False
        assert validate_deployment_id(None) is False
        assert validate_deployment_id("short") is False
        assert validate_deployment_id("invalid@chars") is False
        assert validate_deployment_id("with spaces") is False
    
    def test_validate_token_format_valid(self):
        """Test valid token formats."""
        assert validate_token_format("abcdefghijklmnopqrstuvwxyz") is True
        assert validate_token_format("token123456789012345") is True
        assert validate_token_format("token-with-dashes-12345") is True
        assert validate_token_format("token.with.dots.12345") is True
    
    def test_validate_token_format_invalid(self):
        """Test invalid token formats."""
        assert validate_token_format("") is False
        assert validate_token_format(None) is False
        assert validate_token_format("short") is False
        assert validate_token_format("invalid@token#chars") is False


class TestFormatFileSize:
    """Test cases for format_file_size function."""
    
    def test_format_file_size_bytes(self):
        """Test file size formatting in bytes."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(512) == "512.0 B"
    
    def test_format_file_size_kilobytes(self):
        """Test file size formatting in kilobytes."""
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1536) == "1.5 KB"
    
    def test_format_file_size_megabytes(self):
        """Test file size formatting in megabytes."""
        assert format_file_size(1024 * 1024) == "1.0 MB"
        assert format_file_size(int(1.5 * 1024 * 1024)) == "1.5 MB"
    
    def test_format_file_size_gigabytes(self):
        """Test file size formatting in gigabytes."""
        assert format_file_size(1024 * 1024 * 1024) == "1.0 GB"


class TestChunkIterator:
    """Test cases for chunk_iterator function."""
    
    def test_chunk_iterator_even_chunks(self):
        """Test chunk_iterator with evenly divisible data."""
        data = list(range(10))  # [0, 1, 2, ..., 9]
        chunks = list(chunk_iterator(iter(data), 5))
        
        assert len(chunks) == 2
        assert chunks[0] == [0, 1, 2, 3, 4]
        assert chunks[1] == [5, 6, 7, 8, 9]
    
    def test_chunk_iterator_uneven_chunks(self):
        """Test chunk_iterator with unevenly divisible data."""
        data = list(range(7))  # [0, 1, 2, 3, 4, 5, 6]
        chunks = list(chunk_iterator(iter(data), 3))
        
        assert len(chunks) == 3
        assert chunks[0] == [0, 1, 2]
        assert chunks[1] == [3, 4, 5]
        assert chunks[2] == [6]
    
    def test_chunk_iterator_empty(self):
        """Test chunk_iterator with empty data."""
        chunks = list(chunk_iterator(iter([]), 5))
        assert len(chunks) == 0


class TestMaskSensitiveData:
    """Test cases for mask_sensitive_data function."""
    
    def test_mask_sensitive_data_token(self):
        """Test masking data containing token."""
        result = mask_sensitive_data("my_secret_token_12345")
        assert result.startswith("my_s")
        assert result.endswith("2345")
        assert "*" in result
    
    def test_mask_sensitive_data_password(self):
        """Test masking data containing password."""
        result = mask_sensitive_data("user_password_secret")
        assert result.startswith("user")
        assert result.endswith("ret")
        assert "*" in result
    
    def test_mask_sensitive_data_short_string(self):
        """Test masking short sensitive strings."""
        result = mask_sensitive_data("token123")
        assert result == "********"
    
    def test_mask_sensitive_data_no_keywords(self):
        """Test data without sensitive keywords."""
        original = "normal_data_string"
        result = mask_sensitive_data(original)
        assert result == original
    
    def test_mask_sensitive_data_custom_keywords(self):
        """Test masking with custom keywords."""
        result = mask_sensitive_data("my_secret_api_key", keywords=["secret"])
        assert result.startswith("my_s")
        assert "*" in result