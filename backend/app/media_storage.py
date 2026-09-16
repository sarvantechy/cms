"""Private provider-neutral binary storage used by authorized media routes."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from uuid import UUID, uuid4

from app.config import settings

ALLOWED_MEDIA_TYPES = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
}
MAX_MEDIA_BYTES = 5 * 1024 * 1024


class MediaValidationError(ValueError):
    """Represent a rejected binary object before persistence."""


@dataclass(frozen=True, slots=True)
class StoredMedia:
    """Describe one successfully persisted private binary object."""

    provider: str
    object_key: str
    checksum_sha256: str
    size_bytes: int


class LocalMediaStorage:
    """Persist private media below a configured local root for development."""

    def __init__(self, root: str | Path = settings.media_storage_path) -> None:
        """Initialize storage without creating directories until the first write."""

        self.root = Path(root).resolve()

    def store(self, tenant_id: UUID, content: bytes, content_type: str) -> StoredMedia:
        """Validate and atomically persist one object under an opaque tenant key."""

        suffix = ALLOWED_MEDIA_TYPES.get(content_type)
        if suffix is None:
            raise MediaValidationError("Only PDF, JPEG, and PNG files are allowed")
        if not content:
            raise MediaValidationError("Uploaded file is empty")
        if len(content) > MAX_MEDIA_BYTES:
            raise MediaValidationError("Uploaded file exceeds the 5 MiB limit")
        if content_type == "application/pdf" and not content.startswith(b"%PDF-"):
            raise MediaValidationError("File content does not match the declared PDF type")
        if content_type == "image/jpeg" and not content.startswith(b"\xff\xd8\xff"):
            raise MediaValidationError("File content does not match the declared JPEG type")
        if content_type == "image/png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
            raise MediaValidationError("File content does not match the declared PNG type")

        object_key = f"{tenant_id}/{uuid4().hex}{suffix}"
        destination = self.resolve(object_key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(f"{destination.suffix}.tmp")
        temporary.write_bytes(content)
        temporary.replace(destination)
        return StoredMedia(
            provider="local",
            object_key=object_key,
            checksum_sha256=sha256(content).hexdigest(),
            size_bytes=len(content),
        )

    def delete(self, object_key: str) -> None:
        """Remove an uncommitted object after a metadata persistence failure."""

        self.resolve(object_key).unlink(missing_ok=True)

    def resolve(self, object_key: str) -> Path:
        """Resolve an opaque object key while preventing path traversal."""

        destination = (self.root / object_key).resolve()
        if not destination.is_relative_to(self.root):
            raise MediaValidationError("Invalid media object key")
        return destination