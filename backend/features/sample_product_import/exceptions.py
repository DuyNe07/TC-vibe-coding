"""Errors of feature "Nhập sản phẩm từ Excel (mẫu)". Messages are user-facing (Vietnamese)."""

from backend.core.exceptions import AppError, FileProcessingError


class SampleProductImportError(AppError):
    code = "SAMPLE_PRODUCT_IMPORT_ERROR"
    default_message = "Có lỗi trong chức năng Nhập sản phẩm từ Excel (mẫu)."


class ImportFileError(FileProcessingError):
    code = "IMPORT_FILE_ERROR"
    default_message = "File nhập không đúng mẫu."
