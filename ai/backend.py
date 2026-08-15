from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable


class AIBackend(ABC):
    name: str = "AI"

    @abstractmethod
    def complete(
        self,
        system: str,
        messages: list[dict],
        on_delta: Callable[[str], None] | None = None,
    ) -> str:
        ...

    def is_available(self) -> bool:
        return True
