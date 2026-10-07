from pathlib import Path


ALLOWED_EXTENSIONS = {".csv", ".xlsx"}
MAX_FILE_SIZE_MB = 100
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


class FileValidationError(ValueError):
    """Raised when an uploaded dataset fails validation."""


def validate_file(
    file_name: str,
    file_size_bytes: int,
) -> None:
    """Validate an uploaded dataset before loading it."""

    extension = Path(file_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            f"Unsupported file type '{extension}'. "
            f"Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )

    if file_size_bytes <= 0:
        raise FileValidationError(
            "The uploaded file is empty."
        )

    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        raise FileValidationError(
            f"File exceeds the {MAX_FILE_SIZE_MB} MB limit."
        )