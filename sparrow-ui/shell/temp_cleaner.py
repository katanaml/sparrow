import os
import time
import shutil
import tempfile
import threading
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("temp_cleaner")


class GradioTempCleaner:
    """
    Class to periodically clean Gradio temporary files.
    """

    def __init__(self, max_age_hours=1, check_interval_minutes=30, remove_all=False):
        """
        Initialize the temp cleaner.

        Args:
            max_age_hours: Maximum age of files to keep (in hours)
            check_interval_minutes: How often to check for old files (in minutes)
            remove_all: If True, remove all files regardless of age
        """
        self.max_age_seconds = max_age_hours * 3600
        self.check_interval_seconds = check_interval_minutes * 60
        self.remove_all = remove_all
        self.stop_event = threading.Event()
        self.thread = None

        # Get Gradio's temp directory
        self.temp_dir = self._get_gradio_temp_dir()
        logger.info(f"Monitoring Gradio temp directory: {self.temp_dir}")

    def _get_gradio_temp_dir(self):
        """Determine Gradio's temporary directory"""
        # Gradio uses the system's temp directory + 'gradio'
        return Path(tempfile.gettempdir()) / "gradio"

    def clean_temp_files(self, remove_all=False):
        """
        Clean temporary files and folders

        Args:
            remove_all: If True, remove all files and folders regardless of age.
                       If False, only remove items older than max_age_seconds
        """
        if not self.temp_dir.exists():
            logger.warning(f"Temp directory does not exist: {self.temp_dir}")
            return

        now = time.time()
        files_removed = 0
        dirs_removed = 0

        try:
            # Get a list of all immediate child directories in the temp folder
            child_dirs = [d for d in self.temp_dir.iterdir() if d.is_dir()]

            # Check each directory's age
            for dir_path in child_dirs:
                try:
                    dir_age = now - os.path.getmtime(dir_path)

                    # If directory is old enough or we're removing everything
                    if remove_all or dir_age > self.max_age_seconds:
                        # Remove the entire directory tree
                        shutil.rmtree(dir_path, ignore_errors=True)
                        dirs_removed += 1
                        logger.debug(f"Removed directory: {dir_path}")
                except (PermissionError, OSError) as e:
                    logger.error(f"Error checking/removing directory {dir_path}: {e}")

            # Handle individual files in the root of the temp directory
            root_files = [f for f in self.temp_dir.iterdir() if f.is_file()]
            for file_path in root_files:
                try:
                    file_age = now - os.path.getmtime(file_path)
                    if remove_all or file_age > self.max_age_seconds:
                        os.remove(file_path)
                        files_removed += 1
                except (PermissionError, OSError) as e:
                    logger.error(f"Error removing file {file_path}: {e}")

            if files_removed > 0 or dirs_removed > 0:
                logger.info(f"Cleaned up {files_removed} files and {dirs_removed} directories")

        except Exception as e:
            logger.error(f"Error during temp file cleanup: {e}")

    def start(self):
        """Start the periodic cleaning thread"""
        if self.thread is not None and self.thread.is_alive():
            logger.warning("Cleaner thread already running")
            return

        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._cleaning_loop,
            name="GradioTempCleaner",
            daemon=True
        )
        self.thread.start()
        logger.info(
            f"Started temp file cleaning thread (interval: {self.check_interval_seconds // 60} min, max age: {self.max_age_seconds // 3600} hours)")

    def _cleaning_loop(self):
        """Main loop for periodic cleaning"""
        while not self.stop_event.is_set():
            self.clean_temp_files(remove_all=self.remove_all)

            # Wait for the next interval or until stopped
            self.stop_event.wait(self.check_interval_seconds)

    def stop(self):
        """Stop the periodic cleaning thread"""
        if self.thread is not None and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=5.0)
            logger.info("Stopped temp file cleaning thread")