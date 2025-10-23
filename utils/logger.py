"""Logging configuration for the application"""

import logging
import sys
from pathlib import Path
from logging.handlers import TimedRotatingFileHandler


def setup_logger(name: str = __name__, log_file: str = "app.log", level=logging.INFO):
    """
    Setup logger with file and console handlers
    
    Daily log rotation, keeps 7 days of logs
    
    Args:
        name: Logger name
        log_file: Log file name
        level: Logging level
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # File handler with daily rotation (keep 7 days)
    file_handler = TimedRotatingFileHandler(
        log_dir / log_file,
        when='midnight',
        interval=1,
        backupCount=7,
        encoding='utf-8'
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str = __name__):
    """
    Get or create a logger instance
    
    Args:
        name: Logger name
    
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logger(name)
    return logger

