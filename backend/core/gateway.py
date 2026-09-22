"""Gateway: the ONE uniform way the UI runs business actions (in-process, typed, no HTTP).

    from backend.core.gateway import gateway
    from backend.features.sample_product_import import SampleProductImportController

    products = gateway.open(SampleProductImportController)       # typed like the controller
    data = products.list_products(ListProductsRequest(keyword="A"))

Every call goes through ``Gateway.call`` -> middlewares -> controller method -> service -> ...
It logs "<Controller>.<action> done in N ms" (or the failure) into the feature's log.

Extension point: register a ``GatewayMiddleware`` (permissions, audit trail, caching, remote transport...)
with ``gateway.use(...)`` in the framework - features and pages do not change.
"""

import functools
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeVar, cast

from backend.core.base.base_controller import BaseController
from backend.core.exceptions import AppError, ConfigurationError
from backend.core.logger import get_logger

TController = TypeVar("TController", bound=BaseController)


@dataclass(frozen=True)
class GatewayCall:
    feature_key: str | None
    controller: BaseController
    action: str
    request: Any

    @property
    def name(self) -> str:
        return f"{type(self.controller).__name__}.{self.action}"


class GatewayMiddleware(ABC):
    """Wraps every call. Call ``proceed(call)`` to continue the chain (or raise to stop it)."""

    @abstractmethod
    def handle(self, call: GatewayCall, proceed: Callable[[GatewayCall], Any]) -> Any: ...


class Gateway:
    """
    The single entry point for running business logic.

    Pages never import services or repositories directly.
    Instead, each feature exposes ONE controller class:

        class MyFeatureController(BaseController):
            def my_action(self, req: MyActionRequest) -> MyActionResponse:
                return MyActionService().handle(req)

    Then in a page:

        from backend.core.gateway import gateway
        from backend.features.my_feature import MyFeatureController

        ctrl = gateway.open(MyFeatureController)
        response = ctrl.my_action(MyActionRequest(...))

    All calls are routed through Gateway.call() and can be intercepted by middlewares.
    """

    def __init__(self) -> None:
        self._middlewares: list[GatewayMiddleware] = []

    def use(self, middleware: GatewayMiddleware) -> None:
        self._middlewares.append(middleware)

    def open(self, controller_cls: type[TController]) -> TController:
        """Return the controller of a feature, with every action routed through the gateway."""
        if not (isinstance(controller_cls, type) and issubclass(controller_cls, BaseController)):
            raise ConfigurationError(f"gateway.open() expects a BaseController subclass, got {controller_cls!r}")
        return cast(TController, _ControllerProxy(self, controller_cls()))

    def call(self, controller: BaseController, action: str, request: Any) -> Any:
        logger = get_logger(type(controller).__module__)
        call = GatewayCall(type(controller).feature_key(), controller, action, request)
        started = time.perf_counter()
        try:
            result = self._chain(0)(call)
        except AppError as exc:
            logger.warning("%s failed: [%s] %s", call.name, exc.code, exc.message)
            raise
        except Exception:
            logger.exception("%s crashed", call.name)
            raise
        logger.info("%s done in %.0f ms", call.name, (time.perf_counter() - started) * 1000)
        return result

    def _chain(self, index: int) -> Callable[[GatewayCall], Any]:
        if index == len(self._middlewares):
            return lambda call: getattr(call.controller, call.action)(call.request)
        middleware, proceed = self._middlewares[index], self._chain(index + 1)
        return lambda call: middleware.handle(call, proceed)


class _ControllerProxy:
    """Looks like the controller; each public action is executed through ``Gateway.call``."""

    def __init__(self, gateway: Gateway, controller: BaseController) -> None:
        self._gateway = gateway
        self._controller = controller
        self._actions = type(controller).actions()

    def __getattr__(self, name: str) -> Callable[[Any], Any]:
        if name not in self._actions:
            raise AttributeError(f"{type(self._controller).__name__} has no action {name!r}")

        @functools.wraps(self._actions[name])
        def run(request: Any = None) -> Any:
            return self._gateway.call(self._controller, name, request)

        return run


gateway = Gateway()
