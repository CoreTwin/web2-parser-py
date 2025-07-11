"""
Integration tests for Phase 2 functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch

from job_instruction_downloader.src.core.downloader import DocumentDownloader
from job_instruction_downloader.src.models.department import Department
from job_instruction_downloader.src.models.job_instruction import JobInstruction


@pytest.fixture
def integration_config():
    """Integration test configuration."""
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


@pytest.fixture
def test_department():
    """Test department fixture."""
    department = Department("TEST_DEPARTMENT", True, 2)
    department.job_instructions = [
        JobInstruction("Test Document 1", "TEST_DEPARTMENT", "http://example.com/doc1"),
        JobInstruction("Test Document 2", "TEST_DEPARTMENT", "http://example.com/doc2")
    ]
    return department


class TestPhase2Integration:
    """Integration tests for Phase 2 functionality."""

    def test_downloader_initialization_with_phase2_components(self, integration_config):
        """Test downloader initialization with Phase 2 components."""
        downloader = DocumentDownloader(integration_config)

        assert downloader.error_handler is not None
        assert downloader.structured_logger is not None
        assert downloader.cloud_manager is None  # Not initialized until setup

    @patch('job_instruction_downloader.src.core.cloud_manager.build')
    @patch('job_instruction_downloader.src.core.cloud_manager.Credentials')
    def test_cloud_storage_setup(self, mock_creds, mock_build, integration_config):
        """Test cloud storage setup."""
        downloader = DocumentDownloader(integration_config)

        mock_service = Mock()
        mock_build.return_value = mock_service

        with patch('job_instruction_downloader.src.core.cloud_manager.Path.exists', return_value=False):
            with patch('job_instruction_downloader.src.core.cloud_manager.InstalledAppFlow') as mock_flow:
                mock_flow_instance = Mock()
                mock_flow.from_client_secrets_file.return_value = mock_flow_instance
                mock_creds_instance = Mock()
                mock_creds_instance.valid = True
                mock_flow_instance.run_local_server.return_value = mock_creds_instance

                with patch('builtins.open', create=True):
                    result = downloader.setup_cloud_storage()

        assert result is True
        assert downloader.cloud_manager is not None

    def test_error_handler_retry_logic(self, integration_config):
        """Test error handler retry logic."""
        downloader = DocumentDownloader(integration_config)

        call_count = 0

        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Test error")
            return "success"

        result = downloader.error_handler.retry_with_backoff(failing_operation)

        assert result == "success"
        assert call_count == 3

    def test_structured_logging_operation(self, integration_config, tmp_path):
        """Test structured logging operation."""
        config = integration_config.copy()
        config["logging"]["file_path"] = str(tmp_path / "test.log")

        downloader = DocumentDownloader(config)

        downloader.structured_logger.log_operation(
            downloader.logger, "info", "Test operation",
            operation="test", department="TEST_DEPT"
        )

        log_file = tmp_path / "test.log"
        assert log_file.exists()

        log_content = log_file.read_text()
        log_data = json.loads(log_content.strip())

        assert log_data["message"] == "Test operation"
        assert log_data["operation"] == "test"
        assert log_data["department"] == "TEST_DEPT"

    def test_filename_generation(self, integration_config):
        """Test filename generation from document titles."""
        downloader = DocumentDownloader(integration_config)

        test_cases = [
            ("Должностная инструкция менеджера", "Должностная-инструкция-менеджера.docx"),
            ("Test Document with Special Characters!@#", "Test-Document-with-Special-Characters.docx"),
            ("Very Long Document Title That Exceeds The Maximum Length Limit And Should Be Truncated Properly",
             "Very-Long-Document-Title-That-Exceeds-The-Maximum-Length-Limit-And-Should-Be-Truncated.docx")
        ]

        for input_title, expected_filename in test_cases:
            result = downloader._generate_filename(input_title)
            assert result == expected_filename

    @patch('job_instruction_downloader.src.core.cloud_manager.GoogleDriveManager')
    def test_upload_to_cloud_workflow(self, mock_cloud_manager_class, integration_config, tmp_path):
        """Test complete upload to cloud workflow."""
        mock_cloud_manager = Mock()
        mock_cloud_manager_class.return_value = mock_cloud_manager
        mock_cloud_manager.authenticate.return_value = True
        mock_cloud_manager.get_or_create_folder.return_value = "folder123"
        mock_cloud_manager.check_duplicate.return_value = False
        mock_cloud_manager.upload_file.return_value = "file123"

        downloader = DocumentDownloader(integration_config)
        downloader.cloud_manager = mock_cloud_manager

        test_file = tmp_path / "test.docx"
        test_file.write_text("test content")

        result = downloader.upload_to_cloud(
            str(test_file), "TEST_DEPARTMENT", "Test Document"
        )

        assert result is True
        mock_cloud_manager.upload_file.assert_called_once()

    def test_job_instruction_model_with_cloud_fields(self):
        """Test JobInstruction model with new cloud storage fields."""
        job_instruction = JobInstruction(
            "Test Document", "TEST_DEPARTMENT", "http://example.com/doc"
        )

        assert job_instruction.cloud_status is None
        assert job_instruction.cloud_file_id is None
        assert job_instruction.download_timestamp is None
        assert job_instruction.upload_timestamp is None

        job_instruction.cloud_status = "uploaded"
        job_instruction.cloud_file_id = "file123"

        assert job_instruction.cloud_status == "uploaded"
        assert job_instruction.cloud_file_id == "file123"
