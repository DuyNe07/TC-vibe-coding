"""Errors of feature "Tính giá vải dệt". Messages are shown to users."""

from backend.core.exceptions import AppError, FileProcessingError


class WovenCostingError(AppError):
    code = "WOVEN_COSTING_ERROR"
    default_message = "Có lỗi trong chức năng Tính giá vải dệt."


class WovenFileError(FileProcessingError):
    code = "WOVEN_FILE_ERROR"
    default_message = "File không đúng mẫu."


class CostsheetNotFoundError(AppError):
    code = "COSTSHEET_NOT_FOUND"
    default_message = "Không tìm thấy costsheet."


class CostsheetValidationError(AppError):
    """Several messages of one action (BR-42, BR-43, BR-44, BR-14...): ``details`` is the list of sentences."""

    code = "COSTSHEET_VALIDATION"
    default_message = "Costsheet chưa hợp lệ."
