"""File upload / download widgets that speak DTOs (the backend never sees Streamlit objects)."""

from collections.abc import Sequence

import streamlit as st

from backend.core.base import FileDownloadDTO, UploadedFileDTO


def file_upload(label: str, *, types: Sequence[str], key: str, help: str | None = None) -> UploadedFileDTO | None:
    """Show a file uploader and return the file as ``UploadedFileDTO`` (or None)."""
    uploaded = st.file_uploader(label, type=[t.lstrip(".") for t in types], key=key, help=help)
    if uploaded is None:
        return None
    return UploadedFileDTO(filename=uploaded.name, content=uploaded.getvalue(), mime_type=uploaded.type)


def download_button(file: FileDownloadDTO, *, label: str, key: str, primary: bool = False) -> None:
    st.download_button(
        label,
        data=file.content,
        file_name=file.filename,
        mime=file.mime_type,
        key=key,
        type="primary" if primary else "secondary",
        icon="⬇️",
        on_click="ignore",
    )
