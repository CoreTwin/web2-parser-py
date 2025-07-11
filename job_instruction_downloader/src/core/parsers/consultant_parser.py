"""
Consultant.ru specific parser implementation.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from .base_parser import BaseParser
from ...models.job_instruction import JobInstruction
from ...models.department import Department


class ConsultantParser(BaseParser):
    """Parser for Consultant.ru documents."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Consultant.ru parser.

        Args:
            config: Site configuration dictionary.
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)

    def extract_documents(self, driver: webdriver.Chrome, department: Department) -> List[JobInstruction]:
        """Extract job instruction documents for a department from Consultant.ru.

        Args:
            driver: Selenium WebDriver instance.
            department: Department to extract documents for.

        Returns:
            List of extracted job instructions.
        """
        documents = []
        selectors = self.get_selectors()

        try:
            start_url = self.site_config.get("navigation", {}).get("start_url", "")
            base_url = self.site_config.get("site_info", {}).get("base_url", "")

            if not start_url or not base_url:
                self.logger.warning(f"Missing URL configuration for {department.name}")
                return []

            full_url = f"{base_url}{start_url}"
            self.logger.info(f"Navigating to: {full_url}")
            driver.get(full_url)

            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            document_selector = selectors.get("document_links", "[devinid]")
            self.logger.info(f"Looking for documents with selector: {document_selector}")

            document_elements = driver.find_elements(By.CSS_SELECTOR, document_selector)
            self.logger.info(f"Found {len(document_elements)} potential document elements")

            for i, element in enumerate(document_elements):
                try:
                    title = self._extract_title(driver, element)
                    url = self._extract_url(element, base_url)

                    if title and url:
                        processed_title = self.process_title(title)
                        job_instruction = JobInstruction(
                            title=processed_title,
                            department=department.name,
                            url=url
                        )
                        documents.append(job_instruction)
                        self.logger.debug(f"Extracted document {i+1}: {processed_title}")

                except Exception as e:
                    self.logger.warning(f"Failed to extract document {i+1}: {e}")
                    continue

            self.logger.info(f"Successfully extracted {len(documents)} documents for {department.name}")
            return documents

        except Exception as e:
            self.logger.error(f"Failed to extract documents for {department.name}: {e}")
            return []

    def _extract_title(self, driver: webdriver.Chrome, element) -> str:
        """Extract document title from element.

        Args:
            driver: Selenium WebDriver instance.
            element: Web element containing document information.

        Returns:
            Document title or empty string if not found.
        """
        try:
            selectors = self.get_selectors()
            title_selector = selectors.get("document_title", "h1, .document-title")

            try:
                title_element = element.find_element(By.CSS_SELECTOR, title_selector)
                text = title_element.text
                return text.strip() if text else ""
            except NoSuchElementException:
                try:
                    title_element = driver.find_element(By.CSS_SELECTOR, title_selector)
                    text = title_element.text
                    return text.strip() if text else ""
                except NoSuchElementException:
                    return element.text.strip() if element.text else ""

        except Exception as e:
            self.logger.warning(f"Failed to extract title: {e}")
            return ""

    def _extract_url(self, element, base_url: str) -> str:
        """Extract document URL from element.

        Args:
            element: Web element containing document link.
            base_url: Base URL for the site.

        Returns:
            Full document URL or empty string if not found.
        """
        try:
            href = element.get_attribute("href")
            if href and isinstance(href, str):
                if href.startswith("http"):
                    return str(href)
                elif href.startswith("/"):
                    return f"{base_url}{href}"
                else:
                    return f"{base_url}/{href}"

            onclick = element.get_attribute("onclick")
            if onclick and isinstance(onclick, str) and "location.href" in onclick:
                import re
                url_match = re.search(r"location\.href\s*=\s*['\"]([^'\"]+)['\"]", onclick)
                if url_match:
                    url = url_match.group(1)
                    if isinstance(url, str):
                        if url.startswith("/"):
                            return f"{base_url}{url}"
                        return url

            return ""

        except Exception as e:
            self.logger.warning(f"Failed to extract URL: {e}")
            return ""

    def validate_document(self, file_path: str) -> bool:
        """Validate downloaded document from Consultant.ru.

        Args:
            file_path: Path to the downloaded file.

        Returns:
            True if document is valid, False otherwise.
        """
        try:
            path = Path(file_path)

            if not path.exists():
                self.logger.error(f"File does not exist: {file_path}")
                return False

            validation_config = self.get_validation_config()

            file_size = path.stat().st_size
            min_size = validation_config.get("min_size", 30000)
            max_size = validation_config.get("max_size", 10485760)

            if file_size < min_size:
                self.logger.error(f"File too small: {file_size} < {min_size}")
                return False

            if file_size > max_size:
                self.logger.error(f"File too large: {file_size} > {max_size}")
                return False

            expected_types = self.get_download_config().get("expected_file_types", [".docx", ".doc"])
            if expected_types and path.suffix.lower() not in expected_types:
                self.logger.error(f"Invalid file type: {path.suffix}")
                return False

            if validation_config.get("check_content", False):
                return self._validate_content(file_path)

            return True

        except Exception as e:
            self.logger.error(f"Validation error for {file_path}: {e}")
            return False

    def _validate_content(self, file_path: str) -> bool:
        """Validate document content.

        Args:
            file_path: Path to the downloaded file.

        Returns:
            True if content is valid, False otherwise.
        """
        try:
            path = Path(file_path)

            if path.suffix.lower() in [".docx", ".doc"]:
                with open(file_path, 'rb') as f:
                    header = f.read(8)
                    if path.suffix.lower() == ".docx":
                        return header.startswith(b'PK')
                    elif path.suffix.lower() == ".doc":
                        return header.startswith(b'\xd0\xcf\x11\xe0')

            return True

        except Exception as e:
            self.logger.warning(f"Content validation failed for {file_path}: {e}")
            return False
