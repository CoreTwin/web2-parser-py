#!/usr/bin/env python3
"""Test script for different document format processing."""

import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'job_instruction_downloader'))

from job_instruction_downloader.src.core.validator import DocumentValidator
from job_instruction_downloader.src.utils.config import ConfigManager

def create_test_document(format_type: str, size: int = 50000) -> Path:
    """Create a test document with proper headers for the given format."""
    temp_dir = Path(tempfile.gettempdir())
    
    if format_type == "docx":
        filename = temp_dir / "test_document.docx"
        with open(filename, 'wb') as f:
            f.write(b'PK\x03\x04')  # ZIP header
            f.write(b'\x00' * (size - 4))  # Pad to desired size
    
    elif format_type == "doc":
        filename = temp_dir / "test_document.doc"
        with open(filename, 'wb') as f:
            f.write(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1')  # OLE header
            f.write(b'\x00' * (size - 8))  # Pad to desired size
    
    elif format_type == "pdf":
        filename = temp_dir / "test_document.pdf"
        with open(filename, 'wb') as f:
            f.write(b'%PDF-1.4\n')  # PDF header
            f.write(b'\x00' * (size - 9))  # Pad to desired size
    
    else:
        raise ValueError(f"Unsupported format: {format_type}")
    
    return filename

def test_document_formats():
    """Test document validation for .docx, .pdf, and .doc formats."""
    print("Testing universal document format processing...")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        validator = DocumentValidator(config)
        
        consultant_config_path = Path(__file__).parent / "job_instruction_downloader/config/sites/consultant_ru.json"
        with open(consultant_config_path, 'r', encoding='utf-8') as f:
            site_config = json.load(f)
        
        validation_config = site_config.get("validation", {})
        validation_config["expected_file_types"] = [".docx", ".doc", ".pdf"]  # Add PDF support
        
        print("✅ DocumentValidator initialized successfully")
        print(f"✅ Validation config loaded: {validation_config}")
        
        formats = ["docx", "doc", "pdf"]
        test_results = {}
        
        for format_type in formats:
            print(f"\n--- Testing {format_type.upper()} format ---")
            
            test_file = create_test_document(format_type, 50000)
            print(f"Created test file: {test_file}")
            
            is_valid = validator.validate_file(str(test_file), validation_config)
            print(f"File validation result: {is_valid}")
            
            content_valid = validator._validate_content(str(test_file))
            print(f"Content validation result: {content_valid}")
            
            structure_result = validator.validate_document_structure(str(test_file))
            structure_valid = structure_result.get("valid", False)
            print(f"Structure validation result: {structure_valid}")
            print(f"Structure metadata: {structure_result.get('metadata', {})}")
            
            test_results[format_type] = {
                "file_valid": is_valid,
                "content_valid": content_valid,
                "structure_valid": structure_valid
            }
            
            test_file.unlink()
            print(f"Cleaned up test file: {test_file}")
        
        print("\n=== Test Results Summary ===")
        all_passed = True
        for format_type, results in test_results.items():
            status = "✅ PASS" if all(results.values()) else "❌ FAIL"
            print(f"{format_type.upper()}: {status}")
            if not all(results.values()):
                all_passed = False
                print(f"  - File validation: {results['file_valid']}")
                print(f"  - Content validation: {results['content_valid']}")
                print(f"  - Structure validation: {results['structure_valid']}")
        
        if all_passed:
            print("\n🎉 All document formats validated successfully!")
            print("✅ Universal document processing works for .docx, .pdf, and .doc formats")
        else:
            print("\n❌ Some document format validations failed")
            return False
            
    except Exception as e:
        print(f"❌ Error during document format testing: {e}")
        return False
    
    return True

def test_document_size_limits():
    """Test document validation with different file sizes."""
    print("\n--- Testing document size limits ---")
    
    try:
        config_manager = ConfigManager()
        config = config_manager.load_config()
        validator = DocumentValidator(config)
        
        small_file = create_test_document("docx", 1000)  # 1KB
        consultant_config_path = Path(__file__).parent / "job_instruction_downloader/config/sites/consultant_ru.json"
        with open(consultant_config_path, 'r', encoding='utf-8') as f:
            site_config = json.load(f)
        validation_config = site_config.get("validation", {})
        
        small_valid = validator.validate_file(str(small_file), validation_config)
        print(f"Small file (1KB) validation: {small_valid} (expected: False)")
        small_file.unlink()
        
        normal_file = create_test_document("docx", 50000)  # 50KB
        normal_valid = validator.validate_file(str(normal_file), validation_config)
        print(f"Normal file (50KB) validation: {normal_valid} (expected: True)")
        normal_file.unlink()
        
        large_file = create_test_document("docx", 15000000)  # 15MB
        large_valid = validator.validate_file(str(large_file), validation_config)
        print(f"Large file (15MB) validation: {large_valid} (expected: False)")
        large_file.unlink()
        
        return not small_valid and normal_valid and not large_valid
        
    except Exception as e:
        print(f"❌ Error during size limit testing: {e}")
        return False

if __name__ == "__main__":
    print("Universal Document Format Processing Test")
    print("=" * 50)
    
    format_success = test_document_formats()
    size_success = test_document_size_limits()
    
    if format_success and size_success:
        print("\n🎉 All document format tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some document format tests failed")
        sys.exit(1)
