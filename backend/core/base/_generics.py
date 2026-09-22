"""Helpers to read generic arguments, e.g. ``BaseService[MyRequest, MyResponse]``."""

import inspect
from typing import Any, get_args, get_origin


def generic_args(cls: type, base: type) -> tuple[Any, ...]:
    """Return the type arguments ``cls`` passed to ``base`` (or a subclass of it) in its class statement."""
    for orig in getattr(cls, "__orig_bases__", ()):
        origin = get_origin(orig)
        if isinstance(origin, type) and issubclass(origin, base):
            return get_args(orig)
    return ()


def is_abstract(cls: type) -> bool:
    """True while abstract methods remain unimplemented (works inside ``__init_subclass__``)."""
    for name in dir(cls):
        if getattr(getattr(cls, name, None), "__isabstractmethod__", False):
            return True
    return inspect.isabstract(cls)
