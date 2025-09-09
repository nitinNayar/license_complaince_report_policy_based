# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python tool that exports Semgrep Supply Chain dependencies to Excel files with license compliance checking. The tool fetches dependency data from the Semgrep API, processes it for license compliance, and generates Excel reports with visual highlighting for problematic licenses.

## Development Commands

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Install in development mode with optional dev dependencies
pip install -e ".[dev]"

# Set up configuration
cp .env.example .env
# Edit .env with your Semgrep credentials
```

### Running the Tool
```bash
# Main execution methods
python src/semgrep_deps_export.py
python -m semgrep_deps_export.main

# With CLI arguments
python src/semgrep_deps_export.py --deployment-id DEPLOY_ID --output-dir ./reports
```

### Testing
```bash
# Run all tests
pytest

# Run specific test modules
pytest tests/test_config.py
pytest tests/test_api_client.py

# Run with verbose output
pytest -v

# Run with coverage (if coverage is installed)
pytest --cov=semgrep_deps_export
```

### Code Quality
```bash
# Type checking
mypy src/

# Code formatting (if black is available)
black src/ tests/ --line-length 100

# Linting (if flake8 is available)
flake8 src/ tests/
```

## Architecture

### Core Components

**Package Structure**: The main package is located at `src/semgrep_deps_export/` with a convenience wrapper at `src/semgrep_deps_export.py`.

**Main Classes**:
- `SemgrepDepsExporter` (main.py): Main orchestrator class that coordinates the entire export process
- `SemgrepAPIClient` (api_client.py): Handles all Semgrep API interactions including authentication and data fetching
- `DataProcessor` (data_processor.py): Processes raw API data and applies license compliance logic
- `ExcelExporter` (excel_exporter.py): Generates Excel files with license highlighting and formatting
- `ConfigManager` (config.py): Manages configuration from CLI args, environment variables, and .env files

### Data Flow

1. **Configuration**: ConfigManager loads settings from CLI args, environment variables, or .env file
2. **API Connection**: SemgrepAPIClient authenticates and fetches repository mappings
3. **Data Fetching**: Per-repository dependency data is retrieved from Semgrep Supply Chain API
4. **Processing**: DataProcessor applies license compliance rules and flags problematic licenses
5. **Export**: ExcelExporter generates formatted Excel files with visual highlighting

### Key Features

- **License Compliance**: Configurable "bad" (red highlight) and "review" (yellow highlight) license lists
- **Repository Resolution**: Converts numeric repo IDs to human-readable names via Semgrep Projects API
- **Dual Output**: Generates both full report and filtered report (flagged dependencies only)
- **Visual Highlighting**: Excel files use color coding for license compliance status
- **Logging**: Comprehensive logging to both console and timestamped log files

### Configuration System

The tool supports a flexible configuration hierarchy:
1. Command line arguments (highest priority)
2. Environment variables (prefixed with `SEMGREP_`)
3. .env file values
4. Default values (lowest priority)

Required credentials: `SEMGREP_APP_TOKEN`, `SEMGREP_DEPLOYMENT_ID`, `SEMGREP_DEPLOYMENT_SLUG`

### Testing Architecture

Tests are organized by component with comprehensive mocking of external dependencies:
- `test_config.py`: Configuration management and validation
- `test_api_client.py`: API client functionality with mocked HTTP responses
- `test_data_processor.py`: License processing logic
- `test_integration.py`: End-to-end workflow testing
- `test_utils.py`: Utility functions and logging

All tests use pytest with the `responses` library for HTTP mocking and `pytest-mock` for general mocking.