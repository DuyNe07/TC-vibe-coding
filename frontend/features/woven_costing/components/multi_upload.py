"""Upload 1-4 files at once (Peace / WFX fabric data)."""

from collections.abc import Sequence

import streamlit as st

from backend.core.base import UploadedFileDTO


def multi_file_upload(label: str, *, types: Sequence[str], key: str, max_files: int = 4) -> list[UploadedFileDTO]:
    uploaded = st.file_uploader(label, type=[t.lstrip(".") for t in types], accept_multiple_files=True, key=key) or []
    if len(uploaded) > max_files:
        st.warning(f"Chỉ chọn tối đa {max_files} file.", icon="⚠️")
        uploaded = uploaded[:max_files]
    return [UploadedFileDTO(filename=f.name, content=f.getvalue(), mime_type=f.type) for f in uploaded]
