"""
Tests for data models.
"""

import pytest
from datetime import datetime
from pathlib import Path

from job_instruction_downloader.src.models.job_instruction import JobInstruction
from job_instruction_downloader.src.models.department import Department


def test_job_instruction_creation():
    """Test JobInstruction creation."""
    ji = JobInstruction(
        title="Тестовая инструкция",
        department="ТЕСТОВЫЙ ОТДЕЛ",
        url="https://example.com/test"
    )
    
    assert ji.title == "Тестовая инструкция"
    assert ji.department == "ТЕСТОВЫЙ ОТДЕЛ"
    assert ji.url == "https://example.com/test"
    assert ji.status == "pending"
    assert ji.metadata == {}


def test_job_instruction_filename():
    """Test filename generation."""
    ji = JobInstruction(
        title="Тестовая инструкция с <специальными> символами",
        department="ТЕСТОВЫЙ ОТДЕЛ",
        url="https://example.com/test"
    )
    
    filename = ji.filename
    assert filename == "Тестовая инструкция с _специальными_ символами.docx"


def test_job_instruction_clean_filename():
    """Test filename cleaning."""
    ji = JobInstruction(
        title="Test",
        department="Test",
        url="https://example.com/test"
    )
    
    cleaned = ji.clean_filename("file<name>with:invalid/chars")
    assert "<" not in cleaned
    assert ">" not in cleaned
    assert ":" not in cleaned
    assert "/" not in cleaned
    
    long_name = "a" * 150
    cleaned_long = ji.clean_filename(long_name)
    assert len(cleaned_long) <= 100


def test_job_instruction_serialization():
    """Test JobInstruction serialization."""
    ji = JobInstruction(
        title="Тестовая инструкция",
        department="ТЕСТОВЫЙ ОТДЕЛ",
        url="https://example.com/test",
        status="completed",
        download_date=datetime(2025, 1, 1, 12, 0, 0)
    )
    
    data = ji.to_dict()
    assert data["title"] == "Тестовая инструкция"
    assert data["status"] == "completed"
    assert data["download_date"] == "2025-01-01T12:00:00"
    
    ji_restored = JobInstruction.from_dict(data)
    assert ji_restored.title == ji.title
    assert ji_restored.status == ji.status
    assert ji_restored.download_date == ji.download_date


def test_department_creation():
    """Test Department creation."""
    dept = Department(
        id="test_dept",
        name="ТЕСТОВЫЙ ОТДЕЛ",
        folder_name="Тестовый отдел"
    )
    
    assert dept.id == "test_dept"
    assert dept.name == "ТЕСТОВЫЙ ОТДЕЛ"
    assert dept.folder_name == "Тестовый отдел"
    assert dept.priority == 1
    assert dept.enabled is True
    assert dept.job_instructions == []


def test_department_add_job_instruction():
    """Test adding job instructions to department."""
    dept = Department(
        id="test_dept",
        name="ТЕСТОВЫЙ ОТДЕЛ",
        folder_name="Тестовый отдел"
    )
    
    ji = JobInstruction(
        title="Тестовая инструкция",
        department="ТЕСТОВЫЙ ОТДЕЛ",
        url="https://example.com/test"
    )
    
    dept.add_job_instruction(ji)
    
    assert dept.total_documents == 1
    assert dept.job_instructions[0] == ji


def test_department_progress_calculation():
    """Test department progress calculation."""
    dept = Department(
        id="test_dept",
        name="ТЕСТОВЫЙ ОТДЕЛ",
        folder_name="Тестовый отдел"
    )
    
    ji1 = JobInstruction("Test 1", "ТЕСТОВЫЙ ОТДЕЛ", "https://example.com/1", status="completed")
    ji2 = JobInstruction("Test 2", "ТЕСТОВЫЙ ОТДЕЛ", "https://example.com/2", status="completed")
    ji3 = JobInstruction("Test 3", "ТЕСТОВЫЙ ОТДЕЛ", "https://example.com/3", status="failed")
    ji4 = JobInstruction("Test 4", "ТЕСТОВЫЙ ОТДЕЛ", "https://example.com/4", status="pending")
    
    dept.add_job_instruction(ji1)
    dept.add_job_instruction(ji2)
    dept.add_job_instruction(ji3)
    dept.add_job_instruction(ji4)
    
    assert dept.total_documents == 4
    assert dept.completed_documents == 2
    assert dept.failed_documents == 1
    assert dept.progress_percentage == 50.0


def test_department_serialization():
    """Test Department serialization."""
    dept = Department(
        id="test_dept",
        name="ТЕСТОВЫЙ ОТДЕЛ",
        folder_name="Тестовый отдел",
        priority=2
    )
    
    ji = JobInstruction("Test", "ТЕСТОВЫЙ ОТДЕЛ", "https://example.com/test")
    dept.add_job_instruction(ji)
    
    data = dept.to_dict()
    assert data["id"] == "test_dept"
    assert data["priority"] == 2
    assert len(data["job_instructions"]) == 1
    
    dept_restored = Department.from_dict(data)
    assert dept_restored.id == dept.id
    assert dept_restored.priority == dept.priority
    assert len(dept_restored.job_instructions) == 1
    assert dept_restored.job_instructions[0].title == "Test"
