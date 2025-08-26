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
            deployment_id="test_deployment_123",
            deployment_slug="test_org"
        )
        
        assert config.token == "test_token_12345"
        assert config.deployment_id == "test_deployment_123"
        assert config.deployment_slug == "test_org"
        assert config.log_level == "INFO"  # default
        assert config.max_retries == 3     # default
        assert config.per_repository is False  # default
        assert config.bad_license_types is None  # default
        assert config.review_license_types is None  # default
    
    def test_config_missing_token(self):
        """Test configuration with missing token."""
        with pytest.raises(ValueError, match="SEMGREP_APP_TOKEN is required"):
            Config(token="", deployment_id="test_deployment", deployment_slug="test_org")
    
    def test_config_missing_deployment_id(self):
        """Test configuration with missing deployment_id."""
        with pytest.raises(ValueError, match="deployment_id is required"):
            Config(token="test_token", deployment_id="", deployment_slug="test_org")
    
    def test_config_missing_deployment_slug(self):
        """Test configuration with missing deployment_slug."""
        with pytest.raises(ValueError, match="deployment_slug is required"):
            Config(token="test_token", deployment_id="test_deployment", deployment_slug="")
    
    def test_config_custom_values(self):
        """Test configuration with custom values."""
        config = Config(
            token="test_token",
            deployment_id="test_deployment",
            deployment_slug="test_org",
            output_path="/tmp/output.xlsx",
            log_level="DEBUG",
            max_retries=5,
            timeout=60
        )
        
        assert config.output_path == "/tmp/output.xlsx"
        assert config.log_level == "DEBUG"
        assert config.max_retries == 5
        assert config.timeout == 60
    
    def test_config_with_license_lists(self):
        """Test configuration with license lists."""
        config = Config(
            token="test_token",
            deployment_id="test_deployment",
            deployment_slug="test_org",
            bad_license_types=["GPL-3.0", "AGPL-3.0"],
            review_license_types=["MIT", "Apache-2.0"]
        )
        
        assert config.bad_license_types == ["GPL-3.0", "AGPL-3.0"]
        assert config.review_license_types == ["MIT", "Apache-2.0"]


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def test_create_parser(self):
        """Test parser creation."""
        manager = ConfigManager()
        parser = manager._create_parser()
        
        assert parser is not None
        assert "--token" in parser._option_string_actions
        assert "--deployment-id" in parser._option_string_actions
        assert "--per-repository" in parser._option_string_actions
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'env_token_123',
        'SEMGREP_DEPLOYMENT_ID': 'env_deployment_456',
        'SEMGREP_DEPLOYMENT_SLUG': 'env_org'
    })
    @patch('sys.argv', ['script.py'])
    def test_load_config_from_env(self):
        """Test loading configuration from environment variables."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.token == "env_token_123"
        assert config.deployment_id == "env_deployment_456"
        assert config.deployment_slug == "env_org"
    
    @patch('sys.argv', [
        'script.py',
        '--token', 'cli_token_123',
        '--deployment-id', 'cli_deployment_456',
        '--deployment-slug', 'cli_org',
        '--log-level', 'DEBUG'
    ])
    def test_load_config_from_cli(self):
        """Test loading configuration from CLI arguments."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.token == "cli_token_123"
        assert config.deployment_id == "cli_deployment_456"
        assert config.deployment_slug == "cli_org"
        assert config.log_level == "DEBUG"
    
    @patch.dict(os.environ, {'SEMGREP_APP_TOKEN': 'env_token'})
    @patch('sys.argv', [
        'script.py',
        '--deployment-id', 'cli_deployment',
        '--deployment-slug', 'cli_org',
        '--token', 'cli_token'
    ])
    def test_cli_overrides_env(self):
        """Test that CLI arguments override environment variables."""
        manager = ConfigManager()
        config = manager.load_config()
        
        # CLI should override env
        assert config.token == "cli_token"
        assert config.deployment_id == "cli_deployment"
        assert config.deployment_slug == "cli_org"
    
    @patch('sys.argv', [
        'script.py',
        '--token', 'test_token',
        '--deployment-id', 'test_deployment',
        '--deployment-slug', 'test_org',
        '--bad-licenses', 'GPL-3.0,AGPL-3.0',
        '--review-licenses', 'MIT,Apache-2.0'
    ])
    def test_license_arguments(self):
        """Test license arguments parsing."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.bad_license_types == ["GPL-3.0", "AGPL-3.0"]
        assert config.review_license_types == ["MIT", "Apache-2.0"]
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'test_token',
        'SEMGREP_DEPLOYMENT_ID': 'test_deployment',
        'SEMGREP_DEPLOYMENT_SLUG': 'test_org',
        'SEMGREP_BAD_LICENSES': 'GPL-3.0,LGPL-2.1',
        'SEMGREP_REVIEW_LICENSES': 'MIT,BSD-3-Clause'
    })
    @patch('sys.argv', ['script.py'])
    def test_license_environment_variables(self):
        """Test license environment variables parsing."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.bad_license_types == ["GPL-3.0", "LGPL-2.1"]
        assert config.review_license_types == ["MIT", "BSD-3-Clause"]
    
    @patch.dict(os.environ, {
        'SEMGREP_DEPLOYMENT_ID': 'test_deployment',
        'SEMGREP_DEPLOYMENT_SLUG': 'test_org'
    }, clear=True)  # Clear all other env vars
    @patch('sys.argv', ['script.py'])
    @patch('semgrep_deps_export.config.load_dotenv')  # Mock dotenv loading
    def test_missing_token_exit(self, mock_load_dotenv):
        """Test that missing token causes exit."""
        manager = ConfigManager()
        with pytest.raises(SystemExit) as excinfo:
            manager.load_config()
        assert excinfo.value.code == 1
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'test_token',
        'SEMGREP_DEPLOYMENT_SLUG': 'test_org'
    }, clear=True)  # Clear all other env vars
    @patch('sys.argv', ['script.py'])
    @patch('semgrep_deps_export.config.load_dotenv')  # Mock dotenv loading
    def test_missing_deployment_id_exit(self, mock_load_dotenv):
        """Test that missing deployment_id causes exit."""
        manager = ConfigManager()
        with pytest.raises(SystemExit) as excinfo:
            manager.load_config()
        assert excinfo.value.code == 1
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'test_token',
        'SEMGREP_DEPLOYMENT_ID': 'test_deployment'
    }, clear=True)  # Clear all other env vars
    @patch('sys.argv', ['script.py'])
    @patch('semgrep_deps_export.config.load_dotenv')  # Mock dotenv loading
    def test_missing_deployment_slug_exit(self, mock_load_dotenv):
        """Test that missing deployment_slug causes exit."""
        manager = ConfigManager()
        with pytest.raises(SystemExit) as excinfo:
            manager.load_config()
        assert excinfo.value.code == 1
    
    @patch('sys.argv', [
        'script.py',
        '--token', 'test_token',
        '--deployment-id', 'test_deployment',
        '--deployment-slug', 'test_org',
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
        assert config.deployment_slug == "test_org"
        assert config.output_path == "/custom/path.xlsx"
        assert config.max_retries == 5
        assert config.timeout == 60
        assert config.per_repository is False  # default
    
    @patch('sys.argv', [
        'script.py',
        '--token', 'test_token',
        '--deployment-id', 'test_deployment',
        '--deployment-slug', 'test_org',
        '--per-repository'
    ])
    def test_per_repository_flag(self):
        """Test per-repository command line flag."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.per_repository is True
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'test_token',
        'SEMGREP_DEPLOYMENT_ID': 'test_deployment', 
        'SEMGREP_DEPLOYMENT_SLUG': 'test_org',
        'SEMGREP_PER_REPOSITORY': 'true'
    })
    @patch('sys.argv', ['script.py'])
    def test_per_repository_env_var_true(self):
        """Test per-repository environment variable (true)."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.per_repository is True
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'test_token',
        'SEMGREP_DEPLOYMENT_ID': 'test_deployment',
        'SEMGREP_DEPLOYMENT_SLUG': 'test_org', 
        'SEMGREP_PER_REPOSITORY': 'false'
    })
    @patch('sys.argv', ['script.py'])
    def test_per_repository_env_var_false(self):
        """Test per-repository environment variable (false)."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.per_repository is False
    
    @patch.dict(os.environ, {
        'SEMGREP_APP_TOKEN': 'test_token',
        'SEMGREP_DEPLOYMENT_ID': 'test_deployment',
        'SEMGREP_DEPLOYMENT_SLUG': 'test_org',
        'SEMGREP_PER_REPOSITORY': '1'
    })
    @patch('sys.argv', ['script.py'])
    def test_per_repository_env_var_numeric(self):
        """Test per-repository environment variable (numeric)."""
        manager = ConfigManager()
        config = manager.load_config()
        
        assert config.per_repository is True