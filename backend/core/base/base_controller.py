"""Base class for controllers: the TOP layer of a business feature (its only public entry point).

Each feature has exactly ONE controller, exported by the feature package root
(``backend/features/<key>/__init__.py``). Pages never create it themselves: they open it through the
gateway, which gives every call the same mechanism (logging, timing, future extensions)::

    from backend.core.gateway import gateway
    from backend.features.leave_request import LeaveRequestController

    leave = gateway.open(LeaveRequestController)
    result = leave.submit(SubmitLeaveRequest(days=2))

Each public method = ONE use case and only delegates to ONE service (no logic here)::

    class LeaveRequestController(BaseController):
        def submit(self, request: SubmitLeaveRequest) -> LeaveResponse:
            \"\"\"UC-01 Gửi đơn nghỉ phép.\"\"\"
            return SubmitLeaveService().handle(request)
"""

import inspect
import logging
from abc import ABC
from collections.abc import Callable
from typing import Any

from backend.core.logger import get_logger
from backend.core.naming import feature_key_from_module


class BaseController(ABC):
    @classmethod
    def actions(cls) -> dict[str, Callable[..., Any]]:
        """Public use-case methods of this controller (what the gateway exposes)."""
        base_names = set(dir(BaseController))
        return {
            name: member
            for name, member in inspect.getmembers(cls, inspect.isfunction)
            if not name.startswith("_") and name not in base_names
        }

    @classmethod
    def feature_key(cls) -> str | None:
        return feature_key_from_module(cls.__module__)

    @property
    def logger(self) -> logging.Logger:
        return get_logger(type(self).__module__)
