"""
Configuration management for Semgrep Dependencies Export Tool.

Handles command-line arguments, environment variables, and configuration validation.
"""

import argparse
import os
import sys
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    """Configuration container for the application."""
    
    token: str
    deployment_id: str
    output_path: Optional[str] = None
    output_dir: Optional[str] = None
    log_level: str = "INFO"
    max_retries: int = 3
    timeout: int = 30
    bad_license_types: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.token:
            raise ValueError("SEMGREP_APP_TOKEN is required")
        if not self.deployment_id:
            raise ValueError("deployment_id is required")


class ConfigManager:
    """Manages configuration from multiple sources."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create command-line argument parser."""
        parser = argparse.ArgumentParser(
            description="Export Semgrep dependencies to Excel",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python semgrep_deps_export.py --token TOKEN --deployment-id DEPLOY_ID
  python semgrep_deps_export.py --deployment-id DEPLOY_ID --output report.xlsx
  
Environment variables:
  SEMGREP_APP_TOKEN     - API token
  SEMGREP_DEPLOYMENT_ID - Deployment ID
  SEMGREP_OUTPUT_PATH   - Output file path
  SEMGREP_OUTPUT_DIR    - Output directory
            """
        )
        
        parser.add_argument(
            "--token",
            help="Semgrep API token (can also use SEMGREP_APP_TOKEN env var)"
        )
        
        parser.add_argument(
            "--deployment-id",
            help="Semgrep deployment ID (can also use SEMGREP_DEPLOYMENT_ID env var)"
        )
        
        parser.add_argument(
            "--output",
            help="Output XLSX file path (can also use SEMGREP_OUTPUT_PATH env var)"
        )
        
        parser.add_argument(
            "--output-dir",
            help="Output directory for generated files (can also use SEMGREP_OUTPUT_DIR env var)"
        )
        
        parser.add_argument(
            "--log-level",
            choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            default="INFO",
            help="Logging level (default: INFO)"
        )
        
        parser.add_argument(
            "--max-retries",
            type=int,
            default=3,
            help="Maximum number of API retry attempts (default: 3)"
        )
        
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="API request timeout in seconds (default: 30)"
        )
        
        parser.add_argument(
            "--bad-licenses",
            help="Comma-separated list of bad license types to highlight (e.g., 'GPL-3.0,AGPL-3.0')"
        )
        
        return parser
    
    def _parse_license_list(self, license_str: str) -> List[str]:
        """Parse comma-separated license list with validation."""
        if not license_str or not license_str.strip():
            return []
        
        licenses = [license.strip() for license in license_str.split(',')]
        # Remove empty strings and return non-empty licenses
        return [license for license in licenses if license]
    
    def load_config(self) -> Config:
        """Load configuration from command line and environment variables."""
        # Load environment variables from .env file
        load_dotenv()
        
        args = self.parser.parse_args()
        
        # Get values from args or environment variables
        token = args.token or os.getenv("SEMGREP_APP_TOKEN")
        deployment_id = args.deployment_id or os.getenv("SEMGREP_DEPLOYMENT_ID")
        output_path = args.output or os.getenv("SEMGREP_OUTPUT_PATH")
        output_dir = args.output_dir or os.getenv("SEMGREP_OUTPUT_DIR")
        
        # Handle bad licenses list
        bad_licenses_str = getattr(args, 'bad_licenses', None) or os.getenv("SEMGREP_BAD_LICENSES")
        bad_license_types = self._parse_license_list(bad_licenses_str) if bad_licenses_str else None
        
        if not token:
            print("Error: SEMGREP_APP_TOKEN is required. Provide via --token or environment variable.")
            sys.exit(1)
            
        if not deployment_id:
            print("Error: deployment_id is required. Provide via --deployment-id or environment variable.")
            sys.exit(1)
        
        return Config(
            token=token,
            deployment_id=deployment_id,
            output_path=output_path,
            output_dir=output_dir,
            log_level=args.log_level,
            max_retries=args.max_retries,
            timeout=args.timeout,
            bad_license_types=bad_license_types
        )