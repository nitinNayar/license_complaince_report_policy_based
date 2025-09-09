"""
Main module for the Semgrep Dependencies Export Tool.

Orchestrates the entire process of fetching, processing, and exporting dependency data.
"""

import logging
import sys
from typing import Optional

from .config import ConfigManager, Config
from .api_client import SemgrepAPIClient, SemgrepAPIError
from .data_processor import DataProcessor
from .excel_exporter import ExcelExporter
from .utils import setup_logging, ProgressTracker, error_context


logger = logging.getLogger(__name__)


class SemgrepDepsExporter:
    """Main application class for exporting Semgrep dependencies."""
    
    def __init__(self, config: Config):
        self.config = config
        self.api_client = SemgrepAPIClient(config)
        self.excel_exporter = ExcelExporter(config)
        
        # Initialize progress tracker
        self.progress = ProgressTracker(description="Processing dependencies")
        
        # DataProcessor will be initialized after fetching repository mapping
        self.data_processor = None
    
    def run(self) -> bool:
        """Run the complete export process."""
        logger.info("Starting Semgrep Dependencies Export")
        logger.info(f"Deployment ID: {self.config.deployment_id}")
        logger.info(f"Log Level: {self.config.log_level}")
        logger.info("Fetch Mode: Per-Repository")
        
        try:
            # Step 1: Test API connection
            with error_context("API connection test"):
                if not self.api_client.test_connection():
                    logger.error("API connection test failed. Please check your token and deployment ID.")
                    return False
                logger.info("✓ API connection test successful")
            
            # Step 2: Fetch repository mapping
            with error_context("Fetching repository information"):
                repository_mapping = self.api_client.get_repository_mapping()
                logger.info(f"✓ Loaded {len(repository_mapping)} repository names")
                
                # Initialize data processor with repository mapping
                self.data_processor = DataProcessor(
                    bad_license_types=self.config.bad_license_types,
                    review_license_types=self.config.review_license_types,
                    repository_mapping=repository_mapping
                )
            
            # Step 3: Fetch all dependencies
            with error_context("Fetching dependencies from API"):
                logger.info("Using per-repository dependency fetching mode")
                dependencies_iterator = self.api_client.get_all_dependencies_by_repository()
                logger.info("✓ Starting per-repository dependency retrieval")
            
            # Step 4: Process dependencies
            with error_context("Processing dependency data"):
                logger.info("Processing dependency data...")
                processed_dependencies, processed_vulnerabilities = self.data_processor.process_all_dependencies(
                    dependencies_iterator
                )
                
                if not processed_dependencies:
                    logger.warning("No dependencies were processed. Check API response and logs.")
                    return False
                
                logger.info(f"✓ Processed {len(processed_dependencies)} dependencies")
                logger.info(f"✓ Found {len(processed_vulnerabilities)} vulnerabilities")
            
            # Step 5: Generate summary
            summary = self.data_processor.get_processing_summary()
            self._log_summary(summary)
            
            # Step 6: Export to Excel
            with error_context("Exporting to Excel"):
                output_path = self.excel_exporter.export(
                    processed_dependencies,
                    processed_vulnerabilities,
                    summary
                )
                logger.info(f"✓ Excel export completed: {output_path}")
            
            # Step 7: Export filtered data (bad/review licenses) to separate Excel file
            with error_context("Exporting filtered dependencies"):
                filtered_output_path = self.excel_exporter.export_filtered(
                    processed_dependencies,
                    processed_vulnerabilities,
                    summary
                )
                if filtered_output_path:
                    logger.info(f"✓ Filtered Excel export completed: {filtered_output_path}")
                else:
                    logger.info("✓ No dependencies with bad/review licenses found")
            
            # Step 8: Conditionally export LICENSE_POLICY_SETTING_BLOCK dependencies
            policy_blocked_output_path = None
            if self.config.policy_licenses_block:
                with error_context("Exporting LICENSE_POLICY_SETTING_BLOCK dependencies"):
                    logger.info("LICENSE_POLICY_SETTING_BLOCK export enabled, fetching policy blocked dependencies...")
                    
                    # Fetch dependencies with LICENSE_POLICY_SETTING_BLOCK
                    blocked_dependencies_iterator = self.api_client.get_all_dependencies_by_policy("LICENSE_POLICY_SETTING_BLOCK")
                    
                    # Reset processor state to prevent data accumulation from main export
                    self.data_processor.reset_state()
                    
                    # Process the policy blocked dependencies
                    processed_blocked_dependencies, processed_blocked_vulnerabilities = self.data_processor.process_all_dependencies(
                        blocked_dependencies_iterator
                    )
                    
                    logger.info(f"✓ Processed {len(processed_blocked_dependencies)} policy blocked dependencies")
                    
                    # Validate policy blocked filtering worked correctly
                    if len(processed_blocked_dependencies) > 1000:  # Threshold check - should be much smaller subset
                        logger.warning(f"VALIDATION WARNING: Policy blocked export has {len(processed_blocked_dependencies)} dependencies")
                        logger.warning("This seems high for LICENSE_POLICY_SETTING_BLOCK filtering - may include mixed data")
                    else:
                        logger.info(f"✓ Validation passed: Policy blocked export contains reasonable count of {len(processed_blocked_dependencies)} dependencies")
                    
                    # Export policy blocked dependencies
                    policy_blocked_output_path = self.excel_exporter.export_policy_blocked(
                        processed_blocked_dependencies,
                        processed_blocked_vulnerabilities
                    )
                    
                    if policy_blocked_output_path:
                        logger.info(f"✓ Policy blocked Excel export completed: {policy_blocked_output_path}")
                    else:
                        logger.info("✓ No dependencies with LICENSE_POLICY_SETTING_BLOCK found")
            
            # Step 9: Conditionally export LICENSE_POLICY_SETTING_COMMENT dependencies
            policy_comment_output_path = None
            if self.config.policy_licenses_comment:
                with error_context("Exporting LICENSE_POLICY_SETTING_COMMENT dependencies"):
                    logger.info("LICENSE_POLICY_SETTING_COMMENT export enabled, fetching policy comment dependencies...")
                    
                    # Fetch dependencies with LICENSE_POLICY_SETTING_COMMENT
                    comment_dependencies_iterator = self.api_client.get_all_dependencies_by_policy("LICENSE_POLICY_SETTING_COMMENT")
                    
                    # Reset processor state to prevent data accumulation from previous exports
                    self.data_processor.reset_state()
                    
                    # Process the policy comment dependencies
                    processed_comment_dependencies, processed_comment_vulnerabilities = self.data_processor.process_all_dependencies(
                        comment_dependencies_iterator
                    )
                    
                    logger.info(f"✓ Processed {len(processed_comment_dependencies)} policy comment dependencies")
                    
                    # Validate policy comment filtering worked correctly
                    if len(processed_comment_dependencies) > 2000:  # Threshold check - should be much smaller subset
                        logger.warning(f"VALIDATION WARNING: Policy comment export has {len(processed_comment_dependencies)} dependencies")
                        logger.warning("This seems high for LICENSE_POLICY_SETTING_COMMENT filtering - may include mixed data")
                    else:
                        logger.info(f"✓ Validation passed: Policy comment export contains reasonable count of {len(processed_comment_dependencies)} dependencies")
                    
                    # Export policy comment dependencies
                    policy_comment_output_path = self.excel_exporter.export_policy_comment(
                        processed_comment_dependencies,
                        processed_comment_vulnerabilities
                    )
                    
                    if policy_comment_output_path:
                        logger.info(f"✓ Policy comment Excel export completed: {policy_comment_output_path}")
                    else:
                        logger.info("✓ No dependencies with LICENSE_POLICY_SETTING_COMMENT found")
            
            # Step 10: Conditionally export PyPI ecosystem dependencies
            ecosystem_pypi_output_path = None
            if self.config.ecosystem_pypi:
                with error_context("Exporting PyPI ecosystem dependencies"):
                    logger.info("PyPI ecosystem export enabled, fetching PyPI ecosystem dependencies...")
                    
                    try:
                        # Fetch dependencies with ecosystem: pypi
                        pypi_dependencies_iterator = self.api_client.get_all_dependencies_by_ecosystem("pypi")
                        
                        # Reset processor state to prevent data accumulation from main export
                        self.data_processor.reset_state()
                        
                        # Process the PyPI ecosystem dependencies
                        processed_pypi_dependencies, processed_pypi_vulnerabilities = self.data_processor.process_all_dependencies(
                            pypi_dependencies_iterator
                        )
                        
                        logger.info(f"✓ Processed {len(processed_pypi_dependencies)} PyPI ecosystem dependencies")
                        
                        # Validate that all dependencies are actually from PyPI ecosystem
                        non_pypi_deps = [dep for dep in processed_pypi_dependencies if dep.ecosystem.lower() != "pypi"]
                        if non_pypi_deps:
                            logger.error(f"VALIDATION ERROR: Found {len(non_pypi_deps)} non-PyPI dependencies in ecosystem export!")
                            logger.error(f"Non-PyPI ecosystems found: {set(dep.ecosystem for dep in non_pypi_deps[:5])}")
                            logger.warning("Ecosystem filtering may not be working correctly")
                        else:
                            logger.info(f"✓ Validation passed: All {len(processed_pypi_dependencies)} dependencies are PyPI ecosystem")
                        
                        if processed_pypi_dependencies:
                            # Export PyPI ecosystem dependencies
                            ecosystem_pypi_output_path = self.excel_exporter.export_ecosystem_pypi(
                                processed_pypi_dependencies,
                                processed_pypi_vulnerabilities
                            )
                            
                            if ecosystem_pypi_output_path:
                                logger.info(f"✓ PyPI ecosystem Excel export completed: {ecosystem_pypi_output_path}")
                            else:
                                logger.info("✓ No PyPI ecosystem dependencies found")
                        else:
                            logger.info("✓ No PyPI ecosystem dependencies found (API may not support ecosystem filtering)")
                            
                    except Exception as e:
                        logger.warning(f"PyPI ecosystem export failed: {str(e)}")
                        logger.info("✓ Continuing without PyPI ecosystem export")
            
            # Final success message
            logger.info("=" * 60)
            logger.info("EXPORT COMPLETED SUCCESSFULLY")
            logger.info(f"Output file: {output_path}")
            if filtered_output_path:
                logger.info(f"Filtered output file: {filtered_output_path}")
            if policy_blocked_output_path:
                logger.info(f"Policy blocked output file: {policy_blocked_output_path}")
            if policy_comment_output_path:
                logger.info(f"Policy comment output file: {policy_comment_output_path}")
            if ecosystem_pypi_output_path:
                logger.info(f"PyPI ecosystem output file: {ecosystem_pypi_output_path}")
            logger.info(f"Dependencies: {len(processed_dependencies)}")
            logger.info(f"Vulnerabilities: {len(processed_vulnerabilities)}")
            logger.info("=" * 60)
            
            return True
            
        except SemgrepAPIError as e:
            logger.error(f"API Error: {str(e)}")
            if e.status_code == 401:
                logger.error("Please verify your SEMGREP_APP_TOKEN is correct and has API access.")
            elif e.status_code == 403:
                logger.error("Please ensure your token has Supply Chain API permissions.")
            elif e.status_code == 404:
                logger.error("Please verify your deployment_id is correct.")
            return False
            
        except KeyboardInterrupt:
            logger.warning("Export interrupted by user")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            logger.debug("Full error details:", exc_info=True)
            return False
    
    def _log_summary(self, summary: dict) -> None:
        """Log processing summary."""
        logger.info("Processing Summary:")
        logger.info(f"  Dependencies:")
        logger.info(f"    Total: {summary['dependencies']['total']}")
        logger.info(f"    With vulnerabilities: {summary['dependencies']['with_vulnerabilities']}")
        logger.info(f"    Without vulnerabilities: {summary['dependencies']['without_vulnerabilities']}")
        logger.info(f"    With bad licenses: {summary['dependencies']['with_bad_licenses']}")
        logger.info(f"    Without bad licenses: {summary['dependencies']['without_bad_licenses']}")
        logger.info(f"    With review licenses: {summary['dependencies']['with_review_licenses']}")
        logger.info(f"    Without review licenses: {summary['dependencies']['without_review_licenses']}")
        
        logger.info(f"  Vulnerabilities:")
        logger.info(f"    Total: {summary['vulnerabilities']['total']}")
        logger.info(f"    Critical: {summary['vulnerabilities']['critical']}")
        logger.info(f"    High: {summary['vulnerabilities']['high']}")
        logger.info(f"    Medium: {summary['vulnerabilities']['medium']}")
        logger.info(f"    Low: {summary['vulnerabilities']['low']}")


def main() -> int:
    """Main entry point for the application."""
    try:
        # Load configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        # Setup logging
        setup_logging(level=config.log_level, deployment_id=config.deployment_id)
        
        logger.info("Semgrep Dependencies Export Tool v1.0.0")
        
        # Validate configuration
        if not config.token or not config.deployment_id:
            logger.error("Both SEMGREP_APP_TOKEN and deployment_id are required")
            return 1
        
        # Create and run exporter
        exporter = SemgrepDepsExporter(config)
        success = exporter.run()
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.warning("Application interrupted by user")
        return 130  # Standard exit code for Ctrl+C
        
    except Exception as e:
        logger.error(f"Application failed to start: {str(e)}")
        logger.debug("Full error details:", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())