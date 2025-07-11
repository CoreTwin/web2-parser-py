"""
Tests for document validator functionality.
"""

from job_instruction_downloader.src.core.validator import DocumentValidator


class TestDocumentValidator:
    """Test document validator functionality."""

    def test_validator_initialization(self):
        """Test validator initialization."""
        config = {"validation": {"min_size": 1000}}
        validator = DocumentValidator(config)
        assert validator.config == config

    def test_validate_file_success(self, tmp_path):
        """Test successful file validation."""
        config = {}
        validator = DocumentValidator(config)

        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"A" * 5000)

        validation_config = {
            "min_size": 1000,
            "max_size": 10000,
            "expected_file_types": [".docx"],
            "check_content": False
        }

        assert validator.validate_file(str(test_file), validation_config) is True

    def test_validate_file_not_exists(self):
        """Test validation of non-existent file."""
        config = {}
        validator = DocumentValidator(config)

        validation_config = {"min_size": 1000}

        assert validator.validate_file("/nonexistent/file.docx", validation_config) is False

    def test_validate_file_too_small(self, tmp_path):
        """Test validation of file that's too small."""
        config = {}
        validator = DocumentValidator(config)

        test_file = tmp_path / "small.docx"
        test_file.write_bytes(b"A" * 100)

        validation_config = {
            "min_size": 1000,
            "expected_file_types": [".docx"]
        }

        assert validator.validate_file(str(test_file), validation_config) is False

    def test_validate_file_too_large(self, tmp_path):
        """Test validation of file that's too large."""
        config = {}
        validator = DocumentValidator(config)

        test_file = tmp_path / "large.docx"
        test_file.write_bytes(b"A" * 10000)

        validation_config = {
            "min_size": 1000,
            "max_size": 5000,
            "expected_file_types": [".docx"]
        }

        assert validator.validate_file(str(test_file), validation_config) is False

    def test_validate_file_wrong_type(self, tmp_path):
        """Test validation of file with wrong type."""
        config = {}
        validator = DocumentValidator(config)

        test_file = tmp_path / "test.txt"
        test_file.write_bytes(b"A" * 5000)

        validation_config = {
            "min_size": 1000,
            "expected_file_types": [".docx", ".doc"]
        }

        assert validator.validate_file(str(test_file), validation_config) is False

    def test_validate_content_docx(self, tmp_path):
        """Test content validation for DOCX files."""
        config = {}
        validator = DocumentValidator(config)

        docx_file = tmp_path / "test.docx"
        docx_file.write_bytes(b"PK\x03\x04" + b"A" * 1000)

        assert validator._validate_content(str(docx_file)) is True

        invalid_docx = tmp_path / "invalid.docx"
        invalid_docx.write_bytes(b"INVALID" + b"A" * 1000)

        assert validator._validate_content(str(invalid_docx)) is False

    def test_validate_content_doc(self, tmp_path):
        """Test content validation for DOC files."""
        config = {}
        validator = DocumentValidator(config)

        doc_file = tmp_path / "test.doc"
        doc_file.write_bytes(b"\xd0\xcf\x11\xe0" + b"A" * 1000)

        assert validator._validate_content(str(doc_file)) is True

    def test_validate_content_pdf(self, tmp_path):
        """Test content validation for PDF files."""
        config = {}
        validator = DocumentValidator(config)

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF" + b"A" * 1000)

        assert validator._validate_content(str(pdf_file)) is True

    def test_validate_document_structure(self, tmp_path):
        """Test document structure validation."""
        config = {}
        validator = DocumentValidator(config)

        test_file = tmp_path / "test.docx"
        test_file.write_bytes(b"PK\x03\x04" + b"A" * 1000)

        result = validator.validate_document_structure(str(test_file))

        assert result["valid"] is True
        assert result["file_size"] > 0
        assert result["file_type"] == ".docx"
        assert len(result["errors"]) == 0
        assert "file_name" in result["metadata"]

    def test_validate_document_structure_invalid(self):
        """Test document structure validation for invalid file."""
        config = {}
        validator = DocumentValidator(config)

        result = validator.validate_document_structure("/nonexistent/file.docx")

        assert result["valid"] is False
        assert "File does not exist" in result["errors"]
