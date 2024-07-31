import logging
import logging.handlers
import os
from pathlib import Path

def setup_logging(
    log_dir: str = "logs",
    log_file: str = "app.log",
    max_bytes: int = 10*1024*1024,  # 10 MB
    backup_count: int = 5
):
    # Ensure the log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Log file path
    log_file_path = os.path.join(log_dir, log_file)
    
    # Create a rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path, maxBytes=max_bytes, backupCount=backup_count
    )
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)
    
    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Add handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info("Logging setup complete.")

# Example usage
if __name__ == "__main__":
    setup_logging()
    logging.info("This is an info message.")
    logging.debug("This is a debug message.")
    logging.error("This is an error message.")
