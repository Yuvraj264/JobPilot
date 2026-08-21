import os
import uuid
from typing import Tuple
from app.config import settings

ALLOWED_EXTENSIONS = {".pdf", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
    "application/octet-stream",  # Fallback for binary uploads with valid extension
}


class StorageService:
    """
    Dedicated Storage Service for saving, validating, retrieving, and deleting uploaded resume files.
    Enforces path traversal safety and file size/type constraints.
    """

    @staticmethod
    def get_storage_root() -> str:
        root = os.path.abspath(settings.RESUME_STORAGE_PATH)
        os.makedirs(root, exist_ok=True)
        return root

    @staticmethod
    def validate_file(filename: str, content_type: str, file_size: int) -> str:
        """
        Validates file extension, mime type, and file size.
        Returns normalized file extension (e.g., 'pdf' or 'docx').
        """
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Unsupported file format '{ext}'. Only PDF and DOCX files are allowed.")

        if content_type and content_type.lower() not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Invalid MIME type '{content_type}'. Uploaded file must be a PDF or DOCX document.")

        max_bytes = settings.MAX_RESUME_FILE_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise ValueError(f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed limit of {settings.MAX_RESUME_FILE_SIZE_MB} MB.")

        return ext.lstrip(".").upper()

    @staticmethod
    def save_file(file_bytes: bytes, original_filename: str, user_id: int = 1) -> Tuple[str, str, int]:
        """
        Saves uploaded file to filesystem storage.
        Returns: (safe_relative_path, file_type, file_size)
        """
        file_size = len(file_bytes)
        file_type = StorageService.validate_file(original_filename, None, file_size)

        ext = os.path.splitext(original_filename)[1].lower()
        unique_id = uuid.uuid4().hex[:12]
        safe_filename = f"user_{user_id}_{unique_id}{ext}"

        storage_root = StorageService.get_storage_root()
        absolute_path = os.path.join(storage_root, safe_filename)

        # Path traversal security check
        if not os.path.abspath(absolute_path).startswith(storage_root):
            raise ValueError("Invalid target filename or path traversal attempt detected.")

        with open(absolute_path, "wb") as f:
            f.write(file_bytes)

        # Store relative path for database portability
        relative_path = os.path.relpath(absolute_path, start=os.getcwd())
        return relative_path, file_type, file_size

    @staticmethod
    def resolve_path(file_path: str) -> str:
        """
        Safely resolves a database-stored file path to an absolute path.
        Prevents path traversal.
        """
        abs_path = os.path.abspath(file_path)
        storage_root = StorageService.get_storage_root()

        # If file_path is relative, test against storage root as well
        if not os.path.exists(abs_path):
            alt_path = os.path.abspath(os.path.join(storage_root, os.path.basename(file_path)))
            if os.path.exists(alt_path):
                abs_path = alt_path

        if not abs_path.startswith(storage_root):
            raise ValueError("Path traversal violation: Access to file outside storage root is prohibited.")

        return abs_path

    @staticmethod
    def exists(file_path: str) -> bool:
        try:
            target = StorageService.resolve_path(file_path)
            return os.path.isfile(target)
        except Exception:
            return False

    @staticmethod
    def delete(file_path: str) -> bool:
        try:
            target = StorageService.resolve_path(file_path)
            if os.path.exists(target):
                os.remove(target)
                return True
        except Exception:
            pass
        return False
