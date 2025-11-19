"""Teletools Utilities Module.

Common utility functions for telecom data processing.
"""

import gzip
import logging
import zipfile
from pathlib import Path
from typing import Union

def inspect_file(file: Union[str, Path], nrows: int = 5, encoding: str = "utf8") -> None:
    """Inspect the first few lines of a file.

    Supports regular text files, gzipped files (.gz), and zip archives (.zip).
    For zip files, inspects the first file found in the archive.

    Args:
        file: Path to the file to inspect
        nrows: Number of lines to display (default: 5)
        encoding: Text encoding to use (default: 'utf8')
        
    Raises:
        FileNotFoundError: If the file does not exist
        Exception: For other file reading errors
        
    Example:
        >>> inspect_file('data.csv.gz', nrows=10)
        >>> inspect_file('archive.zip', encoding='latin1')
    """
    file = Path(file)
    
    if not file.exists():
        print(f"Error: File '{file}' does not exist")
        return
    
    print(f"\n======== FILE: {file.name} ========")

    try:
        if file.suffix == ".gz":
            with gzip.open(file, "rt", encoding=encoding) as f:
                for _ in range(nrows):
                    line = f.readline()
                    if not line:
                        break
                    print(line.strip())
                    
        elif file.suffix == ".zip":
            with zipfile.ZipFile(file, "r") as zip_ref:
                file_names = zip_ref.namelist()
                if not file_names:
                    print("ZIP file is empty")
                    return

                first_file = file_names[0]
                print(f"Reading first file in ZIP: {first_file}")

                with zip_ref.open(first_file) as zip_file:
                    for _ in range(nrows):
                        line = zip_file.readline()
                        if not line:
                            break
                        print(line.decode(encoding).strip())
        else:
            with open(file, encoding=encoding) as f:
                for _ in range(nrows):
                    line = f.readline()
                    if not line:
                        break
                    print(line.strip())

    except Exception as e:
        print(f"Error reading file '{file}': {e}")

# Advanced logging configuration for console and file output
def setup_logger(log_file="log.log") -> logging.Logger:
    """Configure logger for console display and file logging.

    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Remove existing handlers to avoid duplication
    if logger.handlers:
        logger.handlers.clear()

    # Message format
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger