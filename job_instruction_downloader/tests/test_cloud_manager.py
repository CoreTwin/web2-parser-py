"""
Tests for Google Drive cloud manager.
"""

import pytest
from unittest.mock import Mock, patch

from job_instruction_downloader.src.core.cloud_manager import GoogleDriveManager


@pytest.fixture
def cloud_config():
    """Cloud configuration fixture."""
    return {
        "cloud_storage": {
            "default_provider": "google_drive",
            "credentials_path": "config/credentials.json"
        }
    }


@pytest.fixture
def cloud_manager(cloud_config):
    """Cloud manager fixture."""
    return GoogleDriveManager(cloud_config)


class TestGoogleDriveManager:
    """Test cases for GoogleDriveManager."""

    @patch('job_instruction_downloader.src.core.cloud_manager.build')
    @patch('job_instruction_downloader.src.core.cloud_manager.Credentials')
    @patch('job_instruction_downloader.src.core.cloud_manager.Path')
    def test_authenticate_success(self, mock_path_class, mock_creds, mock_build, cloud_manager):
        """Test successful authentication."""
        mock_service = Mock()
        mock_build.return_value = mock_service
        
        mock_token_path = Mock()
        mock_token_path.exists.return_value = False
        mock_credentials_path = Mock()
        mock_credentials_path.exists.return_value = True
        
        def path_side_effect(path_str):
            if 'token.json' in str(path_str):
                return mock_token_path
            elif 'credentials.json' in str(path_str):
                return mock_credentials_path
            return Mock()
        
        mock_path_class.side_effect = path_side_effect

        with patch('job_instruction_downloader.src.core.cloud_manager.InstalledAppFlow') as mock_flow:
            mock_flow_instance = Mock()
            mock_flow.from_client_secrets_file.return_value = mock_flow_instance
            mock_creds_instance = Mock()
            mock_creds_instance.valid = True
            mock_flow_instance.run_local_server.return_value = mock_creds_instance

            with patch('builtins.open', create=True):
                result = cloud_manager.authenticate()

        assert result is True
        assert cloud_manager.service == mock_service

    def test_create_folder(self, cloud_manager):
        """Test folder creation."""
        mock_service = Mock()
        mock_service.files().create().execute.return_value = {'id': 'folder123'}
        cloud_manager.service = mock_service

        folder_id = cloud_manager.create_folder("Test Folder")

        assert folder_id == 'folder123'

    def test_find_folder(self, cloud_manager):
        """Test folder finding."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            'files': [{'id': 'folder123', 'name': 'Test Folder'}]
        }
        cloud_manager.service = mock_service

        folder_id = cloud_manager.find_folder("Test Folder")

        assert folder_id == 'folder123'

    def test_upload_file(self, cloud_manager, tmp_path):
        """Test file upload."""
        test_file = tmp_path / "test.docx"
        test_file.write_text("test content")

        mock_service = Mock()
        mock_service.files().create().execute.return_value = {'id': 'file123'}
        cloud_manager.service = mock_service

        with patch('job_instruction_downloader.src.core.cloud_manager.MediaFileUpload'):
            file_id = cloud_manager.upload_file(str(test_file), "folder123", "custom_name.docx")

        assert file_id == 'file123'

    def test_check_duplicate(self, cloud_manager):
        """Test duplicate checking."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {
            'files': [{'id': 'file123', 'name': 'test.docx'}]
        }
        cloud_manager.service = mock_service

        result = cloud_manager.check_duplicate("test.docx", "folder123")

        assert result is True

    def test_create_folder_structure(self, cloud_manager):
        """Test nested folder structure creation."""
        mock_service = Mock()
        mock_service.files().list().execute.return_value = {'files': []}
        mock_service.files().create().execute.side_effect = [
            {'id': 'folder1'}, {'id': 'folder2'}
        ]
        cloud_manager.service = mock_service

        folder_id = cloud_manager.create_folder_structure("parent/child")

        assert folder_id == 'folder2'
