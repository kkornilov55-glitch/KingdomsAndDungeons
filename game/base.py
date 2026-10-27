from typing import Dict, List, Optional
from game.interfaces import IMapEntity
from game.units import (
    Archmage,
    BaseUnit,
    Cleric,
    Crossbowman,
    DarkKnight,
    Paladin,
    ShadowHunter,
)


class CastleBase(IMapEntity):
    """Класс базы игрока (Средневековый замок)"""

    UNIT_RECIPES = {
        "1": ("Паладин Света", Paladin),
        "2": ("Рыцарь Стражи", DarkKnight),
        "3": ("Архимаг Огня", Archmage),
        "4": ("Жрец Храма", Cleric),
        "5": ("Арбалетчик", Crossbowman),
        "6": ("Ночной Охотник", ShadowHunter),
    }

    def __init__(self, x: int, y: int,
                 max_units: int = 5,
                 team: str = "player",
                 symbol: str = "B"):
        self.x = x
        self.y = y
        self.hp = 500
        self.max_units = max_units
        self.team = team
        self._symbol = symbol
        self.units: List[BaseUnit] = []

    def get_symbol(self) -> str:
        return self._symbol

    def can_spawn(self) -> bool:
        return len(self.units) < self.max_units and self.hp > 0

    def create_unit(self, key: str, spawn_x: int, spawn_y: int) -> Optional[BaseUnit]:
        if not self.can_spawn() or key not in self.UNIT_RECIPES:
            return None

        _, unit_cls = self.UNIT_RECIPES[key]
        unit = unit_cls(spawn_x, spawn_y)
        unit.add_death_listener(self.on_unit_destroyed)
        self.units.append(unit)
        return unit

    def on_unit_destroyed(self, unit: BaseUnit) -> None:
        if unit in self.units:
            self.units.remove(unit)

    def get_status(self) -> str:
        counts: Dict[str, int] = {"Рыцари": 0, "Маги": 0, "Стрелки": 0}
        for u in self.units:
            counts[u.get_category()] += 1

        return (
            f"=== СОСТОЯНИЕ ЗАМКА ===\n"
            f"Здоровье стен: {self.hp}\n"
            f"Численность войска: {len(self.units)} / {self.max_units} ед.\n"
            f"Из них -> Рыцари: {counts['Рыцари']} | Маги: {counts['Маги']} | Стрелки: {counts['Стрелки']}"
        )