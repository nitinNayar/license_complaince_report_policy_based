# Semgrep Dependencies Export Tool

A Python application that retrieves dependency information from the Semgrep Supply Chain API and exports the data to an Excel (XLSX) file.

## Features

- **Complete API Integration**: Fetch all dependencies with automatic pagination handling
- **Excel Export**: Professional XLSX files with multiple worksheets
- **Comprehensive Data**: Dependencies, vulnerabilities, licenses, and project information
- **Error Handling**: Robust error handling with retry logic and exponential backoff
- **Security**: Token masking, HTTPS enforcement, and secure credential management
- **Flexibility**: Command-line arguments and environment variable support
- **Progress Tracking**: Real-time progress indicators for long operations
- **Comprehensive Testing**: Unit and integration tests included

## Requirements

- Python 3.8 or higher
- SEMGREP_APP_TOKEN with API scope permissions
- Deployment ID for the target Semgrep deployment

## Installation

### Option 1: From Source

```bash
git clone <repository-url>
cd semgrep-deps-export
pip install -r requirements.txt
```

### Option 2: Using pip (if published)

```bash
pip install semgrep-deps-export
```

## Quick Start

### Configuration with .env File (Recommended)

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your credentials:
   ```bash
   SEMGREP_APP_TOKEN=your_semgrep_api_token_here
   SEMGREP_DEPLOYMENT_ID=your_deployment_id_here
   SEMGREP_OUTPUT_DIR=./reports
   ```

3. Run the tool:
   ```bash
   python src/semgrep_deps_export.py
   ```

### Alternative: Basic Usage

```bash
# Using command-line arguments
python src/semgrep_deps_export.py --token YOUR_TOKEN --deployment-id YOUR_DEPLOYMENT_ID

# Using environment variables
export SEMGREP_APP_TOKEN="your_token_here"
export SEMGREP_DEPLOYMENT_ID="your_deployment_id"
python src/semgrep_deps_export.py --deployment-id YOUR_DEPLOYMENT_ID
```

### With Custom Output Path

```bash
python src/semgrep_deps_export.py \
  --token YOUR_TOKEN \
  --deployment-id YOUR_DEPLOYMENT_ID \
  --output /path/to/report.xlsx
```

## Configuration Options

### Command-Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `--token` | Semgrep API token | Yes* | - |
| `--deployment-id` | Deployment ID | Yes* | - |
| `--output` | Output XLSX file path | No | Auto-generated |
| `--output-dir` | Output directory | No | ./output |
| `--log-level` | Logging level | No | INFO |
| `--max-retries` | Max API retry attempts | No | 3 |
| `--timeout` | API request timeout (seconds) | No | 30 |

*Required unless provided via environment variables

### Environment Variables (.env file supported)

You can set these in a `.env` file in the project root or as environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SEMGREP_APP_TOKEN` | API token | `abc123def456...` |
| `SEMGREP_DEPLOYMENT_ID` | Deployment ID | `deployment-123` |
| `SEMGREP_OUTPUT_DIR` | Output directory | `./reports` |
| `SEMGREP_OUTPUT_PATH` | Specific output file path (overrides OUTPUT_DIR) | `/tmp/report.xlsx` |

**Note**: Create a `.env` file by copying `.env.example` and updating with your values.

### Example Commands

```bash
# Using .env file (recommended)
python src/semgrep_deps_export.py

# Minimal usage with environment variables
SEMGREP_APP_TOKEN="your_token" python src/semgrep_deps_export.py --deployment-id deploy-123

# Using output directory
python src/semgrep_deps_export.py --output-dir ./reports

# Full configuration with command line arguments
python src/semgrep_deps_export.py \
  --token your_token \
  --deployment-id deploy-123 \
  --output-dir ./custom-reports \
  --log-level DEBUG \
  --max-retries 5 \
  --timeout 60
```

## Output Format

The tool generates an Excel file with three worksheets:

### 1. Summary Sheet
- Export metadata (deployment ID, date)
- Dependency statistics
- Vulnerability breakdown by severity

### 2. Dependencies Sheet
- Dependency ID, Name, Version
- Ecosystem and Package Manager
- License information
- Vulnerability counts by severity
- First/Last seen timestamps
- Associated projects

### 3. Vulnerabilities Sheet
- Detailed vulnerability information
- Dependency association
- Severity levels with color coding
- Vulnerability descriptions

### File Naming Convention

Default: `semgrep_dependencies_{deployment_id}_{timestamp}.xlsx`

Example: `semgrep_dependencies_deploy-123_20231201_143022.xlsx`

## API Integration

### Endpoint Details
- **Base URL**: `https://semgrep.dev/api/v1`
- **Endpoint**: `/deployments/{deploymentId}/dependencies`
- **Method**: POST
- **Authentication**: Bearer token

### Pagination
The tool automatically handles pagination:
- Starts with no cursor
- Follows `has_more` flag
- Uses `cursor` for subsequent requests
- Aggregates all dependencies across pages

### Error Handling
- **401 Unauthorized**: Invalid token
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Invalid deployment ID
- **429 Rate Limited**: Exponential backoff retry
- **5xx Server Errors**: Retry with backoff
- **Network Errors**: Connection and timeout handling

## Development

### Project Structure

```
├── src/
│   ├── semgrep_deps_export/
│   │   ├── __init__.py
│   │   ├── main.py              # Main application logic
│   │   ├── config.py            # Configuration management
│   │   ├── api_client.py        # Semgrep API client
│   │   ├── data_processor.py    # Data transformation
│   │   ├── excel_exporter.py    # Excel file generation
│   │   └── utils.py             # Utility functions
│   └── semgrep_deps_export.py   # Main executable
├── tests/
│   ├── test_config.py
│   ├── test_api_client.py
│   ├── test_data_processor.py
│   ├── test_utils.py
│   └── test_integration.py
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-mock responses

# Run all tests
pytest

# Run with coverage
pytest --cov=src/semgrep_deps_export

# Run specific test files
pytest tests/test_api_client.py
pytest tests/test_integration.py
```

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd semgrep-deps-export

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-mock responses black flake8 mypy
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
flake8 src/ tests/

# Type checking
mypy src/
```

## Security Considerations

- **Token Protection**: Tokens are masked in logs and error messages
- **HTTPS Only**: All API communications use HTTPS
- **No Credential Storage**: Tokens are not stored in files or logs
- **SSL Validation**: Certificate validation is enforced
- **Input Validation**: All inputs are validated before processing

## Performance

- **Memory Efficient**: Streaming processing for large datasets
- **Concurrent Requests**: Optimized API request patterns
- **Progress Indicators**: Real-time feedback for long operations
- **Resource Limits**: Memory usage typically under 500MB

## Troubleshooting

### Common Issues

**Authentication Failed**
```
Error: API Error: Authentication failed. Please check your token
```
- Verify your `SEMGREP_APP_TOKEN` is correct
- Ensure the token has API scope permissions

**Deployment Not Found**
```
Error: API Error: Deployment not found: your-deployment-id
```
- Verify your deployment ID is correct
- Check that you have access to the deployment

**Rate Limiting**
```
Warning: Rate limited, waiting X seconds before retry...
```
- This is normal; the tool will automatically retry
- Consider reducing concurrent operations if frequent

**Permission Denied**
```
Error: Access forbidden. Token may not have required permissions
```
- Ensure your token has Supply Chain API permissions
- Contact your Semgrep admin to verify permissions

### Debug Mode

Enable debug logging for detailed information:

```bash
python src/semgrep_deps_export.py \
  --deployment-id YOUR_ID \
  --log-level DEBUG
```

### Support

For issues and bug reports:
1. Check the troubleshooting section above
2. Review logs with `--log-level DEBUG`
3. Create an issue with:
   - Command used (with token masked)
   - Full error message
   - Debug logs (with sensitive data removed)

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Ensure code quality checks pass
6. Submit a pull request

## Changelog

### Version 1.0.0
- Initial release
- Complete API integration with pagination
- Excel export with multiple worksheets
- Comprehensive error handling and retry logic
- Security features and token protection
- Full test coverage
- CLI and environment variable configuration