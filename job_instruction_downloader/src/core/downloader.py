"""
Core downloader functionality for job instruction documents.
"""

import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException

from ..models.job_instruction import JobInstruction
from ..models.department import Department
from ..utils.config import ConfigManager


class DocumentDownloader:
    """Main downloader class for job instruction documents."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the downloader.

        Args:
            config: Application configuration dictionary.
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.driver: Optional[webdriver.Chrome] = None
        self.config_manager = ConfigManager()

        self.total_documents = 0
        self.completed_documents = 0
        self.failed_documents = 0
        self.start_time: Optional[float] = None

        self.progress_callback: Optional[Callable[[int, int], None]] = None
        self.status_callback: Optional[Callable[[str], None]] = None

    def setup_driver(self) -> bool:
        """Setup Selenium WebDriver.

        Returns:
            True if successful, False otherwise.
        """
        try:
            selenium_config = self.config.get("selenium", {})

            chrome_options = ChromeOptions()

            if selenium_config.get("headless", True):
                chrome_options.add_argument("--headless")

            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-images")
            chrome_options.add_argument("--disable-javascript")
            chrome_options.add_experimental_option("useAutomationExtension", False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

            window_size = selenium_config.get("window_size", [1920, 1080])
            chrome_options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")

            download_dir = str(Path(self.config.get("download", {}).get("temp_directory", "downloads")).absolute())
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)

            self.driver = webdriver.Chrome(options=chrome_options)

            page_load_timeout = selenium_config.get("page_load_timeout", 30)
            implicit_wait = selenium_config.get("implicit_wait", 10)

            self.driver.set_page_load_timeout(page_load_timeout)
            self.driver.implicitly_wait(implicit_wait)

            self.logger.info("WebDriver initialized successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to setup WebDriver: {e}")
            return False

    def download_documents(
        self,
        departments: List[Department],
        site_name: str = "consultant_ru",
        progress_callback: Optional[Callable[[int, int], None]] = None,
        status_callback: Optional[Callable[[str], None]] = None
    ) -> bool:
        """Download documents for specified departments.

        Args:
            departments: List of departments to process.
            site_name: Name of the site configuration to use.
            progress_callback: Callback for progress updates (completed, total).
            status_callback: Callback for status messages.

        Returns:
            True if successful, False otherwise.
        """
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        try:
            site_config = self.config_manager.load_site_config(site_name)
            if not site_config:
                self.logger.error(f"Failed to load site configuration for {site_name}")
                return False

            if not self.setup_driver():
                return False

            self.total_documents = sum(dept.total_documents for dept in departments)
            self.completed_documents = 0
            self.failed_documents = 0
            self.start_time = time.time()

            self._update_status(f"Начинаем загрузку {self.total_documents} документов")

            for department in departments:
                if not department.enabled:
                    continue

                self._update_status(f"Обрабатываем отдел: {department.name}")
                self.logger.info(f"Processing department: {department.name}")

                success = self._process_department(department, site_config)
                if not success:
                    self.logger.warning(f"Failed to process department: {department.name}")

            self._update_status("Загрузка завершена")
            self.logger.info(
                f"Download completed. Success: {self.completed_documents}, Failed: {self.failed_documents}"
            )

            return True

        except Exception as e:
            self.logger.error(f"Download process failed: {e}")
            self._update_status(f"Ошибка: {e}")
            return False

        finally:
            self.cleanup()

    def _process_department(self, department: Department, site_config: Dict[str, Any]) -> bool:
        """Process a single department.

        Args:
            department: Department to process.
            site_config: Site configuration.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if not department.job_instructions:
                self.logger.warning(f"No job instructions found for department: {department.name}")
                return True

            for job_instruction in department.job_instructions:
                try:
                    self._update_status(f"Загружаем: {job_instruction.title}")

                    success = self._download_single_document(job_instruction, site_config)

                    if success:
                        job_instruction.status = "completed"
                        self.completed_documents += 1
                        self.logger.info(f"Successfully downloaded: {job_instruction.title}")
                    else:
                        job_instruction.status = "failed"
                        self.failed_documents += 1
                        self.logger.error(f"Failed to download: {job_instruction.title}")

                    if self.progress_callback:
                        self.progress_callback(self.completed_documents, self.total_documents)

                    delay = site_config.get("site_config", {}).get("rate_limiting", {}).get("delay_between_requests", 3)
                    time.sleep(delay)

                except Exception as e:
                    self.logger.error(f"Error processing document {job_instruction.title}: {e}")
                    job_instruction.status = "failed"
                    job_instruction.error_message = str(e)
                    self.failed_documents += 1

            return True

        except Exception as e:
            self.logger.error(f"Error processing department {department.name}: {e}")
            return False

    def _download_single_document(self, job_instruction: JobInstruction, site_config: Dict[str, Any]) -> bool:
        """Download a single document.

        Args:
            job_instruction: Job instruction to download.
            site_config: Site configuration.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if not self.driver:
                self.logger.error("WebDriver not initialized")
                return False

            self.driver.get(job_instruction.url)

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            download_selector = site_config.get("site_config", {}).get(
                "document_extraction", {}
            ).get("download_button_selector", "[devinid='14']")

            try:
                download_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, download_selector))
                )
                download_button.click()

                time.sleep(5)  # Basic wait - could be improved with file monitoring

                return True

            except TimeoutException:
                self.logger.error(f"Download button not found for: {job_instruction.title}")
                return False

        except Exception as e:
            self.logger.error(f"Error downloading document: {e}")
            return False

    def _update_status(self, message: str):
        """Update status via callback.

        Args:
            message: Status message.
        """
        if self.status_callback:
            self.status_callback(message)

    def cleanup(self):
        """Cleanup resources."""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None

    def get_download_statistics(self) -> Dict[str, Any]:
        """Get download statistics.

        Returns:
            Dictionary with download statistics.
        """
        elapsed_time = time.time() - self.start_time if self.start_time else 0

        return {
            "total_documents": self.total_documents,
            "completed_documents": self.completed_documents,
            "failed_documents": self.failed_documents,
            "elapsed_time": elapsed_time,
            "download_rate": self.completed_documents / (elapsed_time / 60) if elapsed_time > 0 else 0
        }
