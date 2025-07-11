"""
Core downloader functionality for job instruction documents.
"""

import logging
import time
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException

from ..models.job_instruction import JobInstruction
from ..models.department import Department
from ..utils.config import ConfigManager
from ..utils.error_handler import EnhancedErrorHandler
from ..utils.structured_logger import StructuredLogger
from .parsers.consultant_parser import ConsultantParser
from .parsers.base_parser import BaseParser
from .validator import DocumentValidator
from .cloud_manager import GoogleDriveManager


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

        self.parser: Optional[BaseParser] = None
        self.validator: Optional[DocumentValidator] = None
        self.cloud_manager: Optional[GoogleDriveManager] = None
        self.error_handler = EnhancedErrorHandler(config)
        self.structured_logger = StructuredLogger(config)

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
        status_callback: Optional[Callable[[str], None]] = None,
        upload_to_cloud: bool = True
    ) -> bool:
        """Download documents for specified departments.

        Args:
            departments: List of departments to process.
            site_name: Name of the site configuration to use.
            progress_callback: Callback for progress updates (completed, total).
            status_callback: Callback for status messages.
            upload_to_cloud: Whether to upload documents to cloud storage.

        Returns:
            True if successful, False otherwise.
        """
        self.progress_callback = progress_callback
        self.status_callback = status_callback

        try:
            with self.structured_logger.timed_operation(
                self.logger, "info", "Document download process", operation="download_process"
            ):
                site_config = self.config_manager.load_site_config(site_name)
                if not site_config:
                    self.logger.error(f"Failed to load site configuration for {site_name}")
                    return False

                self.parser = self._create_parser(site_name, site_config)
                if not self.parser:
                    self.logger.error(f"Failed to create parser for {site_name}")
                    return False

                self.validator = DocumentValidator(site_config)

                if not self.setup_driver():
                    return False

                if upload_to_cloud and not self.setup_cloud_storage():
                    self.logger.warning("Cloud storage setup failed, continuing without cloud upload")
                    upload_to_cloud = False

                self.total_documents = sum(dept.total_documents for dept in departments)
                self.completed_documents = 0
                self.failed_documents = 0
                self.start_time = time.time()

                self._update_status(f"Начинаем загрузку {self.total_documents} документов")

                for department in departments:
                    if not department.enabled:
                        continue

                    self._update_status(f"Обрабатываем отдел: {department.name}")
                    self.structured_logger.log_operation(
                        self.logger, "info", f"Processing department: {department.name}",
                        operation="process_department", department=department.name
                    )

                    success = self._process_department(department, site_config, upload_to_cloud)
                    if not success:
                        self.structured_logger.log_operation(
                            self.logger, "warning", f"Failed to process department: {department.name}",
                            operation="process_department", department=department.name
                        )

                self._update_status("Загрузка завершена")
                self.structured_logger.log_operation(
                    self.logger, "info",
                    f"Download completed. Success: {self.completed_documents}, Failed: {self.failed_documents}",
                    operation="download_complete"
                )

                return True

        except Exception as e:
            self.structured_logger.log_operation(
                self.logger, "error", f"Download process failed: {e}",
                operation="download_process"
            )
            self._update_status(f"Ошибка: {e}")
            return False

        finally:
            self.cleanup()

    def _process_department(self, department: Department, site_config: Dict[str, Any],
                            upload_to_cloud: bool = True) -> bool:
        """Process a single department.

        Args:
            department: Department to process.
            site_config: Site configuration.
            upload_to_cloud: Whether to upload documents to cloud storage.

        Returns:
            True if successful, False otherwise.
        """
        try:
            if not department.job_instructions:
                if not self.driver or not self.parser:
                    self.logger.warning(f"Cannot extract job instructions for department: {department.name}")
                    return False

                department.job_instructions = self.extract_department_documents(department)

                if not department.job_instructions:
                    self.structured_logger.log_operation(
                        self.logger, "warning", f"No job instructions found for department: {department.name}",
                        operation="process_department", department=department.name
                    )
                    return True

            with self.structured_logger.timed_operation(
                self.logger, "info", f"Processing department {department.name}",
                operation="process_department", department=department.name
            ):
                for job_instruction in department.job_instructions:
                    try:
                        self._update_status(f"Загружаем: {job_instruction.title}")

                        download_result = self.error_handler.retry_with_backoff(
                            self._download_single_document,
                            job_instruction, site_config
                        )

                        if download_result[0]:  # Success
                            job_instruction.status = "completed"
                            job_instruction.local_path = download_result[1]

                            if upload_to_cloud and self.cloud_manager and job_instruction.local_path:
                                cloud_success = self.upload_to_cloud(
                                    job_instruction.local_path,
                                    department.name,
                                    job_instruction.title
                                )

                                if cloud_success:
                                    job_instruction.cloud_status = "uploaded"
                                    self.structured_logger.log_operation(
                                        self.logger, "info", f"Uploaded to cloud: {job_instruction.title}",
                                        operation="cloud_upload", department=department.name,
                                        document_title=job_instruction.title
                                    )
                                else:
                                    job_instruction.cloud_status = "failed"
                                    self.structured_logger.log_operation(
                                        self.logger, "error", f"Failed to upload to cloud: {job_instruction.title}",
                                        operation="cloud_upload", department=department.name,
                                        document_title=job_instruction.title
                                    )

                            self.completed_documents += 1
                            self.structured_logger.log_operation(
                                self.logger, "info", f"Successfully downloaded: {job_instruction.title}",
                                operation="download_document", department=department.name,
                                document_title=job_instruction.title
                            )
                        else:
                            job_instruction.status = "failed"
                            self.failed_documents += 1
                            self.structured_logger.log_operation(
                                self.logger, "error", f"Failed to download: {job_instruction.title}",
                                operation="download_document", department=department.name,
                                document_title=job_instruction.title
                            )

                        if self.progress_callback:
                            self.progress_callback(self.completed_documents, self.total_documents)

                        delay = site_config.get("site_config", {}).get(
                            "rate_limiting", {}
                        ).get("delay_between_requests", 3)
                        time.sleep(delay)

                    except Exception as e:
                        self.structured_logger.log_operation(
                            self.logger, "error", f"Error processing document {job_instruction.title}: {e}",
                            operation="download_document", department=department.name,
                            document_title=job_instruction.title
                        )
                        job_instruction.status = "failed"
                        job_instruction.error_message = str(e)
                        self.failed_documents += 1

                return True

        except Exception as e:
            self.structured_logger.log_operation(
                self.logger, "error", f"Error processing department {department.name}: {e}",
                operation="process_department", department=department.name
            )
            return False

    def _download_single_document(self, job_instruction: JobInstruction,
                                  site_config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Download a single document.

        Args:
            job_instruction: Job instruction to download.
            site_config: Site configuration.

        Returns:
            Tuple of (success, file_path). If success is False, file_path will be None.
        """
        try:
            if not self.driver:
                self.logger.error("WebDriver not initialized")
                return False, None

            with self.structured_logger.timed_operation(
                self.logger, "info", f"Downloading document: {job_instruction.title}",
                operation="download_document", document_title=job_instruction.title
            ):
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

                    download_timeout = site_config.get("site_config", {}).get(
                        "document_extraction", {}
                    ).get("download_timeout", 30)

                    time.sleep(5)  # Initial wait

                    download_dir = Path(self.config.get("download", {}).get("temp_directory", "downloads"))
                    download_dir.mkdir(parents=True, exist_ok=True)

                    max_wait_time = time.time() + download_timeout
                    downloaded_file = None

                    while time.time() < max_wait_time:
                        files = list(download_dir.glob("*"))
                        if files:
                            downloaded_file = max(files, key=lambda f: f.stat().st_mtime)

                            if (not downloaded_file.name.endswith('.crdownload') and
                                    not downloaded_file.name.endswith('.part')):
                                break

                        time.sleep(1)

                    if not downloaded_file:
                        self.structured_logger.log_operation(
                            self.logger, "error", f"Download timeout for: {job_instruction.title}",
                            operation="download_document", document_title=job_instruction.title
                        )
                        return False, None

                    if self.validator and not self.validator.validate_document_structure(str(downloaded_file)):
                        self.structured_logger.log_operation(
                            self.logger, "error", f"Downloaded file validation failed: {job_instruction.title}",
                            operation="validate_document", document_title=job_instruction.title
                        )
                        return False, None

                    clean_filename = self._generate_filename(job_instruction.title)
                    new_file_path = download_dir / clean_filename
                    downloaded_file.rename(new_file_path)

                    self.structured_logger.log_operation(
                        self.logger, "info", f"Successfully downloaded and validated: {job_instruction.title}",
                        operation="download_document", document_title=job_instruction.title
                    )

                    return True, str(new_file_path)

                except TimeoutException:
                    self.structured_logger.log_operation(
                        self.logger, "error", f"Download button not found for: {job_instruction.title}",
                        operation="download_document", document_title=job_instruction.title
                    )
                    return False, None

        except Exception as e:
            self.structured_logger.log_operation(
                self.logger, "error", f"Error downloading document: {e}",
                operation="download_document", document_title=job_instruction.title
            )
            return False, None

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

    def _create_parser(self, site_name: str, site_config: Dict[str, Any]) -> Optional[BaseParser]:
        """Create appropriate parser for the site.

        Args:
            site_name: Name of the site.
            site_config: Site configuration.

        Returns:
            Parser instance or None if creation failed.
        """
        try:
            if site_name == "consultant_ru":
                return ConsultantParser(site_config)
            else:
                self.logger.error(f"No parser available for site: {site_name}")
                return None

        except Exception as e:
            self.logger.error(f"Failed to create parser for {site_name}: {e}")
            return None

    def setup_cloud_storage(self) -> bool:
        """Setup cloud storage integration.

        Returns:
            True if setup successful, False otherwise.
        """
        try:
            cloud_config = self.config.get("cloud_storage", {})
            provider = cloud_config.get("default_provider", "google_drive")

            if provider == "google_drive":
                self.cloud_manager = GoogleDriveManager(self.config)
                return self.cloud_manager.authenticate()
            else:
                self.logger.warning(f"Unsupported cloud provider: {provider}")
                return False

        except Exception as e:
            self.structured_logger.log_operation(
                self.logger, "error", f"Failed to setup cloud storage: {e}",
                operation="setup_cloud_storage"
            )
            return False

    def upload_to_cloud(self, file_path: str, department_name: str,
                        document_title: str) -> bool:
        """Upload file to cloud storage with proper folder organization.

        Args:
            file_path: Path to the file to upload.
            department_name: Name of the department for folder organization.
            document_title: Title of the document for naming.

        Returns:
            True if upload successful, False otherwise.
        """
        if not self.cloud_manager:
            self.logger.warning("Cloud manager not initialized")
            return False

        try:
            with self.structured_logger.timed_operation(
                self.logger, "info", f"Uploading to cloud storage: {document_title}",
                operation="cloud_upload", department=department_name,
                document_title=document_title
            ):
                folder_id = self._get_or_create_department_folder(department_name)
                if not folder_id:
                    return False

                clean_filename = self._generate_filename(document_title)

                cloud_config = self.config.get("cloud_storage", {})
                if cloud_config.get("check_duplicates", True):
                    if self.cloud_manager.check_duplicate(clean_filename, folder_id):
                        self.structured_logger.log_operation(
                            self.logger, "info", f"File already exists in cloud storage: {clean_filename}",
                            operation="cloud_upload", department=department_name,
                            document_title=document_title
                        )
                        return True

                file_id = self.error_handler.retry_with_backoff(
                    self.cloud_manager.upload_file,
                    file_path, folder_id, clean_filename
                )

                if file_id:
                    self.structured_logger.log_operation(
                        self.logger, "info", "Successfully uploaded to cloud storage",
                        operation="cloud_upload", department=department_name,
                        document_title=document_title
                    )

                    if cloud_config.get("cleanup_after_upload", False):
                        try:
                            Path(file_path).unlink()
                            self.logger.info(f"Cleaned up local file: {file_path}")
                        except Exception as e:
                            self.logger.warning(f"Failed to cleanup local file: {e}")

                    return True
                else:
                    return False

        except Exception as e:
            self.structured_logger.log_operation(
                self.logger, "error", f"Cloud upload failed: {e}",
                operation="cloud_upload", department=department_name,
                document_title=document_title
            )
            return False

    def _get_or_create_department_folder(self, department_name: str) -> Optional[str]:
        """Get or create department folder in cloud storage.

        Args:
            department_name: Name of the department.

        Returns:
            Folder ID if successful, None otherwise.
        """
        if not self.cloud_manager:
            return None

        try:
            cloud_config = self.config.get("cloud_storage", {})
            root_folder_name = cloud_config.get("root_folder_name", "Job Instructions")

            root_folder_id = self.cloud_manager.get_or_create_folder(root_folder_name)
            if not root_folder_id:
                self.logger.error("Failed to create root folder")
                return None

            department_folder_id = self.cloud_manager.get_or_create_folder(
                department_name, root_folder_id
            )

            return department_folder_id

        except Exception as e:
            self.logger.error(f"Failed to get/create department folder: {e}")
            return None

    def _generate_filename(self, document_title: str) -> str:
        """Generate clean filename from document title.

        Args:
            document_title: Original document title.

        Returns:
            Clean filename with .docx extension.
        """
        clean_title = re.sub(r'[^\w\s-]', '', document_title)
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        clean_title = clean_title.strip('-')

        if len(clean_title) > 100:
            clean_title = clean_title[:100]

        return f"{clean_title}.docx"

    def extract_department_documents(self, department: Department) -> List[JobInstruction]:
        """Extract documents for a department using the configured parser.

        Args:
            department: Department to extract documents for.

        Returns:
            List of extracted job instructions.
        """
        if not self.parser or not self.driver:
            self.logger.error("Parser or driver not initialized")
            return []

        try:
            return self.parser.extract_documents(self.driver, department)
        except Exception as e:
            self.structured_logger.log_operation(
                self.logger, "error", f"Failed to extract documents for {department.name}: {e}",
                operation="extract_documents", department=department.name
            )
            return []
