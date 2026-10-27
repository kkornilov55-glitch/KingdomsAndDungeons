import copy
import random
from typing import Dict, List, Optional, Tuple
from game.base import CastleBase
from game.interfaces import INeutralObject, ITerrain
from game.terrain import StoneFloor
from game.units import BaseUnit


class DungeonField:
    """Игровое поле — контейнер для ландшафта, базы, юнитов и нейтральных объектов"""
    def __init__(self, width: int, height: int, max_objects: int = 15):
        self.width = width
        self.height = height
        self.max_objects = max_objects

        self.terrain: List[List[ITerrain]] = [
            [StoneFloor() for _ in range(width)] for _ in range(height)
        ]
        self.neutral_objects: Dict[Tuple[int, int], INeutralObject] = {}
        self.units: Dict[Tuple[int, int], BaseUnit] = {}
        self.base: Optional[CastleBase] = None
        self.enemy_base: Optional[CastleBase] = None

    @property
    def total_objects(self) -> int:
        bases = (1 if self.base else 0) + (1 if self.enemy_base else 0)
        return bases + len(self.neutral_objects) + len(self.units)

    def is_inside(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def set_terrain(self, x: int, y: int, terrain_obj: ITerrain) -> None:
        if self.is_inside(x, y):
            self.terrain[y][x] = terrain_obj

    def place_base(self, base: CastleBase) -> bool:
        if self.total_objects >= self.max_objects:
            return False
        if base.team == "player":
            self.base = base
        else:
            self.enemy_base = base
        return True

    def add_neutral(self, x: int, y: int, obj: INeutralObject) -> bool:
        if not self.is_inside(x, y) or self.total_objects >= self.max_objects:
            return False
        self.neutral_objects[(x, y)] = obj
        return True

    def add_unit(self, unit: BaseUnit) -> bool:
        pos = (unit.x, unit.y)
        if not self.is_inside(unit.x, unit.y) or self.total_objects >= self.max_objects:
            return False
        if not self.terrain[unit.y][unit.x].is_walkable() or pos in self.units:
            return False

        self.units[pos] = unit
        unit.add_death_listener(lambda u: self.remove_unit(u.x, u.y))
        return True

    def remove_unit(self, x: int, y: int) -> Optional[BaseUnit]:
        return self.units.pop((x, y), None)

    def find_spawn_point(self, target_base: Optional[CastleBase] = None) -> Optional[Tuple[int, int]]:
        b = target_base or self.base
        if not b:
            return None
        for dx, dy in [(1, 0), (0, 1), (-1, 0), (0, -1), (1, 1), (-1, -1)]:
            nx, ny = b.x + dx, b.y + dy
            if self.is_inside(nx, ny) and self.terrain[ny][nx].is_walkable():
                if (nx, ny) not in self.units:
                    return nx, ny
        return None

    def move_unit(self, unit: BaseUnit, dx: int, dy: int) -> str:
        nx, ny = unit.x + dx, unit.y + dy
        if not self.is_inside(nx, ny):
            return "Выход за границы поля невозможен!"

        cell_terrain = self.terrain[ny][nx]
        if not cell_terrain.is_walkable():
            return cell_terrain.apply_effect(unit)

        for b in [self.base, self.enemy_base]:
            if b and b.hp > 0 and (nx, ny) == (b.x, b.y):
                if b.team == unit.team:
                    return "Нельзя встать на собственную базу!"
                b.hp = max(0, b.hp - unit.attack)
                return f"{unit.name} штурмует базу [{b.get_symbol()}] (-{unit.attack} HP, у базы осталось {b.hp} HP)!"

        # Ближний бой при шаге на клетку с юнитом
        if (nx, ny) in self.units:
            other = self.units[(nx, ny)]
            if other.team == unit.team:
                return "Клетка занята союзником!"
            combat_msg = unit.attack_enemy(other, is_ranged=False)
            if other.hp == 0 and unit.hp > 0:
                self.remove_unit(unit.x, unit.y)
                unit.move(dx, dy)
                self.units[(nx, ny)] = unit
            return combat_msg

        self.remove_unit(unit.x, unit.y)
        unit.move(dx, dy)
        self.units[(nx, ny)] = unit

        log = [cell_terrain.apply_effect(unit)]
        if (nx, ny) in self.neutral_objects:
            neutral = self.neutral_objects.pop((nx, ny))
            log.append(unit + neutral)
            if unit.hp == 0:
                log.append(f"Отряд {unit.name} пал!")

        return "\n".join(log)

    def ranged_attack(self, unit: BaseUnit, target_x: int, target_y: int) -> str:
        """Дальняя атака для Магов и Стрелков по координатам цели."""
        if unit.attack_range <= 1:
            return f"{unit.name} — боец ближнего боя и не умеет атаковать издалека!"

        dist = abs(unit.x - target_x) + abs(unit.y - target_y)
        if dist == 0 or dist > unit.attack_range:
            return f"Цель вне радиуса досягаемости! (Дистанция: {dist}, макс. дальность: {unit.attack_range})"

        # Проверка попадания по вражеской базе
        if self.enemy_base and self.enemy_base.hp > 0 and (target_x, target_y) == (self.enemy_base.x,
                                                                                   self.enemy_base.y):
            if self.enemy_base.team != unit.team:
                self.enemy_base.hp = max(0, self.enemy_base.hp - unit.attack)
                return f"🏹 {unit.name} обстреливает базу [C] (-{unit.attack} HP, осталось {self.enemy_base.hp} HP)!"

        # Проверка попадания по вражескому юниту
        target = self.units.get((target_x, target_y))
        if not target or target.team == unit.team:
            return "На указанной клетке нет врага!"

        return unit.attack_enemy(target, is_ranged=True)

    def enemy_turn(self) -> str:
        """Автоматический ход всех врагов после действия игрока."""
        if not self.enemy_base:
            return ""
        logs = ["--- ОТВЕТНЫЙ ХОД ВРАГА ---"]

        player_targets = list(self.base.units) if self.base else []

        for enemy in list(self.enemy_base.units):
            if enemy.hp == 0:
                continue

            # Если враг — стрелок/маг и кто-то из наших в радиусе обстрела, бьет издалека
            attacked = False
            if enemy.attack_range > 1:
                for pt in player_targets:
                    if pt.hp > 0 and abs(enemy.x - pt.x) + abs(enemy.y - pt.y) <= enemy.attack_range:
                        logs.append(enemy.attack_enemy(pt, is_ranged=True))
                        attacked = True
                        break
            if attacked:
                continue

            # Иначе враг делает шаг к ближайшему юниту игрока (или к замку B)
            goals = [(u.x, u.y) for u in player_targets if u.hp > 0]
            if self.base and self.base.hp > 0:
                goals.append((self.base.x, self.base.y))
            if not goals:
                break

            tx, ty = min(goals, key=lambda p: abs(p[0] - enemy.x) + abs(p[1] - enemy.y))
            dx = 1 if tx > enemy.x else (-1 if tx < enemy.x else 0)
            dy = 1 if ty > enemy.y else (-1 if ty < enemy.y else 0)

            for step_x, step_y in [(dx, 0), (0, dy)]:
                if step_x == 0 and step_y == 0:
                    continue
                nx, ny = enemy.x + step_x, enemy.y + step_y
                if self.is_inside(nx, ny) and self.terrain[ny][nx].is_walkable():
                    if (nx, ny) in self.units and self.units[(nx, ny)].team == "enemy":
                        continue
                    logs.append(f"[{enemy.get_symbol().lower()}] " + self.move_unit(enemy, step_x, step_y))
                    break

        # Вражеская база C с шансом 40% призывает подкрепление (до 3 юнитов)
        if self.enemy_base.can_spawn() and len(self.enemy_base.units) < 3 and random.random() < 0.4:
            pos = self.find_spawn_point(self.enemy_base)
            if pos:
                u = self.enemy_base.create_unit(random.choice(["2", "3", "5"]), pos[0], pos[1])
                if u and self.add_unit(u):
                    logs.append(
                        f"База [C] призвала подкрепление: {u.name} [{u.get_symbol().lower()}] на ({pos[0]}, {pos[1]})!")

        return "\n".join(logs)

    def copy_field(self) -> "DungeonField":
        """Копирование поля вместе со всеми объектами на нем"""
        return copy.deepcopy(self)

    def render(self) -> str:
        border = "X " * (self.width + 2)
        rows = [border]
        for y in range(self.height):
            line = ["X"]
            for x in range(self.width):
                if self.base and self.base.hp > 0 and (self.base.x, self.base.y) == (x, y):
                    line.append(self.base.get_symbol())
                elif self.enemy_base and self.enemy_base.hp > 0 and (self.enemy_base.x, self.enemy_base.y) == (x, y):
                    line.append(self.enemy_base.get_symbol())
                elif (x, y) in self.units:
                    u = self.units[(x, y)]
                    sym = u.get_symbol()
                    line.append(sym if u.team == "player" else sym.lower())
                else:
                    line.append(self.terrain[y][x].get_symbol())
            line.append("X")
            rows.append(" ".join(line))
        rows.append(border)
        return "\n".join(rows)