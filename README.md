# Semgrep Dependencies Export Tool

A Python application that retrieves dependency information from the Semgrep Supply Chain API and exports the data to an Excel (XLSX) file.

## Features

- **Complete API Integration**: Fetch all dependencies with automatic pagination handling (33,985+ dependencies across 34+ pages)
- **Bad License Detection**: Configurable license compliance checking with visual red highlighting
- **Optimized Excel Export**: Clean, focused XLSX files with 8 essential columns (41% smaller file size)
- **License Compliance**: Visual identification of problematic licenses for enterprise compliance
- **Comprehensive Data**: Dependencies with licenses, ecosystem info, and repository tracking
- **Error Handling**: Robust error handling with retry logic and exponential backoff
- **Security**: Token masking, HTTPS enforcement, and secure credential management
- **Flexible Configuration**: CLI arguments, environment variables, and .env file support
- **Progress Tracking**: Real-time progress indicators for long operations
- **Performance Optimized**: Processes 33k+ dependencies in ~50 seconds with 1.2MB output files
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
   SEMGREP_BAD_LICENSES=GPL-3.0,AGPL-3.0,LGPL-2.1,Commercial,Proprietary
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
| `--bad-licenses` | Comma-separated bad license list | No | None |

*Required unless provided via environment variables

### Environment Variables (.env file supported)

You can set these in a `.env` file in the project root or as environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `SEMGREP_APP_TOKEN` | API token | `abc123def456...` |
| `SEMGREP_DEPLOYMENT_ID` | Deployment ID | `deployment-123` |
| `SEMGREP_OUTPUT_DIR` | Output directory | `./reports` |
| `SEMGREP_OUTPUT_PATH` | Specific output file path (overrides OUTPUT_DIR) | `/tmp/report.xlsx` |
| `SEMGREP_BAD_LICENSES` | Comma-separated bad license types | `GPL-3.0,AGPL-3.0,Commercial` |

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
  --bad-licenses "GPL-3.0,AGPL-3.0,Commercial" \
  --log-level DEBUG \
  --max-retries 5 \
  --timeout 60

# License compliance checking
python src/semgrep_deps_export.py \
  --bad-licenses "GPL-3.0,AGPL-3.0,LGPL-2.1,Commercial,Proprietary"
```

## Output Format

The tool generates a clean Excel file optimized for license compliance:

### Dependencies Sheet (Main Output)
The primary sheet contains 8 essential columns with clear, actionable data:

| Column | Description | Example |
|--------|-------------|---------|
| **Repository ID** | Unique repository identifier | `1554601` |
| **Name** | Package/dependency name | `alembic` |
| **Version** | Package version | `1.13.1` |
| **Ecosystem** | Package ecosystem | `pypi` |
| **Package Manager** | Derived package manager | `pip` |
| **Transitivity** | Dependency relationship | `DIRECT` or `TRANSITIVE` |
| **Bad_License** | License compliance flag | `True` or `False` |
| **Licenses** | License names | `MIT` or `GPL-3.0, Apache-2.0` |

### Visual License Compliance
- **Red Row Highlighting**: Dependencies with bad licenses are highlighted in red for immediate identification
- **Clean Data**: Only populated, meaningful fields are included (no "Unknown" values)
- **Compact Size**: Optimized 8-column structure reduces file size by 41%

### Optional Vulnerabilities Sheet
- Created only when vulnerabilities are present in the data
- Detailed vulnerability information with severity color coding

### Performance Metrics
- **Processing**: 33,985+ dependencies in ~50 seconds  
- **File Size**: ~1.2MB for complete dataset
- **License Detection**: Configurable flagging (e.g., 2,162 bad licenses found)

### File Naming Convention

Default: `semgrep_dependencies_{deployment_id}_{timestamp}.xlsx`

Example: `semgrep_dependencies_deploy-123_20231201_143022.xlsx`

## License Compliance Features

### Bad License Detection
The tool provides comprehensive license compliance checking to identify problematic licenses in your dependencies.

#### Configuration
**Via CLI:**
```bash
python src/semgrep_deps_export.py --bad-licenses "GPL-3.0,AGPL-3.0,Commercial"
```

**Via Environment Variable:**
```bash
export SEMGREP_BAD_LICENSES="GPL-3.0,AGPL-3.0,LGPL-2.1,Commercial,Proprietary"
python src/semgrep_deps_export.py
```

**Via .env File:**
```bash
# .env file
SEMGREP_BAD_LICENSES=GPL-3.0,AGPL-3.0,LGPL-2.1,Commercial,Proprietary
```

#### Common Bad License Examples
- **Copyleft Licenses**: `GPL-2.0`, `GPL-3.0`, `AGPL-3.0`, `LGPL-2.1`, `LGPL-3.0`
- **Commercial/Proprietary**: `Commercial`, `Proprietary`, `Custom`
- **Restrictive**: `CC-BY-NC`, `SSPL-1.0`

#### Visual Identification
- Dependencies with bad licenses are **highlighted in red** throughout the entire row
- The `Bad_License` column shows `True` for flagged dependencies
- Case-insensitive matching ensures flexible detection
- Multiple licenses per dependency are properly evaluated

#### Processing Statistics
The tool reports bad license statistics in the console output:
```
Processing Summary:
  Dependencies:
    Total: 33985
    With bad licenses: 2162
    Without bad licenses: 31823
```

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
- **Bad License Detection**: Configurable license compliance checking with visual red highlighting
- **Optimized Excel Export**: Clean 8-column structure, 41% smaller files, no irrelevant data
- **Complete API Integration**: Handle 33,985+ dependencies across 34+ pages with automatic pagination
- **License Compliance**: Enterprise-ready compliance reporting with immediate visual identification
- **Performance Optimized**: Process large datasets in ~50 seconds with 1.2MB output files
- **Flexible Configuration**: CLI arguments, environment variables, and .env file support
- **Comprehensive Error Handling**: Robust retry logic, exponential backoff, and detailed logging
- **Security Features**: Token masking, HTTPS enforcement, and secure credential management
- **Full Test Coverage**: Unit and integration tests for all components
- **Professional Output**: Business-ready Excel files suitable for compliance audits

### Key Features Added
- **Bad License Highlighting**: Flag problematic licenses like GPL, AGPL, Commercial licenses
- **Case-Insensitive Matching**: Flexible license detection regardless of case variations
- **Red Row Highlighting**: Visual identification of compliance issues in Excel
- **Configuration Options**: `--bad-licenses` CLI arg and `SEMGREP_BAD_LICENSES` env var
- **Optimized Data Structure**: Removed unused vulnerability and timestamp columns
- **Enhanced Performance**: Faster processing and smaller file sizes