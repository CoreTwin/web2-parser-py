"""
Tests for configuration management.
"""

import json

from job_instruction_downloader.src.utils.config import ConfigManager


def test_load_config_success(config_manager, sample_config):
    """Test successful configuration loading."""
    config = config_manager.load_config()
    assert config == sample_config
    assert config["application"]["name"] == "Job Instruction Downloader"


def test_load_config_file_not_found(temp_dir):
    """Test loading configuration when file doesn't exist."""
    config_manager = ConfigManager(temp_dir)
    config = config_manager.load_config("nonexistent.json")
    assert config == {}


def test_load_config_invalid_json(temp_dir):
    """Test loading configuration with invalid JSON."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()

    config_file = config_dir / "invalid.json"
    with open(config_file, 'w') as f:
        f.write("{ invalid json }")

    config_manager = ConfigManager(config_dir)
    config = config_manager.load_config("invalid.json")
    assert config == {}


def test_save_config(temp_dir):
    """Test saving configuration."""
    config_manager = ConfigManager(temp_dir)

    test_config = {
        "test": "value",
        "number": 42
    }

    success = config_manager.save_config(test_config, "test.json")
    assert success

    config_file = temp_dir / "test.json"
    assert config_file.exists()

    with open(config_file, 'r') as f:
        loaded_config = json.load(f)

    assert loaded_config == test_config


def test_load_departments_config(config_manager):
    """Test loading departments configuration."""
    departments_config = {
        "departments": [
            {
                "id": "test_dept",
                "name": "ТЕСТОВЫЙ ОТДЕЛ",
                "folder_name": "Тестовый отдел",
                "priority": 1,
                "enabled": True
            }
        ]
    }

    config_manager.save_config(departments_config, "departments.json")
    loaded_config = config_manager.load_departments_config()

    assert loaded_config == departments_config
    assert len(loaded_config["departments"]) == 1
    assert loaded_config["departments"][0]["name"] == "ТЕСТОВЫЙ ОТДЕЛ"
