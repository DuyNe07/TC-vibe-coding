"""Data warnings shown at the top of each screen (BR-61: a data file of the previous app could not be imported)."""

import streamlit as st

from backend.features.yarn_costing.dto.reference_dto import ReferenceDataResponse


def show_data_warnings(reference: ReferenceDataResponse | None = None) -> None:
    for warning in reference.data_warnings if reference is not None else []:
        st.warning(warning, icon="⚠️")
