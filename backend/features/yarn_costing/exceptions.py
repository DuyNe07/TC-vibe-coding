"""Errors of feature "Tính giá sợi". Messages are shown to users."""

from backend.core.exceptions import AppError, FileProcessingError, NotFoundError


class YarnCostingError(AppError):
    code = "YARN_COSTING_ERROR"
    default_message = "Có lỗi trong chức năng Tính giá sợi."


class YarnValidationError(YarnCostingError):
    """Input that fails a check of a use case (messages from section 6 of the business document)."""

    code = "YARN_VALIDATION"
    default_message = "Dữ liệu nhập chưa hợp lệ."


class YarnNotFoundError(NotFoundError):
    code = "YARN_NOT_FOUND"
    default_message = "Không tìm thấy dữ liệu."


class ImportFileError(FileProcessingError):
    code = "YARN_IMPORT_FILE"
    default_message = "Không đọc được file. Hãy dùng file mẫu."


class DataFileError(YarnCostingError):
    """A stored data file (for example one copied from the previous app) can not be read (BR-61)."""

    code = "YARN_DATA_FILE"
    default_message = "Không đọc được dữ liệu. Vui lòng chép lại file dữ liệu từ app cũ (thư mục data\\yarn_costing)."
