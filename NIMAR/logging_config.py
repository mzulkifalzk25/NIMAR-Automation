"""
Logging configuration for NIMAR Automation.

This module sets up file and console logging with date-time based filenames.
"""
import os
import logging
from datetime import datetime
from pathlib import Path


def setup_logging(log_level: str = "INFO") -> str:
    """
    Set up logging configuration with file and console handlers.
    
    Creates a logs directory in the project root and saves logs with
    date-time based filenames.
    
    Args:
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        str: Path to the log file that was created
    """
    # Get project root (parent of NIMAR folder)
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_file_dir)
    logs_dir = os.path.join(project_root, "logs")
    
    # Create logs directory if it doesn't exist
    os.makedirs(logs_dir, exist_ok=True)
    
    # Generate log filename with date and time
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"log_{timestamp}.log"
    log_filepath = os.path.join(logs_dir, log_filename)
    
    # Convert log level string to logging level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Remove existing handlers to avoid duplicates
    root_logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s - %(message)s'
    )
    
    # File handler - logs everything with detailed format
    file_handler = logging.FileHandler(log_filepath, encoding='utf-8')
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(detailed_formatter)
    root_logger.addHandler(file_handler)
    
    # Console handler - logs to console with simpler format
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Log the log file location
    logging.info(f"Logging initialized. Log file: {log_filepath}")
    
    return log_filepath

