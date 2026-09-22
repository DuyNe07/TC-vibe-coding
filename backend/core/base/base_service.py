"""Base class for services (``services/`` folder). ONE service = ONE use case (called by ONE controller method).

    class CreateOrderService(BaseService[CreateOrderRequest, OrderResponse]):
        def __init__(self, repository: OrderRepository | None = None) -> None:
            self.repository = repository or OrderRepository()

        def execute(self, request: CreateOrderRequest) -> OrderResponse:
            ...  # orchestrate: repository -> business -> builder -> response DTO

``handle()`` is the fixed template method (validate input -> execute -> check output). Never override it.
"""

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import Any, ClassVar, Generic, TypeVar

from pydantic import ValidationError as PydanticValidationError

from backend.core.base._generics import generic_args, is_abstract
from backend.core.base.base_dto import BaseRequestDTO, BaseResponseDTO
from backend.core.exceptions import ConfigurationError, InvalidInputError
from backend.core.logger import get_logger

TRequest = TypeVar("TRequest", bound=BaseRequestDTO)
TResponse = TypeVar("TResponse", bound=BaseResponseDTO)


class BaseService(ABC, Generic[TRequest, TResponse]):
    request_model: ClassVar[type[BaseRequestDTO]]
    response_model: ClassVar[type[BaseResponseDTO]]

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if "handle" in cls.__dict__:
            raise ConfigurationError(f"{cls.__name__} must not override handle(); implement execute()")
        args = generic_args(cls, BaseService)
        if len(args) == 2 and all(isinstance(a, type) for a in args):
            request_model, response_model = args
            if not issubclass(request_model, BaseRequestDTO):
                raise ConfigurationError(f"{cls.__name__}: request type must inherit BaseRequestDTO")
            if not issubclass(response_model, BaseResponseDTO):
                raise ConfigurationError(f"{cls.__name__}: response type must inherit BaseResponseDTO")
            cls.request_model, cls.response_model = request_model, response_model
        elif not is_abstract(cls) and not hasattr(cls, "request_model"):
            raise ConfigurationError(f"Declare {cls.__name__} as BaseService[MyRequest, MyResponse]")

    @property
    def logger(self) -> logging.Logger:
        return get_logger(type(self).__module__)

    def handle(self, payload: Any = None) -> TResponse:
        """Called by the controller: validate the request -> execute() -> check the response type.

        Start/end are logged at DEBUG; the gateway logs the result/failure of the call at INFO/WARNING.
        """
        name = type(self).__name__
        started = time.perf_counter()
        self.logger.debug("%s started", name)
        response = self.execute(self._parse_request(payload))
        if not isinstance(response, self.response_model):
            raise ConfigurationError(
                f"{name}.execute() must return {self.response_model.__name__}, got {type(response).__name__}"
            )
        self.logger.debug("%s finished in %.0f ms", name, (time.perf_counter() - started) * 1000)
        return response

    @abstractmethod
    def execute(self, request: TRequest) -> TResponse:
        """Implement the use case here."""

    def _parse_request(self, payload: Any) -> TRequest:
        if isinstance(payload, self.request_model):
            return payload  # type: ignore[return-value]
        try:
            if payload is None:
                return self.request_model()  # type: ignore[return-value]
            if isinstance(payload, Mapping):
                return self.request_model.model_validate(dict(payload))  # type: ignore[return-value]
        except PydanticValidationError as exc:
            raise InvalidInputError.from_pydantic(exc) from exc
        raise InvalidInputError(f"Cần dữ liệu kiểu {self.request_model.__name__}, nhận được {type(payload).__name__}.")
