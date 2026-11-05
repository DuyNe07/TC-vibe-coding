"""Errors of feature "Năng suất xưởng may". Messages are shown to users."""

from backend.core.exceptions import AppError, FileProcessingError


class SewingProductivityError(AppError):
    code = "SEWING_PRODUCTIVITY_ERROR"
    default_message = "Có lỗi trong chức năng Năng suất xưởng may."


class UploadFileError(FileProcessingError):
    """The data file cannot be read or is too big (BR-01)."""

    code = "SEWING_UPLOAD_FILE"
    default_message = (
        "File phải có định dạng .xlsx, không quá 50 MB và mỗi sheet không quá 200.000 dòng. "
        "Hãy kiểm tra lại rồi tải lên."
    )
