"""
Comprehensive tests for Phase 2 functionality.
"""

import pytest
import json
from unittest.mock import Mock, patch

from job_instruction_downloader.src.core.downloader import DocumentDownloader
from job_instruction_downloader.src.utils.error_handler import EnhancedErrorHandler
from job_instruction_downloader.src.utils.structured_logger import StructuredLogger
from job_instruction_downloader.src.models.job_instruction import JobInstruction


@pytest.fixture
def phase2_config():
    """Phase 2 test configuration."""
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
            "root_folder_name": "Test Job Instructions",
            "cleanup_after_upload": False
        },
        "error_handling": {
            "retry_attempts": 3,
            "retry_delay": 0.1,
            "exponential_backoff": True,
            "refresh_page_on_error": True,
            "skip_on_repeated_failure": True
        },
        "logging": {
            "file_path": "logs/test.log",
            "max_file_size": "10MB",
            "backup_count": 5,
            "console_output": True,
            "structured_logging": True,
            "level": "INFO"
        }
    }


class TestPhase2Integration:
    """Test Phase 2 integration functionality."""

    def test_enhanced_job_instruction_model(self):
        """Test JobInstruction model with cloud storage fields."""
        job_instruction = JobInstruction(
            title="Test Document",
            department="TEST_DEPARTMENT",
            url="http://example.com/doc"
        )

        assert hasattr(job_instruction, 'local_path')
        assert hasattr(job_instruction, 'cloud_status')
        assert hasattr(job_instruction, 'cloud_file_id')
        assert hasattr(job_instruction, 'download_timestamp')
        assert hasattr(job_instruction, 'upload_timestamp')

        job_instruction.cloud_status = "uploaded"
        job_instruction.cloud_file_id = "file123"

        data = job_instruction.to_dict()
        assert "cloud_status" in data
        assert "cloud_file_id" in data
        assert data["cloud_status"] == "uploaded"
        assert data["cloud_file_id"] == "file123"

    def test_downloader_with_phase2_components(self, phase2_config):
        """Test downloader initialization with Phase 2 components."""
        downloader = DocumentDownloader(phase2_config)

        assert downloader.error_handler is not None
        assert downloader.structured_logger is not None
        assert isinstance(downloader.error_handler, EnhancedErrorHandler)
        assert isinstance(downloader.structured_logger, StructuredLogger)

    def test_filename_generation_russian_characters(self, phase2_config):
        """Test filename generation with Russian characters."""
        downloader = DocumentDownloader(phase2_config)

        test_cases = [
            ("Должностная инструкция менеджера по продажам",
             "Должностная-инструкция-менеджера-по-продажам.docx"),
            ("Инструкция №123 для отдела кадров",
             "Инструкция-123-для-отдела-кадров.docx"),
            ("Документ с символами !@#$%^&*()",
             "Документ-с-символами.docx")
        ]

        for input_title, expected_pattern in test_cases:
            result = downloader._generate_filename(input_title)
            assert result.endswith(".docx")
            assert len(result) <= 104
            assert not any(char in result for char in '<>:"/\\|?*')

    @patch('job_instruction_downloader.src.core.cloud_manager.build')
    @patch('job_instruction_downloader.src.core.cloud_manager.Credentials')
    def test_cloud_storage_authentication_flow(self, mock_creds, mock_build, phase2_config):
        """Test Google Drive authentication flow."""
        downloader = DocumentDownloader(phase2_config)

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

    def test_error_handler_exponential_backoff(self, phase2_config):
        """Test error handler exponential backoff functionality."""
        downloader = DocumentDownloader(phase2_config)

        call_count = 0

        def failing_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception(f"Test error {call_count}")
            return "success"

        result = downloader.error_handler.retry_with_backoff(failing_operation)

        assert result == "success"
        assert call_count == 3

    def test_structured_logging_with_operation_context(self, phase2_config, tmp_path):
        """Test structured logging with operation context."""
        config = phase2_config.copy()
        config["logging"]["file_path"] = str(tmp_path / "test.log")

        downloader = DocumentDownloader(config)

        downloader.structured_logger.log_operation(
            downloader.logger, "info", "Test operation completed",
            operation="test_operation",
            department="TEST_DEPT",
            document_title="Test Document",
            duration=1.5
        )

        log_file = tmp_path / "test.log"
        assert log_file.exists()

        log_content = log_file.read_text()
        log_data = json.loads(log_content.strip())

        assert log_data["message"] == "Test operation completed"
        assert log_data["operation"] == "test_operation"
        assert log_data["department"] == "TEST_DEPT"
        assert log_data["document_title"] == "Test Document"
        assert log_data["duration"] == 1.5

    @patch('job_instruction_downloader.src.core.cloud_manager.GoogleDriveManager')
    def test_complete_upload_workflow(self, mock_cloud_manager_class, phase2_config, tmp_path):
        """Test complete upload workflow with all Phase 2 components."""
        mock_cloud_manager = Mock()
        mock_cloud_manager_class.return_value = mock_cloud_manager
        mock_cloud_manager.authenticate.return_value = True
        mock_cloud_manager.get_or_create_folder.side_effect = ["root123", "dept123"]
        mock_cloud_manager.check_duplicate.return_value = False
        mock_cloud_manager.upload_file.return_value = "file123"

        downloader = DocumentDownloader(phase2_config)
        downloader.cloud_manager = mock_cloud_manager

        test_file = tmp_path / "test.docx"
        test_file.write_text("test content")

        result = downloader.upload_to_cloud(
            str(test_file), "Отдел кадров", "Должностная инструкция менеджера"
        )

        assert result is True
        mock_cloud_manager.get_or_create_folder.assert_any_call("Test Job Instructions")
        mock_cloud_manager.get_or_create_folder.assert_any_call("Отдел кадров", "root123")
        mock_cloud_manager.upload_file.assert_called_once()

        upload_args = mock_cloud_manager.upload_file.call_args
        assert upload_args[0][0] == str(test_file)
        assert upload_args[0][1] == "dept123"
        assert upload_args[0][2].endswith(".docx")
