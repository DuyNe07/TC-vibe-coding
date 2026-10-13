"""File upload / download widgets that speak DTOs (the backend never sees Streamlit objects)."""

import mimetypes
from collections.abc import Callable, Sequence

import streamlit as st

from backend.core.base import FileDownloadDTO, UploadedFileDTO


def file_upload(label: str, *, types: Sequence[str], key: str, help: str | None = None) -> UploadedFileDTO | None:
    """Show a file uploader and return the file as ``UploadedFileDTO`` (or None)."""
    uploaded = st.file_uploader(label, type=[t.lstrip(".") for t in types], key=key, help=help)
    if uploaded is None:
        return None
    return UploadedFileDTO(filename=uploaded.name, content=uploaded.getvalue(), mime_type=uploaded.type)


def download_button(
    file: FileDownloadDTO | Callable[[], FileDownloadDTO],
    *,
    label: str,
    key: str,
    primary: bool = False,
    file_name: str | None = None,
) -> None:
    """Download a file. Pass a FUNCTION (``lambda: feature.export(request)``) plus ``file_name`` to build the file only
    when the user clicks - heavy Excel exports then cost nothing on page reruns."""
    if callable(file):
        if not file_name:
            raise ValueError("download_button(<function>) needs file_name")
        build = file
        data, name, mime = (lambda: build().content), file_name, mimetypes.guess_type(file_name)[0]
    else:
        data, name, mime = file.content, file.filename, file.mime_type
    st.download_button(
        label,
        data=data,
        file_name=name,
        mime=mime,
        key=key,
        type="primary" if primary else "secondary",
        icon=":material/download:",
        on_click="ignore",
    )
