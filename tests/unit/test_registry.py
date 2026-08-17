"""Registry registration and dispatch."""

from __future__ import annotations

import pytest
from pydantic import BaseModel

from videospec.errors import OperationError
from videospec.models.storyboard import StoryboardOperation
from videospec.operations.base import OperationContext, OperationResult
from videospec.operations.registry import REGISTRY, OperationRegistry


class _Model(BaseModel):
    pass


class _Other(BaseModel):
    pass


def test_register_and_dispatch() -> None:
    registry = OperationRegistry()

    @registry.register(_Model)
    class _Handler:
        def run(self, op: BaseModel, ctx: OperationContext) -> OperationResult:
            raise NotImplementedError

    handler = registry.handler_for(_Model())
    assert handler.__class__.__name__ == "_Handler"


def test_duplicate_registration_raises() -> None:
    registry = OperationRegistry()

    @registry.register(_Model)
    class _First:
        def run(self, op: BaseModel, ctx: OperationContext) -> OperationResult:
            raise NotImplementedError

    with pytest.raises(OperationError, match="already registered"):

        @registry.register(_Model)
        class _Second:
            def run(self, op: BaseModel, ctx: OperationContext) -> OperationResult:
                raise NotImplementedError


def test_unknown_model_raises() -> None:
    registry = OperationRegistry()
    with pytest.raises(OperationError, match="no handler registered"):
        registry.handler_for(_Other())


def test_global_registry_has_storyboard() -> None:
    import videospec.operations  # noqa: F401 - trigger registration

    handler = REGISTRY.handler_for(StoryboardOperation())
    assert handler.__class__.__name__ == "StoryboardHandler"
