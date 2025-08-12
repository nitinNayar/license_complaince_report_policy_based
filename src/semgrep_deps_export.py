#!/usr/bin/env python3
"""
Semgrep Dependencies Export Tool

Main executable script for exporting Semgrep dependencies to Excel.

Usage:
    python semgrep_deps_export.py --token TOKEN --deployment-id DEPLOY_ID
    python semgrep_deps_export.py --deployment-id DEPLOY_ID --output report.xlsx

Environment variables (.env file supported):
    SEMGREP_APP_TOKEN     - API token
    SEMGREP_DEPLOYMENT_ID - Deployment ID
    SEMGREP_OUTPUT_DIR    - Output directory (default: ./output)
    SEMGREP_OUTPUT_PATH   - Specific output file path

Configuration:
    Create a .env file in the project root with your credentials:
        SEMGREP_APP_TOKEN=your_token_here
        SEMGREP_DEPLOYMENT_ID=your_deployment_id_here
        SEMGREP_OUTPUT_DIR=./reports
    
    Or copy .env.example to .env and update with your values.

Examples:
    python semgrep_deps_export.py --token abc123 --deployment-id deploy-456
    SEMGREP_APP_TOKEN=abc123 python semgrep_deps_export.py --deployment-id deploy-456
    python semgrep_deps_export.py --deployment-id deploy-456 --output /tmp/report.xlsx
    python semgrep_deps_export.py  # Uses .env file for configuration
"""

import sys
import os

# Add the src directory to Python path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from semgrep_deps_export.main import main

if __name__ == "__main__":
    sys.exit(main())