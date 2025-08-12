"""
Unit tests for configuration management.
"""

import os
import pytest
from unittest.mock import patch, MagicMock
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from semgrep_deps_export.config import Config, ConfigManager


class TestConfig:
    """Test cases for Config dataclass."""
    
    def test_config_valid(self):
        """Test valid configuration."""
        config = Config(
            token="test_token_12345",
            deployment_id="test_deployment_123"
        )
        
        assert config.token == "test_token_12345"
        assert config.deployment_id == "test_deployment_123"
        assert config.log_level == "INFO"  # default
        assert config.max_retries == 3     # default
    
    def test_config_missing_token(self):
        """Test configuration with missing token."""
        with pytest.raises(ValueError, match="SEMGREP_APP_TOKEN is required"):
            Config(token="", deployment_id="test_deployment")
    
    def test_config_missing_deployment_id(self):
        """Test configuration with missing deployment_id."""
        with pytest.raises(ValueError, match="deployment_id is required"):
            Config(token="test_token", deployment_id="")
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = Config(
            token="test_token",
            deployment_id="test_deployment",
            output_path="/tmp/output.xlsx",
            log_level="DEBUG",
            max_retries=5,
            timeout=60
        )
        
        assert config.output_path == "/tmp/output.xlsx"
        assert config.log_level == "DEBUG"
        assert config.max_retries == 5
        assert config.timeout == 60


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def test_create_parser(self):
        """Test parser creation."""
        manager = ConfigManager()
        parser = manager._create_parser()
        
        assert parser is not None
        assert "token" in parser._option_string_actions
        assert "deployment-id" in parser._option_string_actions
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'env_token_123',
        'SEMGREP_DEPLOYMENT_ID': 'env_deployment_456'
    })
    @patch('sys.argv', ['script.py'])
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.token == "env_token_123"
        assert config.deployment_id == "env_deployment_456"
    
    @patch('sys.argv', [
        'script.py',
        '--token', 'cli_token_123',
        '--deployment-id', 'cli_deployment_456',
        '--log-level', 'DEBUG'
    ])
    def test_load_config_from_cli(self):
        """Test loading configuration from CLI arguments."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.token == "cli_token_123"
        assert config.deployment_id == "cli_deployment_456"
        assert config.log_level == "DEBUG"
    
    @patch.dict(os.environ, {'SEMGREP_APP_TOKEN': 'env_token'})
    @patch('sys.argv', [
        'script.py',
        '--deployment-id', 'cli_deployment',
        '--token', 'cli_token'
    ])
    def test_cli_overrides_env(self):
        """Test that CLI arguments override environment variables."""
        manager = ConfigManager()
        config = manager.load_config()
        
        # CLI should override env
        assert config.token == "cli_token"
        assert config.deployment_id == "cli_deployment"
    
    @patch('sys.argv', ['script.py'])
    @patch('sys.exit')
    def test_missing_token_exit(self, mock_exit):
        """Test that missing token causes exit."""
        manager = ConfigManager()
        manager.load_config()
        
        mock_exit.assert_called_with(1)
    
    @patch.dict(os.environ, {'SEMGREP_APP_TOKEN': 'test_token'})
    @patch('sys.argv', ['script.py'])
    @patch('sys.exit')
    def test_missing_deployment_id_exit(self, mock_exit):
        """Test that missing deployment_id causes exit."""
        manager = ConfigManager()
        manager.load_config()
        
        mock_exit.assert_called_with(1)
    
    @patch('sys.argv', [
        'script.py',
        '--token', 'test_token',
        '--deployment-id', 'test_deployment',
        '--output', '/custom/path.xlsx',
        '--max-retries', '5',
        '--timeout', '60'
    ])
    def test_all_options(self):
        """Test all command line options."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.token == "test_token"
        assert config.deployment_id == "test_deployment"
        assert config.output_path == "/custom/path.xlsx"
        assert config.max_retries == 5
        assert config.timeout == 60