"""Registry mapping operation model types to their handlers.

A handler registers itself with the module-level :data:`REGISTRY` via the
:meth:`OperationRegistry.register` decorator. Dispatch is an O(1) dict lookup keyed on the
concrete model type, so adding an operation never touches the orchestrator.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from videospec.errors import OperationError
from videospec.operations.base import OperationHandler

HandlerT = TypeVar("HandlerT", bound=OperationHandler[Any])


class OperationRegistry:
    """Maps operation model types to handler instances."""

    def __init__(self) -> None:
        self._handlers: dict[type[BaseModel], OperationHandler[Any]] = {}

    def register(self, model: type[BaseModel]) -> Callable[[type[HandlerT]], type[HandlerT]]:
        """Decorator registering ``handler_cls`` as the handler for ``model``."""

        def decorator(handler_cls: type[HandlerT]) -> type[HandlerT]:
            if model in self._handlers:
                raise OperationError(f"handler already registered for {model.__name__}")
            self._handlers[model] = handler_cls()
            return handler_cls

        return decorator

    def handler_for(self, op: BaseModel) -> OperationHandler[Any]:
        """Return the handler for ``op``'s type, or raise :class:`OperationError`."""
        try:
            return self._handlers[type(op)]
        except KeyError as exc:
            raise OperationError(f"no handler registered for {type(op).__name__}") from exc


REGISTRY = OperationRegistry()
