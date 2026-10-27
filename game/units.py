from abc import abstractmethod, ABC
from typing import Callable, List
from game.interfaces import IMapEntity, INeutralObject


class BaseUnit(IMapEntity):
    """Базовый класс юнита"""
    SYMBOL = "?"
    attack_range: int = 1  #По умолчанию ближний бой (1 клетка)

    def __init__(self, name: str,
                 hp: int,
                 armor: int,
                 attack: int,
                 x: int, y: int,
                 team: str = "player"):
        self.name = name
        self._hp = hp
        self.armor = armor
        self.attack = attack
        self.x = x
        self.y = y
        self.team = team
        self._death_listeners: List[Callable[["BaseUnit"], None]] = []

    def get_symbol(self) -> str:
        # Игрок — заглавные буквы (P, M), Враг — строчные (p, m)
        return self.SYMBOL.upper() if self.team == "player" else self.SYMBOL.lower()

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, value)
        if self._hp == 0:
            for listener in list(self._death_listeners):
                listener(self)

    def add_death_listener(self, callback: Callable[["BaseUnit"], None]) -> None:
        self._death_listeners.append(callback)

    def take_damage(self, raw_damage: int) -> int:
        damage = max(1, raw_damage - self.armor // 2)
        self.hp -= damage
        return damage

    def attack_enemy(self, other: "BaseUnit", is_ranged: bool = False) -> str:
        """Бой с другим отрядом. Если атака дальняя (is_ranged=True), ответного удара нет"""
        old_hp = other.hp
        other.take_damage(self.attack)
        dealt = old_hp - other.hp

        attack_type = "стреляет/колдует в" if is_ranged else "атакует в ближнем бою"
        log = [f"⚔️ {self.name} {attack_type} {other.name} (-{dealt} HP, осталось {other.hp} HP)"]

        # Ответный удар только в ближнем бою, если цель выжила
        if not is_ranged and other.hp > 0:
            my_old_hp = self.hp
            self.take_damage(max(1, other.attack // 2))
            taken = my_old_hp - self.hp
            log.append(f"{other.name} контратакует {self.name} (-{taken} HP, осталось {self.hp} HP)")
            if self.hp <= 0:
                log.append(f"Ваш отряд {self.name} погиб при контратаке!")
        elif other.hp == 0:
            log.append(f"Отряд {other.name} уничтожен!")

        return "\n".join(log)

    def move(self, dx: int, dy: int) -> None:
        self.x += dx
        self.y += dy

    def __add__(self, neutral_obj: INeutralObject) -> str:
        """Перегрузка оператора + для взаимодействия с нейтральным объектом."""
        if not isinstance(neutral_obj, INeutralObject):
            raise TypeError("Оператор + поддерживает только объекты INeutralObject")
        return neutral_obj.interact(self)

    @abstractmethod
    def use_ability(self) -> str:
        pass

    @abstractmethod
    def get_category(self) -> str:
        pass

    def get_info(self) -> str:
        return (
            f"[{self.get_symbol()}] {self.name} ({self.get_category()}) | "
            f"HP: {self.hp}, Броня: {self.armor}, Атака: {self.attack} | "
            f"Позиция: ({self.x}, {self.y}) | "
            f"Дальность: {self.attack_range}"
        )


# Рыцари (2 вида)
class KnightUnit(BaseUnit, ABC):
    def get_category(self) -> str:
        return "Рыцари"


class Paladin(KnightUnit):
    def __init__(self, x: int, y: int):
        super().__init__("Паладин Света", hp=90, armor=10, attack=18, x=x, y=y)

    def get_symbol(self) -> str:
        return "P"

    def use_ability(self) -> str:
        self.hp += 15
        return f"{self.name} исцеляет себя молитвой (+15 HP)."


class DarkKnight(KnightUnit):
    def __init__(self, x: int, y: int):
        super().__init__("Рыцарь Стражи", hp=110, armor=14, attack=15, x=x, y=y)

    def get_symbol(self) -> str:
        return "K"

    def use_ability(self) -> str:
        self.armor += 5
        return f"{self.name} глухо закрывается щитом (+5 к броне)."


# Маги (2 вида)
class MageUnit(BaseUnit, ABC):
    attack_range = 2

    def get_category(self) -> str:
        return "Маги"


class Archmage(MageUnit):
    def __init__(self, x: int, y: int):
        super().__init__("Архимаг Огня", hp=60, armor=4, attack=30, x=x, y=y)

    def get_symbol(self) -> str:
        return "M"

    def use_ability(self) -> str:
        self.attack += 8
        return f"{self.name} заряжает посох первородным пламенем (+8 к атаке)."


class Cleric(MageUnit):
    def __init__(self, x: int, y: int):
        super().__init__("Жрец Храма", hp=75, armor=6, attack=15, x=x, y=y)

    def get_symbol(self) -> str:
        return "C"

    def use_ability(self) -> str:
        self.hp += 20
        return f"{self.name} призывает небесное благословение (+20 HP)."


# Стрелки (2 вида)
class RangerUnit(BaseUnit, ABC):
    attack_range = 3

    def get_category(self) -> str:
        return "Стрелки"


class Crossbowman(RangerUnit):
    def __init__(self, x: int, y: int):
        super().__init__("Арбалетчик", hp=80, armor=8, attack=24, x=x, y=y)

    def get_symbol(self) -> str:
        return "A"

    def use_ability(self) -> str:
        self.attack += 6
        return f"{self.name} устанавливает тяжелые болты (+6 к атаке)."


class ShadowHunter(RangerUnit):
    def __init__(self, x: int, y: int):
        super().__init__("Ночной Охотник", hp=70, armor=5, attack=26, x=x, y=y)

    def get_symbol(self) -> str:
        return "H"

    def use_ability(self) -> str:
        self.armor += 3
        self.attack += 3
        return f"{self.name} уходит в тень (+3 к атаке и броне)."