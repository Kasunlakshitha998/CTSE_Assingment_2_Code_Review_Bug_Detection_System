"""
File Reader Tool - Safely reads source code files from disk.

This tool is used by the Code Parser Agent to load source code
files for analysis. It includes comprehensive error handling,
encoding detection, and file validation.
"""

import os
import logging
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Logger
# ---------------------------------------------------------------------------
logger = logging.getLogger("ai_code_review.tools.file_reader")


# ---------------------------------------------------------------------------
# Supported extensions (expand as needed)
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {
    ".py", ".js", ".ts", ".java", ".c", ".cpp", ".h", ".hpp",
    ".cs", ".go", ".rb", ".php", ".swift", ".kt", ".rs",
    ".html", ".css", ".sql", ".sh", ".bat", ".yaml", ".yml",
    ".json", ".xml", ".toml", ".cfg", ".ini", ".md", ".txt",
    ".jsx", ".tsx", ".vue", ".dart", ".scala", ".r", ".m",
}

# Maximum file size in bytes (5 MB)
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


def read_code_file(file_path: str) -> Dict[str, Any]:
    """Read a source code file safely and return its content with metadata.

    This function validates the file path, checks the file extension,
    enforces a size limit, and reads the content with proper encoding
    handling.  It is designed for production use and never raises
    uncaught exceptions.

    Args:
        file_path (str): Absolute or relative path to the source code file.

    Returns:
        Dict[str, Any]: A dictionary with the following keys:
            - ``success`` (bool): Whether the file was read successfully.
            - ``file_path`` (str): Normalised absolute path to the file.
            - ``content`` (str): The raw content of the file (empty on error).
            - ``lines`` (int): Total number of lines in the file.
            - ``size_bytes`` (int): Size of the file in bytes.
            - ``extension`` (str): File extension (e.g. ``.py``).
            - ``error`` (str | None): Error message if the read failed.

    Raises:
        This function does **not** raise exceptions.  All errors are
        captured and returned in the ``error`` field of the result dict.
    """

    result: Dict[str, Any] = {
        "success": False,
        "file_path": "",
        "content": "",
        "lines": 0,
        "size_bytes": 0,
        "extension": "",
        "error": None,
    }

    try:
        # ---- Validate input ------------------------------------------------
        if not file_path or not isinstance(file_path, str):
            result["error"] = "Invalid file path: path must be a non-empty string."
            logger.error(result["error"])
            return result

        abs_path = os.path.abspath(file_path)
        result["file_path"] = abs_path

        # ---- Check existence -----------------------------------------------
        if not os.path.exists(abs_path):
            result["error"] = f"File not found: {abs_path}"
            logger.error(result["error"])
            return result

        if not os.path.isfile(abs_path):
            result["error"] = f"Path is not a file: {abs_path}"
            logger.error(result["error"])
            return result

        # ---- Check extension -----------------------------------------------
        _, ext = os.path.splitext(abs_path)
        ext = ext.lower()
        result["extension"] = ext

        if ext not in SUPPORTED_EXTENSIONS:
            result["error"] = (
                f"Unsupported file extension '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            )
            logger.warning(result["error"])
            return result

        # ---- Check size ----------------------------------------------------
        file_size = os.path.getsize(abs_path)
        result["size_bytes"] = file_size

        if file_size > MAX_FILE_SIZE_BYTES:
            result["error"] = (
                f"File too large ({file_size:,} bytes). "
                f"Maximum allowed: {MAX_FILE_SIZE_BYTES:,} bytes."
            )
            logger.warning(result["error"])
            return result

        if file_size == 0:
            result["error"] = "File is empty (0 bytes)."
            logger.warning(result["error"])
            return result

        # ---- Read content --------------------------------------------------
        encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
        content = None

        for encoding in encodings_to_try:
            try:
                with open(abs_path, "r", encoding=encoding) as fh:
                    content = fh.read()
                break
            except (UnicodeDecodeError, ValueError):
                continue

        if content is None:
            result["error"] = (
                f"Failed to decode file with encodings: {encodings_to_try}"
            )
            logger.error(result["error"])
            return result

        # ---- Success -------------------------------------------------------
        result["success"] = True
        result["content"] = content
        result["lines"] = content.count("\n") + 1
        logger.info(
            "Successfully read file: %s (%d lines, %d bytes)",
            abs_path,
            result["lines"],
            file_size,
        )
        return result

    except PermissionError:
        result["error"] = f"Permission denied: {file_path}"
        logger.error(result["error"])
        return result
    except OSError as exc:
        result["error"] = f"OS error reading file: {exc}"
        logger.error(result["error"])
        return result
    except Exception as exc:  # pragma: no cover – safety net
        result["error"] = f"Unexpected error: {exc}"
        logger.exception(result["error"])
        return result
