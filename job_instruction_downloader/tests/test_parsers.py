"""
Tests for parser functionality.
"""

from unittest.mock import Mock

from job_instruction_downloader.src.core.parsers.base_parser import BaseParser
from job_instruction_downloader.src.core.parsers.consultant_parser import ConsultantParser
from job_instruction_downloader.src.models.department import Department


class TestBaseParser:
    """Test base parser functionality."""

    def test_base_parser_initialization(self):
        """Test base parser initialization."""
        config = {
            "site_config": {
                "extraction": {
                    "selectors": {
                        "document_links": "[devinid]"
                    }
                },
                "rate_limiting": {
                    "delay_between_requests": 3
                }
            }
        }

        class TestParser(BaseParser):
            def extract_documents(self, driver, department):
                return []

            def validate_document(self, file_path):
                return True

        parser = TestParser(config)
        assert parser.config == config
        assert parser.site_config == config["site_config"]

    def test_get_selectors(self):
        """Test selector retrieval."""
        config = {
            "site_config": {
                "extraction": {
                    "selectors": {
                        "document_links": "[devinid]",
                        "export_button": "[devinid='14']"
                    }
                }
            }
        }

        class TestParser(BaseParser):
            def extract_documents(self, driver, department):
                return []

            def validate_document(self, file_path):
                return True

        parser = TestParser(config)
        selectors = parser.get_selectors()

        assert selectors["document_links"] == "[devinid]"
        assert selectors["export_button"] == "[devinid='14']"

    def test_process_title(self):
        """Test title processing."""
        config = {
            "site_config": {
                "extraction": {
                    "title_processing": {
                        "remove_prefixes": ["Должностная инструкция"],
                        "remove_suffixes": ["(профессиональный стандарт)"],
                        "max_length": 50
                    }
                }
            }
        }

        class TestParser(BaseParser):
            def extract_documents(self, driver, department):
                return []

            def validate_document(self, file_path):
                return True

        parser = TestParser(config)

        title = "Должностная инструкция Менеджер (профессиональный стандарт)"
        processed = parser.process_title(title)
        assert processed == "Менеджер"

        long_title = "Должностная инструкция " + "А" * 100
        processed_long = parser.process_title(long_title)
        assert len(processed_long) <= 50


class TestConsultantParser:
    """Test Consultant.ru parser functionality."""

    def test_consultant_parser_initialization(self):
        """Test Consultant parser initialization."""
        config = {
            "site_config": {
                "site_info": {
                    "name": "Consultant.ru",
                    "base_url": "https://cloud.consultant.ru"
                },
                "extraction": {
                    "selectors": {
                        "document_links": "[devinid]"
                    }
                }
            }
        }

        parser = ConsultantParser(config)
        assert parser.config == config
        assert parser.site_config == config["site_config"]

    def test_extract_url(self):
        """Test URL extraction."""
        config = {
            "site_info": {
                "base_url": "https://cloud.consultant.ru"
            }
        }

        parser = ConsultantParser(config)

        mock_element = Mock()
        mock_element.get_attribute.return_value = "/document/123"

        url = parser._extract_url(mock_element, "https://cloud.consultant.ru")
        assert url == "https://cloud.consultant.ru/document/123"

        mock_element.get_attribute.return_value = "https://cloud.consultant.ru/document/456"
        url = parser._extract_url(mock_element, "https://cloud.consultant.ru")
        assert url == "https://cloud.consultant.ru/document/456"

    def test_validate_document(self, tmp_path):
        """Test document validation."""
        config = {
            "site_config": {
                "download": {
                    "expected_file_types": [".docx", ".doc"],
                    "validation": {
                        "min_size": 1000,
                        "max_size": 1000000,
                        "check_content": False
                    }
                }
            }
        }

        parser = ConsultantParser(config)

        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"A" * 5000)

        assert parser.validate_document(str(test_file)) is True

        small_file = tmp_path / "small.docx"
        small_file.write_bytes(b"A" * 100)

        assert parser.validate_document(str(small_file)) is False

        wrong_type = tmp_path / "wrong.txt"
        wrong_type.write_bytes(b"A" * 5000)

        assert parser.validate_document(str(wrong_type)) is False

    def test_extract_documents_no_driver(self):
        """Test document extraction without driver."""
        config = {}
        parser = ConsultantParser(config)
        department = Department(
            id="test",
            name="Test Department",
            folder_name="test",
            priority=1,
            enabled=True
        )

        documents = parser.extract_documents(None, department)
        assert documents == []
