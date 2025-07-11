"""
Integration tests for DocumentDownloader with Phase 2 functionality.
"""

import pytest
from unittest.mock import patch

from job_instruction_downloader.src.core.downloader import DocumentDownloader


@pytest.fixture
def downloader_config():
    """Configuration for downloader tests."""
    return {
        "download": {
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 0.1,
            "temp_directory": "downloads"
        },
        "cloud_storage": {
            "default_provider": "google_drive",
            "create_folders_automatically": True,
            "check_duplicates": True,
            "credentials_path": "config/credentials.json",
            "root_folder_name": "Test Job Instructions"
        },
        "error_handling": {
            "retry_attempts": 3,
            "retry_delay": 0.1,
            "exponential_backoff": True
        },
        "logging": {
            "file_path": "logs/test.log",
            "structured_logging": True,
            "level": "INFO"
        }
    }


class TestDocumentDownloaderIntegration:
    """Integration tests for DocumentDownloader with Phase 2 features."""

    def test_downloader_initialization(self, downloader_config):
        """Test downloader initialization with Phase 2 components."""
        downloader = DocumentDownloader(downloader_config)

        assert downloader.error_handler is not None
        assert downloader.structured_logger is not None
        assert downloader.cloud_manager is None

    def test_filename_generation(self, downloader_config):
        """Test filename generation from document titles."""
        downloader = DocumentDownloader(downloader_config)

        test_cases = [
            ("Должностная инструкция менеджера", "Должностная-инструкция-менеджера.docx"),
            ("Test Document with Special Characters!@#", "Test-Document-with-Special-Characters.docx"),
            ("Very Long Document Title That Exceeds The Maximum Length Limit",
             "Very-Long-Document-Title-That-Exceeds-The-Maximum-Length-Limit-And-Should-Be-Truncated.docx")
        ]

        for input_title, expected_filename in test_cases:
            result = downloader._generate_filename(input_title)
            assert result.endswith(".docx")
            assert len(result) <= 104

    def test_cloud_storage_setup_without_credentials(self, downloader_config):
        """Test cloud storage setup without credentials."""
        downloader = DocumentDownloader(downloader_config)

        result = downloader.setup_cloud_storage()

        assert result is False
        assert downloader.cloud_manager is not None

    @patch('job_instruction_downloader.src.core.cloud_manager.GoogleDriveManager')
    def test_upload_to_cloud_without_manager(self, mock_cloud_manager_class, downloader_config, tmp_path):
        """Test upload to cloud without initialized manager."""
        downloader = DocumentDownloader(downloader_config)

        test_file = tmp_path / "test.docx"
        test_file.write_text("test content")

        result = downloader.upload_to_cloud(
            str(test_file), "TEST_DEPARTMENT", "Test Document"
        )

        assert result is False
