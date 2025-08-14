# Semgrep Dependencies Export Tool

A Python tool that exports Semgrep Supply Chain dependencies to Excel with license compliance checking and human-readable repository names.

## Key Features

- **Repository Name Resolution**: Shows readable repository names instead of numeric IDs
- **License Compliance**: Flags problematic licenses (GPL, AGPL, Commercial) with red highlighting
- **Excel Export**: Clean 8-column reports optimized for compliance teams
- **Dual Logging**: Console output with automatic file logging
- **Flexible Configuration**: CLI arguments, environment variables, and .env file support

## Requirements

- Python 3.8+
- Semgrep API token with Supply Chain access
- Deployment ID and Deployment Slug from your Semgrep dashboard

## Quick Start

1. **Clone and install**:
   ```bash
   git clone https://github.com/nitinNayar/license_compliance_report.git
   cd license_compliance_report
   pip install -r requirements.txt
   ```

2. **Configure credentials**:
   ```bash
   cp .env.example .env
   # Edit .env with your Semgrep credentials
   ```

3. **Run the tool**:
   ```bash
   python src/semgrep_deps_export.py
   ```

## Configuration

### Environment Variables (.env file)

```bash
SEMGREP_APP_TOKEN=your_api_token_here
SEMGREP_DEPLOYMENT_ID=your_deployment_id_here
SEMGREP_DEPLOYMENT_SLUG=your_deployment_slug_here
SEMGREP_BAD_LICENSES=GPL-3.0,AGPL-3.0,Commercial,Proprietary
```

### Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--deployment-id` | Semgrep deployment ID | `--deployment-id deploy-123` |
| `--deployment-slug` | Deployment slug for repository names | `--deployment-slug my-org` |
| `--bad-licenses` | Comma-separated bad license list | `--bad-licenses "GPL-3.0,AGPL-3.0"` |
| `--output-dir` | Output directory | `--output-dir ./reports` |
| `--log-level` | Logging verbosity | `--log-level DEBUG` |

## Output Format

The tool generates Excel files with 8 essential columns:

| Column | Description | Example |
|--------|-------------|---------|
| **Repository Name** | Human-readable repository name | `returntocorp/semgrep` |
| **Name** | Package name | `requests` |
| **Version** | Package version | `2.28.1` |
| **Ecosystem** | Package ecosystem | `pypi` |
| **Package Manager** | Package manager | `pip` |
| **Transitivity** | Dependency type | `DIRECT` or `TRANSITIVE` |
| **Bad_License** | License compliance flag | `True` or `False` |
| **Licenses** | License names | `MIT` or `GPL-3.0, Apache-2.0` |

### Visual Features
- **Red highlighting** for dependencies with problematic licenses
- **Automatic file naming** with deployment ID and timestamp
- **Dual logging** with console output and timestamped log files

## License Compliance

Configure which licenses to flag as problematic:

**Common Bad Licenses**:
- Copyleft: `GPL-2.0`, `GPL-3.0`, `AGPL-3.0`, `LGPL-2.1`
- Commercial: `Commercial`, `Proprietary`, `Custom`
- Restrictive: `CC-BY-NC`, `SSPL-1.0`

**Example Configuration**:
```bash
SEMGREP_BAD_LICENSES=GPL-3.0,AGPL-3.0,LGPL-2.1,Commercial,Proprietary
```

## Examples

```bash
# Basic usage with .env file
python src/semgrep_deps_export.py

# Command line with custom output
python src/semgrep_deps_export.py \
  --deployment-id deploy-123 \
  --deployment-slug my-org \
  --output-dir ./custom-reports

# Debug mode with specific bad licenses
python src/semgrep_deps_export.py \
  --log-level DEBUG \
  --bad-licenses "GPL-3.0,AGPL-3.0,Commercial"
```

## Troubleshooting

**Authentication Error**:
- Verify your `SEMGREP_APP_TOKEN` has Supply Chain API permissions
- Check that `DEPLOYMENT_ID` and `DEPLOYMENT_SLUG` are correct

**No Repository Names**:
- Ensure `DEPLOYMENT_SLUG` is correct (different from deployment ID)
- Tool will fallback to "Repo-{ID}" format if Projects API fails

**Debug Mode**:
```bash
python src/semgrep_deps_export.py --log-level DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.