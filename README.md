# Semgrep Dependencies Export Tool

A Python tool that exports Semgrep Supply Chain dependencies to Excel with license compliance checking and human-readable repository names.

## Key Features

- **Repository Name Resolution**: Shows readable repository names instead of numeric IDs
- **License Compliance**: Flags problematic licenses (GPL, AGPL, Commercial) with red highlighting
- **Review License Tracking**: Marks licenses requiring review with yellow highlighting
- **Policy-Based Filtering**: Generate separate reports for LICENSE_POLICY_SETTING_BLOCK and LICENSE_POLICY_SETTING_COMMENT dependencies
- **Ecosystem Filtering**: Create targeted reports for specific package ecosystems (PyPI, npm, etc.)
- **Excel Export**: Clean reports optimized for compliance teams with multiple output formats
- **Dual Logging**: Console output with automatic file logging
- **Flexible Configuration**: CLI arguments, environment variables, and .env file support

## Requirements

- Python 3.8+
- Semgrep API token with Supply Chain access
- Deployment ID and Deployment Slug from your Semgrep dashboard

## Quick Start

1. **Clone and install**:
   ```bash
   git clone https://github.com/nitinNayar/license_complaince_report_policy_based.git
   cd license_complaince_report_policy_based
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
# Required Configuration
SEMGREP_APP_TOKEN=your_api_token_here
SEMGREP_DEPLOYMENT_ID=your_deployment_id_here
SEMGREP_DEPLOYMENT_SLUG=your_deployment_slug_here

# License Classification (Optional)
SEMGREP_BAD_LICENSES=GPL-3.0,AGPL-3.0,Commercial,Proprietary
SEMGREP_REVIEW_LICENSES=MIT,Apache-2.0,BSD-2-Clause

# Policy-Based Filtering (Optional)
SEMGREP_POLICY_LICENSES_BLOCK=true     # Generate report for blocked license dependencies
SEMGREP_POLICY_LICENSES_COMMENT=true   # Generate report for comment license dependencies

# Ecosystem Filtering (Optional)
SEMGREP_ECOSYSTEM_PYPI=true            # Generate report for PyPI ecosystem dependencies
```

### Command Line Options

| Option | Description | Example |
|--------|-------------|---------|
| `--deployment-id` | Semgrep deployment ID | `--deployment-id deploy-123` |
| `--deployment-slug` | Deployment slug for repository names | `--deployment-slug my-org` |
| `--bad-licenses` | Comma-separated bad license list | `--bad-licenses "GPL-3.0,AGPL-3.0"` |
| `--review-licenses` | Comma-separated review license list | `--review-licenses "MIT,Apache-2.0"` |
| `--output-dir` | Output directory | `--output-dir ./reports` |
| `--log-level` | Logging verbosity | `--log-level DEBUG` |

## Output Format

The tool generates Excel files with 9 essential columns. See [`example_license_report.xlsx`](example_license_report.xlsx) for a sample of what the output looks like:

| Column | Description | Example |
|--------|-------------|---------|
| **Repository Name** | Human-readable repository name | `returntocorp/semgrep` |
| **Name** | Package name | `requests` |
| **Version** | Package version | `2.28.1` |
| **Ecosystem** | Package ecosystem | `pypi` |
| **Package Manager** | Package manager | `pip` |
| **Transitivity** | Dependency type | `DIRECT` or `TRANSITIVE` |
| **Bad_License** | License compliance flag | `True` or `False` |
| **Review_License** | Review license flag | `True` or `False` |
| **Licenses** | License names | `MIT` or `GPL-3.0, Apache-2.0` |

### Visual Features
- **Red highlighting** for dependencies with problematic licenses
- **Yellow highlighting** for dependencies requiring review
- **Orange highlighting** for dependencies with both bad and review licenses
- **Automatic file naming** with deployment ID and timestamp
- **Dual logging** with console output and timestamped log files
- **Filtered export** generates separate file with only flagged dependencies

## License Compliance

Configure which licenses to flag as problematic and which require review:

**Common Bad Licenses** (highlighted in red):
- Copyleft: `GPL-2.0`, `GPL-3.0`, `AGPL-3.0`, `LGPL-2.1`
- Commercial: `Commercial`, `Proprietary`, `Custom`
- Restrictive: `CC-BY-NC`, `SSPL-1.0`

**Common Review Licenses** (highlighted in yellow):
- Permissive: `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`
- Other: `ISC`, `0BSD`, `Unlicense`

**Example Configuration**:
```bash
SEMGREP_BAD_LICENSES=GPL-3.0,AGPL-3.0,LGPL-2.1,Commercial,Proprietary
SEMGREP_REVIEW_LICENSES=MIT,Apache-2.0,BSD-2-Clause
```

## Policy-Based Filtering

The tool supports generating separate Excel reports based on Semgrep license policy settings. This enables focused compliance analysis for different license policy categories.

### Available Policy Filters

#### LICENSE_POLICY_SETTING_BLOCK
Generate a report containing only dependencies with the `LICENSE_POLICY_SETTING_BLOCK` policy setting. These are typically dependencies with licenses that are blocked by your organization's policy.

```bash
SEMGREP_POLICY_LICENSES_BLOCK=true
```

**Output**: `policy_blocked_semgrep_dependencies_<deployment_id>_<timestamp>.xlsx`

#### LICENSE_POLICY_SETTING_COMMENT  
Generate a report containing only dependencies with the `LICENSE_POLICY_SETTING_COMMENT` policy setting. These are dependencies that require additional review or comments.

```bash
SEMGREP_POLICY_LICENSES_COMMENT=true
```

**Output**: `policy_comment_semgrep_dependencies_<deployment_id>_<timestamp>.xlsx`

### Policy Report Format

Policy-based reports use a clean 7-column format (no license classification columns):

| Column | Description |
|--------|-------------|
| **Repository Name** | Human-readable repository name |
| **Name** | Package name |
| **Version** | Package version |
| **Ecosystem** | Package ecosystem |
| **Package Manager** | Package manager |
| **Transitivity** | DIRECT or TRANSITIVE |
| **Licenses** | License names |

**Key Features**:
- ✅ **No color coding** - Clean format for policy review
- ✅ **No bad/review license columns** - Focused on policy classification
- ✅ **Separate files** - Each policy type gets its own Excel file
- ✅ **Filtered data** - Contains only dependencies matching the policy

### Ecosystem Filtering

Generate reports for specific package ecosystems:

```bash
SEMGREP_ECOSYSTEM_PYPI=true        # Python packages (PyPI)
# More ecosystems coming soon: npm, Maven, etc.
```

**Output**: `ecosystem_pypi_semgrep_dependencies_<deployment_id>_<timestamp>.xlsx`

## Examples

### Basic Usage

```bash
# Standard export with license analysis
python src/semgrep_deps_export.py

# With custom output directory
python src/semgrep_deps_export.py --output-dir ./compliance-reports
```

### Policy-Based Filtering

```bash
# Generate reports for blocked license dependencies only
SEMGREP_POLICY_LICENSES_BLOCK=true python src/semgrep_deps_export.py

# Generate reports for comment license dependencies only  
SEMGREP_POLICY_LICENSES_COMMENT=true python src/semgrep_deps_export.py

# Generate both policy reports
SEMGREP_POLICY_LICENSES_BLOCK=true SEMGREP_POLICY_LICENSES_COMMENT=true python src/semgrep_deps_export.py
```

### Ecosystem Filtering

```bash
# Generate PyPI ecosystem report only
SEMGREP_ECOSYSTEM_PYPI=true python src/semgrep_deps_export.py

# Combine ecosystem and policy filtering
SEMGREP_ECOSYSTEM_PYPI=true SEMGREP_POLICY_LICENSES_BLOCK=true python src/semgrep_deps_export.py
```

### Advanced Usage

```bash
# All filtering options enabled
SEMGREP_POLICY_LICENSES_BLOCK=true \
SEMGREP_POLICY_LICENSES_COMMENT=true \
SEMGREP_ECOSYSTEM_PYPI=true \
python src/semgrep_deps_export.py

# Debug mode with custom licenses
python src/semgrep_deps_export.py \
  --log-level DEBUG \
  --bad-licenses "GPL-3.0,AGPL-3.0,Commercial" \
  --review-licenses "MIT,Apache-2.0"
```

### Generated Files

When filtering is enabled, you'll get multiple output files:

```
./reports/
├── semgrep_dependencies_37285_20240909_120000.xlsx              # Main report (all deps)
├── bad_review_license_semgrep_dependencies_37285_20240909_120005.xlsx  # Flagged licenses
├── policy_blocked_semgrep_dependencies_37285_20240909_120010.xlsx      # Policy blocked
├── policy_comment_semgrep_dependencies_37285_20240909_120015.xlsx      # Policy comment
└── ecosystem_pypi_semgrep_dependencies_37285_20240909_120020.xlsx      # PyPI ecosystem
```

## Troubleshooting

**Authentication Error**:
- Verify your `SEMGREP_APP_TOKEN` has Supply Chain API permissions
- Check that `DEPLOYMENT_ID` and `DEPLOYMENT_SLUG` are correct

**No Repository Names**:
- Ensure `DEPLOYMENT_SLUG` is correct (different from deployment ID)
- Tool will fallback to "Repo-{ID}" format if Projects API fails

**Policy Filtering Issues**:
- Ensure your Semgrep deployment has license policies configured
- Policy reports will be empty if no dependencies match the policy settings
- Check validation messages in the logs for data integrity issues

**Ecosystem Filtering Issues**:
- Currently only PyPI ecosystem filtering is supported
- Ecosystem reports will be empty if no dependencies match the specified ecosystem
- Check API logs for ecosystem filter compatibility

**Empty Reports**:
- Policy blocked/comment reports are empty → No dependencies match those policy settings
- Ecosystem reports are empty → No dependencies from that ecosystem found
- Check the main report first to verify dependencies are being processed

**Debug Mode**:
```bash
python src/semgrep_deps_export.py --log-level DEBUG
```

**Validation Checks**:
The tool includes built-in validation to ensure data integrity:
- Policy reports should contain reasonable dependency counts (< 1000-2000)
- Ecosystem reports should contain only dependencies from the specified ecosystem
- Warning messages will appear if validation fails

