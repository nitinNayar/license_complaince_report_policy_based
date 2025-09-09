# Implementation Plan: Review License List Feature

## Overview
Add a new "review license types" feature that works alongside the existing "bad license types" functionality. Dependencies will be highlighted in yellow for review licenses and red for bad licenses, with support for dual highlighting when a dependency matches both criteria.

## Implementation Steps

### 1. Update Configuration (config.py)
- Add `review_license_types` parameter to the `Config` dataclass
- Add `--review-licenses` CLI argument for comma-separated review license types
- Add `SEMGREP_REVIEW_LICENSES` environment variable support
- Update help text and examples to document the new feature

### 2. Enhance Data Processor (data_processor.py)
- Add `review_license` field to `ProcessedDependency` dataclass
- Create `_is_review_license()` method to check if any dependency licenses match the review list
- Update `_process_single_dependency()` to set `review_license = True/False`
- Handle multiple licenses per dependency (license list from API)
- Update processing summary to include review license statistics

### 3. Update Excel Exporter (excel_exporter.py)
- Add "Review_License" column to dependencies sheet
- Create yellow fill style for review license highlighting
- Implement dual highlighting logic:
  - Red background for bad licenses only
  - Yellow background for review licenses only  
  - Combined styling for dependencies matching both criteria
- Update column formatting and headers

### 4. Update Main Application (main.py)
- Pass `review_license_types` from config to `DataProcessor`
- Update logging summary to report review license counts
- Ensure review license statistics are displayed alongside bad license stats

### 5. Create Implementation Document
- Write this implementation plan to `specs/implementation_plan_review_license_list.md`

### 6. Update Tests
- Add test cases for review license configuration parsing
- Test review license detection logic with single and multiple licenses
- Test Excel export with yellow highlighting
- Test dual highlighting scenarios

## Key Technical Considerations
- Case-insensitive license matching (consistent with existing bad license logic)
- Support for dependencies with multiple licenses (API returns license arrays)
- Preserve existing bad license functionality completely
- Handle edge cases where dependencies match both bad and review lists
- Maintain performance with additional license checking

## Files to Modify
- `src/semgrep_deps_export/config.py` - Add review license configuration
- `src/semgrep_deps_export/data_processor.py` - Add review license processing logic
- `src/semgrep_deps_export/excel_exporter.py` - Add yellow highlighting and Review_License column
- `src/semgrep_deps_export/main.py` - Integration and logging updates
- Test files - Add comprehensive test coverage

## Files to Create
- `specs/implementation_plan_review_license_list.md` - This implementation plan

## Expected Outcome
Users will be able to specify review licenses via `--review-licenses "MIT,Apache-2.0"` or environment variables, see a new "Review_License" column in Excel output, and have dependencies highlighted in yellow (review) and/or red (bad) based on their license types.