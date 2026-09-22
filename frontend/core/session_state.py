"""Namespaced wrapper around ``st.session_state`` so features never overwrite each other's keys."""

from typing import Any

import streamlit as st


class SessionState:
    def __init__(self, namespace: str) -> None:
        self._prefix = f"{namespace}::"

    def key(self, name: str) -> str:
        """Namespaced key; also use it for widget ``key=`` arguments."""
        return f"{self._prefix}{name}"

    def get(self, name: str, default: Any = None) -> Any:
        return st.session_state.get(self.key(name), default)

    def set(self, name: str, value: Any) -> None:
        st.session_state[self.key(name)] = value

    def pop(self, name: str, default: Any = None) -> Any:
        return st.session_state.pop(self.key(name), default)

    def has(self, name: str) -> bool:
        return self.key(name) in st.session_state

    def clear(self) -> None:
        for key in [k for k in st.session_state if str(k).startswith(self._prefix)]:
            del st.session_state[key]
