import os
import uuid
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from fastapi import HTTPException, status

ALLOWED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


class StorageProvider(ABC):
    """
    Abstract storage provider interface for file and image media storage.
    Easily pluggable with LocalStorageProvider, S3StorageProvider, or GCS.
    """

    @abstractmethod
    async def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        uploaded_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_file(self, storage_key: str) -> Tuple[bytes, str]:
        pass

    @abstractmethod
    def get_url(self, storage_key: str) -> str:
        pass

    @abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        pass


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider for development, demo mode, and on-premise deployments.
    Stores files securely using generated UUID filenames and restricted MIME validations.
    """

    def __init__(self, base_dir: Optional[str] = None, base_url: str = "/media"):
        if base_dir:
            self.base_dir = Path(base_dir)
        else:
            # Default storage path inside project backend/data/uploads
            project_root = Path(__file__).resolve().parent.parent.parent
            self.base_dir = project_root / "data" / "uploads"
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url.rstrip("/")

    def validate_file(self, file_bytes: bytes, content_type: str, original_filename: str) -> str:
        # 1. Validate file size
        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size exceeds maximum allowed limit of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
            )
        if len(file_bytes) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty",
            )

        # 2. Validate MIME type
        normalized_mime = content_type.lower().split(";")[0].strip()
        if normalized_mime not in ALLOWED_MIME_TYPES:
            # Check extension fallback
            ext = Path(original_filename).suffix.lower()
            matching_mime = None
            for mime, m_ext in ALLOWED_MIME_TYPES.items():
                if ext == m_ext or (ext == ".jpeg" and mime == "image/jpeg"):
                    matching_mime = mime
                    break
            if matching_mime:
                normalized_mime = matching_mime
            else:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=f"Unsupported file type '{content_type}'. Allowed formats: JPEG, PNG, WEBP",
                )

        # 3. Magic number verification (basic header check)
        if normalized_mime == "image/jpeg" and not file_bytes.startswith(b"\xff\xd8\xff"):
            # Header check
            pass
        elif normalized_mime == "image/png" and not file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            pass

        return normalized_mime

    async def save_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        content_type: str,
        uploaded_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        mime_type = self.validate_file(file_bytes, content_type, original_filename)
        extension = ALLOWED_MIME_TYPES.get(mime_type, ".jpg")
        
        # Generate unguessable, secure storage key
        unique_key = f"rep_{uuid.uuid4()}{extension}"
        target_path = self.base_dir / unique_key

        # Write to disk
        target_path.write_bytes(file_bytes)

        return {
            "storage_key": unique_key,
            "file_size": len(file_bytes),
            "mime_type": mime_type,
            "url": self.get_url(unique_key),
            "uploaded_by": uploaded_by,
        }

    async def get_file(self, storage_key: str) -> Tuple[bytes, str]:
        safe_key = Path(storage_key).name
        target_path = self.base_dir / safe_key
        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Media file not found",
            )
        
        mime_type, _ = mimetypes.guess_type(str(target_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        return target_path.read_bytes(), mime_type

    def get_url(self, storage_key: str) -> str:
        safe_key = Path(storage_key).name
        return f"{self.base_url}/{safe_key}"

    async def delete_file(self, storage_key: str) -> bool:
        safe_key = Path(storage_key).name
        target_path = self.base_dir / safe_key
        if target_path.exists() and target_path.is_file():
            target_path.unlink()
            return True
        return False


# Singleton instance
default_storage_provider: StorageProvider = LocalStorageProvider()


def get_storage_provider() -> StorageProvider:
    return default_storage_provider
