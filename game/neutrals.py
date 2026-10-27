from game.interfaces import INeutralObject
from game.units import BaseUnit


class HealingGrail(INeutralObject):
    """Чаша Грааля — восстанавливает здоровье."""

    def get_symbol(self) -> str:
        return "+"

    def interact(self, unit: BaseUnit) -> str:
        unit.hp += 20
        return f"{unit.name} испил из Чаши Грааля (+20 HP)."


class RunicForge(INeutralObject):
    """Рунная кузница — повышает атаку."""

    def get_symbol(self) -> str:
        return "F"

    def interact(self, unit: BaseUnit) -> str:
        unit.attack += 5
        return f"{unit.name} улучшил оружие в кузнице (+5 к атаке)."


class DragonShrine(INeutralObject):
    """Алтарь дракона — повышает броню."""

    def get_symbol(self) -> str:
        return "S"

    def interact(self, unit: BaseUnit) -> str:
        unit.armor += 4
        return f"{unit.name} получил благословение Алтаря (+4 к броне)."


class CursedChest(INeutralObject):
    """Проклятый сундук — наносит урон отряду."""

    def get_symbol(self) -> str:
        return "?"

    def interact(self, unit: BaseUnit) -> str:
        unit.take_damage(50)
        return f"Сундук оказался ловушкой! {unit.name} получает тяжелый урон."