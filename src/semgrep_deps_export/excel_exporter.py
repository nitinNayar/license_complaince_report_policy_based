"""
Excel export functionality for Semgrep dependencies data.

Creates formatted XLSX files with Dependencies and Vulnerabilities sheets.
"""

import logging
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.worksheet import Worksheet
except ImportError:
    raise ImportError("openpyxl is required for Excel export. Install with: pip install openpyxl")

from .data_processor import ProcessedDependency, ProcessedVulnerability
from .config import Config


logger = logging.getLogger(__name__)


class ExcelExporter:
    """Exports processed dependency data to Excel format."""
    
    def __init__(self, config: Config):
        self.config = config
        self.workbook = Workbook()
        # Remove default sheet
        self.workbook.remove(self.workbook.active)
        
        # Define styles
        self.header_font = Font(bold=True, color="FFFFFF")
        self.header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        self.header_alignment = Alignment(horizontal="center", vertical="center")
        
        self.cell_alignment = Alignment(horizontal="left", vertical="center")
        self.number_alignment = Alignment(horizontal="right", vertical="center")
        
        self.border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )
        
        # Severity colors
        self.severity_colors = {
            "Critical": "FF0000",  # Red
            "High": "FF6600",      # Orange
            "Medium": "FFCC00",    # Yellow
            "Low": "99CC00",       # Light Green
            "Info": "CCCCCC"       # Gray
        }
    
    def _generate_filename(self) -> str:
        """Generate filename based on deployment ID and timestamp."""
        if self.config.output_path:
            return self.config.output_path
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"semgrep_dependencies_{self.config.deployment_id}_{timestamp}.xlsx"
        
        # Use output directory if specified, otherwise use 'output' directory
        if self.config.output_dir:
            output_dir = self.config.output_dir
        else:
            output_dir = os.path.join(os.getcwd(), "output")
        
        return os.path.join(output_dir, filename)
    
    def _create_dependencies_sheet(self, dependencies: List[ProcessedDependency]) -> Worksheet:
        """Create the Dependencies worksheet."""
        logger.info("Creating Dependencies sheet...")
        
        ws = self.workbook.create_sheet("Dependencies")
        
        # Define headers
        headers = [
            "Repository ID",
            "Name",
            "Version",
            "Ecosystem",
            "Package Manager",
            "Transitivity",
            "Bad_License",
            "Licenses"
        ]
        
        # Set headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.border
        
        # Add data
        for row, dep in enumerate(dependencies, 2):
            ws.cell(row=row, column=1, value=dep.repository_id)
            ws.cell(row=row, column=2, value=dep.name)
            ws.cell(row=row, column=3, value=dep.version)
            ws.cell(row=row, column=4, value=dep.ecosystem)
            ws.cell(row=row, column=5, value=dep.package_manager)
            ws.cell(row=row, column=6, value=dep.transitivity)
            ws.cell(row=row, column=7, value=dep.bad_license)
            ws.cell(row=row, column=8, value=dep.licenses)
            
            # Apply styles to data cells
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = self.border
                
                # All columns use left alignment now (no number columns remaining)
                cell.alignment = self.cell_alignment
            
            # Apply red highlighting for bad license rows
            if dep.bad_license:
                self._apply_bad_license_formatting(ws, row, len(headers))
        
        # Auto-adjust column widths
        for col in range(1, len(headers) + 1):
            column_letter = get_column_letter(col)
            max_length = len(headers[col-1])
            
            for row in range(2, len(dependencies) + 2):
                try:
                    cell_value = str(ws.cell(row=row, column=col).value)
                    max_length = max(max_length, len(cell_value))
                except:
                    pass
            
            # Set column width with some padding
            ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
        
        # Freeze the header row
        ws.freeze_panes = "A2"
        
        logger.info(f"Dependencies sheet created with {len(dependencies)} rows")
        return ws
    
    def _apply_bad_license_formatting(self, ws: Worksheet, row: int, num_cols: int) -> None:
        """Apply red background formatting to bad license rows."""
        bad_license_fill = PatternFill(
            start_color="FFCCCC",  # Light red background
            end_color="FFCCCC",
            fill_type="solid"
        )
        
        # Apply to all cells in the row
        for col in range(1, num_cols + 1):
            cell = ws.cell(row=row, column=col)
            # Preserve existing border formatting
            if cell.border:
                cell.fill = bad_license_fill
            else:
                cell.fill = bad_license_fill
                cell.border = self.border
    
    def _create_vulnerabilities_sheet(self, vulnerabilities: List[ProcessedVulnerability]) -> Optional[Worksheet]:
        """Create the Vulnerabilities worksheet."""
        if not vulnerabilities:
            logger.info("No vulnerabilities to export, skipping Vulnerabilities sheet")
            return None
            
        logger.info("Creating Vulnerabilities sheet...")
        
        ws = self.workbook.create_sheet("Vulnerabilities")
        
        # Define headers
        headers = [
            "Dependency Name",
            "Dependency Version",
            "Vulnerability ID",
            "Severity",
            "Description"
        ]
        
        # Set headers
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.header_alignment
            cell.border = self.border
        
        # Add data
        for row, vuln in enumerate(vulnerabilities, 2):
            ws.cell(row=row, column=1, value=vuln.dependency_name)
            ws.cell(row=row, column=2, value=vuln.dependency_version)
            ws.cell(row=row, column=3, value=vuln.vulnerability_id)
            ws.cell(row=row, column=4, value=vuln.severity)
            ws.cell(row=row, column=5, value=vuln.description)
            
            # Apply styles to data cells
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=row, column=col)
                cell.border = self.border
                cell.alignment = self.cell_alignment
                
                # Color-code severity
                if col == 4:  # Severity column
                    severity = vuln.severity
                    if severity in self.severity_colors:
                        cell.fill = PatternFill(
                            start_color=self.severity_colors[severity],
                            end_color=self.severity_colors[severity],
                            fill_type="solid"
                        )
                        # Use white text for dark backgrounds
                        if severity in ["Critical", "High"]:
                            cell.font = Font(color="FFFFFF", bold=True)
                        else:
                            cell.font = Font(bold=True)
        
        # Auto-adjust column widths
        for col in range(1, len(headers) + 1):
            column_letter = get_column_letter(col)
            max_length = len(headers[col-1])
            
            for row in range(2, min(len(vulnerabilities) + 2, 100)):  # Check first 100 rows for performance
                try:
                    cell_value = str(ws.cell(row=row, column=col).value)
                    max_length = max(max_length, len(cell_value))
                except:
                    pass
            
            # Set column width with some padding
            if col == 5:  # Description column - limit width
                ws.column_dimensions[column_letter].width = min(max_length + 2, 80)
            else:
                ws.column_dimensions[column_letter].width = min(max_length + 2, 40)
        
        # Freeze the header row
        ws.freeze_panes = "A2"
        
        logger.info(f"Vulnerabilities sheet created with {len(vulnerabilities)} rows")
        return ws
    
    def _create_summary_sheet(self, summary: Dict[str, Any]) -> Worksheet:
        """Create a summary sheet with processing statistics."""
        logger.info("Creating Summary sheet...")
        
        ws = self.workbook.create_sheet("Summary", 0)  # Insert as first sheet
        
        # Title
        ws.cell(row=1, column=1, value="Semgrep Dependencies Export Summary")
        ws.cell(row=1, column=1).font = Font(size=16, bold=True)
        ws.merge_cells("A1:D1")
        
        # Export metadata
        ws.cell(row=3, column=1, value="Export Details")
        ws.cell(row=3, column=1).font = Font(bold=True)
        
        ws.cell(row=4, column=1, value="Deployment ID:")
        ws.cell(row=4, column=2, value=self.config.deployment_id)
        
        ws.cell(row=5, column=1, value="Export Date:")
        ws.cell(row=5, column=2, value=datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"))
        
        # Dependencies summary
        ws.cell(row=7, column=1, value="Dependencies Summary")
        ws.cell(row=7, column=1).font = Font(bold=True)
        
        ws.cell(row=8, column=1, value="Total Dependencies:")
        ws.cell(row=8, column=2, value=summary["dependencies"]["total"])
        
        ws.cell(row=9, column=1, value="With Vulnerabilities:")
        ws.cell(row=9, column=2, value=summary["dependencies"]["with_vulnerabilities"])
        
        ws.cell(row=10, column=1, value="Without Vulnerabilities:")
        ws.cell(row=10, column=2, value=summary["dependencies"]["without_vulnerabilities"])
        
        # Vulnerabilities summary
        ws.cell(row=12, column=1, value="Vulnerabilities Summary")
        ws.cell(row=12, column=1).font = Font(bold=True)
        
        ws.cell(row=13, column=1, value="Total Vulnerabilities:")
        ws.cell(row=13, column=2, value=summary["vulnerabilities"]["total"])
        
        ws.cell(row=14, column=1, value="Critical:")
        ws.cell(row=14, column=2, value=summary["vulnerabilities"]["critical"])
        
        ws.cell(row=15, column=1, value="High:")
        ws.cell(row=15, column=2, value=summary["vulnerabilities"]["high"])
        
        ws.cell(row=16, column=1, value="Medium:")
        ws.cell(row=16, column=2, value=summary["vulnerabilities"]["medium"])
        
        ws.cell(row=17, column=1, value="Low:")
        ws.cell(row=17, column=2, value=summary["vulnerabilities"]["low"])
        
        # Auto-adjust column widths
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        
        return ws
    
    def export(self, dependencies: List[ProcessedDependency], vulnerabilities: List[ProcessedVulnerability], summary: Dict[str, Any]) -> str:
        """Export data to Excel file."""
        output_path = self._generate_filename()
        
        logger.info(f"Starting Excel export to {output_path}")
        
        try:
            # Create sheets
            self._create_dependencies_sheet(dependencies)
            
            if vulnerabilities:
                self._create_vulnerabilities_sheet(vulnerabilities)
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            
            # Save workbook
            self.workbook.save(output_path)
            
            # Get file size for logging
            file_size = os.path.getsize(output_path)
            file_size_mb = file_size / (1024 * 1024)
            
            logger.info(f"Excel export completed successfully:")
            logger.info(f"  - File: {output_path}")
            logger.info(f"  - Size: {file_size_mb:.2f} MB")
            logger.info(f"  - Sheets: Dependencies" + (", Vulnerabilities" if vulnerabilities else ""))
            
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to export Excel file: {str(e)}")
            raise Exception(f"Excel export failed: {str(e)}")
    
    def __del__(self):
        """Clean up workbook resources."""
        if hasattr(self, 'workbook'):
            try:
                self.workbook.close()
            except:
                pass