from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from game.units import BaseUnit


class IMapEntity(ABC):
    """Любой объект, размещаемый на карте."""
    @abstractmethod
    def get_symbol(self) -> str:
        pass


class ITerrain(IMapEntity):
    """Класс ландшафта."""
    @abstractmethod
    def is_walkable(self) -> bool:
        pass

    @abstractmethod
    def apply_effect(self, unit: "BaseUnit") -> str:
        pass


class INeutralObject(IMapEntity):
    """Нейтральный объект поля."""
    @abstractmethod
    def interact(self, unit: "BaseUnit") -> str:
        pass