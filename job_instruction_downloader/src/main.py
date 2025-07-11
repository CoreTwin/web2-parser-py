"""
Main entry point for the Job Instruction Downloader application.
"""

import sys
import logging
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from job_instruction_downloader.src.utils.logger import setup_logging
from job_instruction_downloader.src.utils.config import ConfigManager


def main():
    """Main application entry point."""
    try:
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Job Instruction Downloader")
        
        config_manager = ConfigManager()
        config = config_manager.load_config()
        
        from job_instruction_downloader.src.gui.main_window import MainWindow
        
        try:
            from PyQt6.QtWidgets import QApplication
            gui_framework = "PyQt6"
        except ImportError:
            try:
                from PySide6.QtWidgets import QApplication
                gui_framework = "PySide6"
            except ImportError:
                logger.error("Neither PyQt6 nor PySide6 is available. Please install one of them.")
                return 1
        
        logger.info(f"Using {gui_framework} for GUI")
        
        app = QApplication(sys.argv)
        app.setApplicationName("Job Instruction Downloader")
        app.setApplicationVersion("1.0.0")
        
        main_window = MainWindow(config)
        main_window.show()
        
        return app.exec()
        
    except Exception as e:
        logging.error(f"Application failed to start: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
