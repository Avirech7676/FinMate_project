"""
FinMate 2.0 Security Module
Provides password complexity validation, safe upload verification, and sensitive data sanitization.
"""

import re
from typing import Tuple, Optional
from fastapi import HTTPException, UploadFile


class SecurityValidator:
    ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".pdf"}
    ALLOWED_CSV_EXTENSIONS = {".csv"}
    MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        Ensures password meets enterprise security standards:
        - At least 8 characters
        - Contains uppercase letter
        - Contains lowercase letter
        - Contains a number
        - Contains a special character
        """
        if not password or len(password) < 8:
            return False, "Password must be at least 8 characters long."
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter."
        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter."
        if not re.search(r"[0-9]", password):
            return False, "Password must contain at least one digit."
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>\-_=+/\\~`]", password):
            return False, "Password must contain at least one special character."
        return True, None

    @classmethod
    def validate_upload_file(
        cls,
        file: UploadFile,
        allowed_extensions: Optional[set] = None,
        max_size: Optional[int] = None
    ) -> None:
        """
        Validates file extension and size safely.
        """
        allowed = allowed_extensions or (cls.ALLOWED_IMAGE_EXTENSIONS | cls.ALLOWED_CSV_EXTENSIONS)
        max_bytes = max_size or cls.MAX_FILE_SIZE_BYTES

        filename = file.filename or ""
        ext = "." + filename.split(".")[-1].lower() if "." in filename else ""

        if ext not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(sorted(allowed))}"
            )

        # File size check (if content size available in headers or file spool)
        if file.size and file.size > max_bytes:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds maximum allowed size of {max_bytes // (1024 * 1024)} MB."
            )
