"""
Utility functions for the Semgrep Dependencies Export Tool.

Contains helper functions for logging, progress tracking, and other common operations.
"""

import logging
import sys
import time
from typing import Optional, Any, Iterator
from contextlib import contextmanager


def setup_logging(level: str = "INFO", format_string: Optional[str] = None) -> None:
    """Setup logging configuration for the application."""
    
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Convert string level to logging level
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific loggers to appropriate levels
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)


class ProgressTracker:
    """Simple progress tracker for long-running operations."""
    
    def __init__(self, total: Optional[int] = None, description: str = "Processing"):
        self.total = total
        self.description = description
        self.current = 0
        self.start_time = time.time()
        self.last_update = 0
        self.update_interval = 1.0  # Update every second
        
        self.logger = logging.getLogger(__name__)
    
    def update(self, increment: int = 1) -> None:
        """Update progress by increment amount."""
        self.current += increment
        current_time = time.time()
        
        # Only update if enough time has passed
        if current_time - self.last_update >= self.update_interval:
            self._log_progress()
            self.last_update = current_time
    
    def set_total(self, total: int) -> None:
        """Set or update the total count."""
        self.total = total
    
    def _log_progress(self) -> None:
        """Log current progress."""
        elapsed = time.time() - self.start_time
        
        if self.total:
            percentage = (self.current / self.total) * 100
            rate = self.current / elapsed if elapsed > 0 else 0
            
            if rate > 0 and self.current < self.total:
                eta_seconds = (self.total - self.current) / rate
                eta_str = f", ETA: {self._format_duration(eta_seconds)}"
            else:
                eta_str = ""
            
            self.logger.info(f"{self.description}: {self.current}/{self.total} ({percentage:.1f}%){eta_str}")
        else:
            rate = self.current / elapsed if elapsed > 0 else 0
            self.logger.info(f"{self.description}: {self.current} items ({rate:.1f}/sec)")
    
    def finish(self) -> None:
        """Mark progress as complete and log final stats."""
        elapsed = time.time() - self.start_time
        rate = self.current / elapsed if elapsed > 0 else 0
        
        self.logger.info(f"{self.description} completed: {self.current} items in {self._format_duration(elapsed)} ({rate:.2f}/sec)")
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"


@contextmanager
def error_context(operation: str, logger: Optional[logging.Logger] = None):
    """Context manager for error handling with logging."""
    if logger is None:
        logger = logging.getLogger(__name__)
    
    try:
        logger.debug(f"Starting: {operation}")
        yield
        logger.debug(f"Completed: {operation}")
    except Exception as e:
        logger.error(f"Failed: {operation} - {str(e)}")
        raise


def safe_get_nested(data: dict, path: str, default: Any = None) -> Any:
    """Safely get a nested dictionary value using dot notation."""
    try:
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
    except (AttributeError, TypeError, KeyError):
        return default


def validate_deployment_id(deployment_id: str) -> bool:
    """Validate deployment ID format."""
    if not deployment_id:
        return False
    
    # Basic validation - deployment IDs are typically UUIDs or alphanumeric strings
    if len(deployment_id) < 8:
        return False
        
    # Check if it contains only valid characters (alphanumeric, hyphens, underscores)
    return all(c.isalnum() or c in ['-', '_'] for c in deployment_id)


def validate_token_format(token: str) -> bool:
    """Validate API token format."""
    if not token:
        return False
    
    # Basic validation - tokens are typically at least 20 characters
    if len(token) < 20:
        return False
        
    # Check if it looks like a valid token (alphanumeric and common special chars)
    return all(c.isalnum() or c in ['-', '_', '.'] for c in token)


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes == 0:
        return "0 B"
    
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(units) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {units[i]}"


def chunk_iterator(iterator: Iterator[Any], chunk_size: int):
    """Yield chunks of items from an iterator."""
    chunk = []
    for item in iterator:
        chunk.append(item)
        if len(chunk) >= chunk_size:
            yield chunk
            chunk = []
    
    # Yield remaining items
    if chunk:
        yield chunk


def mask_sensitive_data(text: str, keywords: list = None) -> str:
    """Mask sensitive data in text for logging."""
    if keywords is None:
        keywords = ['token', 'password', 'secret', 'key', 'auth']
    
    masked_text = text
    for keyword in keywords:
        if keyword.lower() in text.lower():
            # Simple masking - replace middle characters
            if len(text) > 8:
                masked_text = f"{text[:4]}{'*' * (len(text) - 8)}{text[-4:]}"
            else:
                masked_text = '*' * len(text)
            break
    
    return masked_text