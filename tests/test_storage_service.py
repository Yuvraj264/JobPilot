import os
import pytest
from app.services.storage_service import StorageService


def test_storage_validation():
    """Test extension and file size validation."""
    # Valid PDF
    ext = StorageService.validate_file("my_resume.pdf", "application/pdf", 1024)
    assert ext == "PDF"

    # Valid DOCX
    ext_docx = StorageService.validate_file("my_resume.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 2048)
    assert ext_docx == "DOCX"

    # Invalid extension
    with pytest.raises(ValueError, match="Unsupported file format"):
        StorageService.validate_file("script.exe", "application/octet-stream", 500)

    # Oversized file (>10MB)
    with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
        StorageService.validate_file("huge.pdf", "application/pdf", 15 * 1024 * 1024)


def test_save_and_delete_file():
    """Test saving file to storage, verifying file existence, and deleting file."""
    content = b"%PDF-1.4 Mock PDF Content"
    rel_path, file_type, file_size = StorageService.save_file(content, "test_file.pdf", user_id=1)
    
    assert file_type == "PDF"
    assert file_size == len(content)
    assert StorageService.exists(rel_path) is True

    # Delete
    deleted = StorageService.delete(rel_path)
    assert deleted is True
    assert StorageService.exists(rel_path) is False


def test_path_traversal_protection():
    """Test path traversal detection."""
    with pytest.raises(ValueError):
        StorageService.resolve_path("../../../etc/passwd")
