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
        self.data_processor = DataProcessor(bad_license_types=config.bad_license_types)
        self.excel_exporter = ExcelExporter(config)
        
        # Initialize progress tracker
        self.progress = ProgressTracker(description="Processing dependencies")
    
    def run(self) -> bool:
        """Run the complete export process."""
        logger.info("Starting Semgrep Dependencies Export")
        logger.info(f"Deployment ID: {self.config.deployment_id}")
        logger.info(f"Log Level: {self.config.log_level}")
        
        try:
            # Step 1: Test API connection
            with error_context("API connection test"):
                if not self.api_client.test_connection():
                    logger.error("API connection test failed. Please check your token and deployment ID.")
                    return False
                logger.info("✓ API connection test successful")
            
            # Step 2: Fetch all dependencies
            with error_context("Fetching dependencies from API"):
                dependencies_iterator = self.api_client.get_all_dependencies()
                logger.info("✓ Starting dependency retrieval")
            
            # Step 3: Process dependencies
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
            
            # Step 4: Generate summary
            summary = self.data_processor.get_processing_summary()
            self._log_summary(summary)
            
            # Step 5: Export to Excel
            with error_context("Exporting to Excel"):
                output_path = self.excel_exporter.export(
                    processed_dependencies,
                    processed_vulnerabilities,
                    summary
                )
                logger.info(f"✓ Excel export completed: {output_path}")
            
            # Final success message
            logger.info("=" * 60)
            logger.info("EXPORT COMPLETED SUCCESSFULLY")
            logger.info(f"Output file: {output_path}")
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
        setup_logging(level=config.log_level)
        
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