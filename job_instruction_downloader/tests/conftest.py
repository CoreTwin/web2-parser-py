"""
Pytest configuration and fixtures.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any

from job_instruction_downloader.src.utils.config import ConfigManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """Sample configuration for testing."""
    return {
        "application": {
            "name": "Job Instruction Downloader",
            "version": "1.0.0",
            "debug": True,
            "log_level": "DEBUG"
        },
        "download": {
            "timeout": 30,
            "retry_attempts": 3,
            "retry_delay": 1,
            "max_concurrent_downloads": 1,
            "temp_directory": "test_downloads"
        },
        "selenium": {
            "browser": "chrome",
            "driver_path": "auto",
            "headless": True,
            "window_size": [1920, 1080],
            "page_load_timeout": 10,
            "implicit_wait": 5
        },
        "logging": {
            "file_path": "test_logs/app.log",
            "max_file_size": "1MB",
            "backup_count": 2,
            "console_output": False
        }
    }


@pytest.fixture
def config_manager(temp_dir, sample_config):
    """ConfigManager instance with temporary directory."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()

    config_file = config_dir / "settings.json"
    import json
    with open(config_file, 'w') as f:
        json.dump(sample_config, f)

    return ConfigManager(config_dir)


@pytest.fixture
def sample_job_instruction():
    """Sample job instruction for testing."""
    from job_instruction_downloader.src.models.job_instruction import JobInstruction

    return JobInstruction(
        title="Тестовая должностная инструкция",
        department="ТЕСТОВЫЙ ОТДЕЛ",
        url="https://example.com/test-document"
    )


@pytest.fixture
def sample_department():
    """Sample department for testing."""
    from job_instruction_downloader.src.models.department import Department
    from job_instruction_downloader.src.models.job_instruction import JobInstruction

    department = Department(
        id="test_dept",
        name="ТЕСТОВЫЙ ОТДЕЛ",
        folder_name="Тестовый отдел",
        priority=1
    )

    for i in range(3):
        ji = JobInstruction(
            title=f"Тестовая инструкция {i+1}",
            department="ТЕСТОВЫЙ ОТДЕЛ",
            url=f"https://example.com/test-document-{i+1}"
        )
        department.add_job_instruction(ji)

    return department
