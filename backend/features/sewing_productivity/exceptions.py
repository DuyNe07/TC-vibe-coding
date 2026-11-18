"""Errors of feature "Năng suất xưởng may". Messages are shown to users."""

from backend.core.exceptions import AppError, ConflictError, FileProcessingError


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


class SaveInProgressError(ConflictError):
    """Fix log 2026-11-16: a second "Check & save" while one is still running (another click, another tab)."""

    code = "SEWING_SAVE_IN_PROGRESS"
    default_message = (
        "Đang lưu một file khác, chưa lưu file này. Hãy chờ khoảng một phút rồi xem dòng mới trong lịch sử tải file "
        "bên dưới; nếu chưa có, bấm Check & save lại."
    )
