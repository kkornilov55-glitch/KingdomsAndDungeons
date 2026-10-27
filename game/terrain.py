from game.interfaces import ITerrain
from game.units import BaseUnit


class StoneFloor(ITerrain):
    """Каменный пол подземелья — обычный проходимый ландшафт."""

    def get_symbol(self) -> str:
        return "."

    def is_walkable(self) -> bool:
        return True

    def apply_effect(self, unit: BaseUnit) -> str:
        return f"{unit.name} перемещается по каменному полу."


class MagicRuneTile(ITerrain):
    """Древние рунные плиты — дают бонус к броне при прохождении."""

    def get_symbol(self) -> str:
        return "^"

    def is_walkable(self) -> bool:
        return True

    def apply_effect(self, unit: BaseUnit) -> str:
        unit.armor += 1
        return f"Магические руны укрепляют доспехи {unit.name} (+1 к броне)!"


class LavaChasm(ITerrain):
    """Лавовый разлом — непроходимая клетка."""
    def get_symbol(self) -> str:
        return "~"

    def is_walkable(self) -> bool:
        return False

    def apply_effect(self, unit: BaseUnit) -> str:
        return "Путь преграждает кипящая лава! Проход невозможен."