"""
Consultant.ru resource adapter implementation.
"""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from .base_resource_adapter import BaseResourceAdapter
from ...models.job_instruction import JobInstruction
from ...models.department import Department
from ..parsers.consultant_parser import ConsultantParser


class ConsultantAdapter(BaseResourceAdapter):
    """Resource adapter for Consultant.ru website."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the Consultant adapter.

        Args:
            config: Configuration dictionary for the adapter.
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        self.parser = ConsultantParser(config)

    def authenticate(self, credentials: Optional[Dict[str, Any]] = None) -> bool:
        """Authenticate with Consultant.ru.

        Args:
            credentials: Authentication credentials (not required for public access).

        Returns:
            True (Consultant.ru allows public access to documents).
        """
        return True

    def get_document_list(self, department: Department, filters: Optional[Dict[str, Any]] = None) -> List[JobInstruction]:
        """Get list of documents from Consultant.ru.

        Args:
            department: Department to get documents for.
            filters: Optional filters to apply.

        Returns:
            List of available documents.
        """
        try:
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                documents = self.parser.extract_documents(driver, department)
                self.logger.info(f"Extracted {len(documents)} documents for department {department.name}")
                return documents
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error getting document list: {e}")
            return []

    def download_document(self, document: JobInstruction, download_path: Path) -> bool:
        """Download a document from Consultant.ru.

        Args:
            document: Document to download.
            download_path: Path to save the document.

        Returns:
            True if download successful, False otherwise.
        """
        try:
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            import requests
            import time
            
            chrome_options = ChromeOptions()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            
            prefs = {
                "download.default_directory": str(download_path.parent),
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(document.url)
                time.sleep(2)
                
                export_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Экспорт в Word') or contains(@title, 'Word')]"))
                )
                export_button.click()
                
                time.sleep(5)
                
                if download_path.exists() and download_path.stat().st_size > 0:
                    self.logger.info(f"Successfully downloaded document: {document.title}")
                    return True
                else:
                    self.logger.warning(f"Download may have failed for: {document.title}")
                    return False
                    
            finally:
                driver.quit()
                
        except Exception as e:
            self.logger.error(f"Error downloading document {document.title}: {e}")
            return False

    def validate_document(self, file_path: Path) -> bool:
        """Validate a downloaded document.

        Args:
            file_path: Path to the downloaded file.

        Returns:
            True if document is valid, False otherwise.
        """
        return self.parser.validate_document(str(file_path))

    def get_metadata(self, document: JobInstruction) -> Dict[str, Any]:
        """Get metadata for a document.

        Args:
            document: Document to get metadata for.

        Returns:
            Dictionary containing document metadata.
        """
        metadata = {
            "source": "consultant.ru",
            "document_type": document.document_type,
            "department": document.department,
            "url": document.url,
            "title": document.title,
            "extraction_date": document.download_date.isoformat() if document.download_date else None,
            "file_extension": document.file_extension,
            "status": document.status
        }
        
        if document.metadata:
            metadata.update(document.metadata)
            
        return metadata
