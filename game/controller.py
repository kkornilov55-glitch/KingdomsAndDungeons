from typing import Optional
from game.base import CastleBase
from game.field import DungeonField
from game.neutrals import CursedChest, DragonShrine, HealingGrail, RunicForge
from game.terrain import LavaChasm, MagicRuneTile


class GameController:
    """Консольный контроллер для управления базой, юнитами и полем  """
    def __init__(self):
        self.field = self._init_world()
        self.saved_copy: Optional[DungeonField] = None

    def _init_world(self) -> DungeonField:
        field = DungeonField(width=10, height=10, max_objects=15)
        base = CastleBase(x=0, y=0, max_units=5)
        field.place_base(base)

        for rx, ry in [(2, 2), (3, 2), (6, 5)]:
            field.set_terrain(rx, ry, MagicRuneTile())
        for lx, ly in [(4, 4), (4, 5), (4, 6)]:
            field.set_terrain(lx, ly, LavaChasm())

        field.add_neutral(2, 0, HealingGrail())
        field.add_neutral(0, 3, RunicForge())
        field.add_neutral(5, 2, DragonShrine())
        field.add_neutral(1, 2, CursedChest())

        starter_unit = base.create_unit("1", 1, 0)
        if starter_unit:
            field.add_unit(starter_unit)

        # Вражеская база [C] в правом нижнем углу и 2 стартовых врага
        enemy_base = CastleBase(x=9, y=9, max_units=4, team="enemy", symbol="C")
        field.place_base(enemy_base)
        for key, ex, ey in [("2", 8, 9), ("3", 9, 8)]:
            eu = enemy_base.create_unit(key, ex, ey)
            field.add_unit(eu)


        return field

    def run(self) -> None:
        while True:
            if self.field.enemy_base and self.field.enemy_base.hp == 0 and not self.field.enemy_base.units:
                print("ПОБЕДА!")
                break
            elif self.field.base and self.field.base.hp == 0:
                print("ПОРАЖЕНИЕ")
                break

            print("\n" + self.field.render())
            print(
                "Обозначения: [B] Замок | [.] Пол | [^] Руны | [~] Лава\n"
                "Нейтральные объекты: [+] Грааль | [F] Кузница | [S] Алтарь | [?] Сундук"
            )
            print(
                "\n1 - Управление базой\n"
                "2 - Управление юнитом\n"
                "3 - Копирование/восстановление поля\n"
                "0 - Выход"
            )
            cmd = input("Выбор: ").strip()

            if cmd == "1":
                self._handle_base()
            elif cmd == "2":
                self._handle_unit()
            elif cmd == "3":
                self._handle_copy()
            elif cmd == "0":
                break
            else:
                print("Неверная команда.")

    def _handle_base(self) -> None:
        base = self.field.base
        if not base:
            return
        print("\n1 - Состояние базы и войска\n2 - Создание юнита")
        act = input("Выбор действия: ").strip()

        if act == "1":
            print("\n" + base.get_status())
            for i, u in enumerate(base.units, 1):
                print(f"  {i}. {u.get_info()}")
        elif act == "2":
            pos = self.field.find_spawn_point()
            if not base.can_spawn() or not pos:
                print("Невозможно создать юнита (лимит войска или нет места у замка).")
                return
            for k, (name, _) in base.UNIT_RECIPES.items():
                print(f"{k} - {name}")
            u_type = input("Выбор типа юнита: ").strip()
            unit = base.create_unit(u_type, pos[0], pos[1])
            if unit and self.field.add_unit(unit):
                print(f"Создан отряд: {unit.get_info()}")
                print("\n" + self.field.enemy_turn())
            else:
                print("Ошибка создания отряда.")

    def _handle_unit(self) -> None:
        base = self.field.base
        if not base or not base.units:
            print("Нет доступных юнитов!")
            return

        for i, u in enumerate(base.units, 1):
            print(f"{i} - {u.get_info()} (Дальность атаки: {u.attack_range})")
        try:
            idx = int(input("Выберите номер юнита: ").strip()) - 1
            unit = base.units[idx]
        except (ValueError, IndexError):
            print("Неверный номер.")
            return

        print(
            f"\nЮнит {unit.get_symbol()} ({unit.name}) готов к приказу!\n"
            "1 - Перемещение / Ближний бой (W/A/S/D)\n"
            "2 - Использование способности\n"
            "3 - Дальняя атака (для Магов и Стрелков)\n"
            "4 - Оставить юнита в покое"
        )
        act = input("Выбор действия: ").strip()

        if act == "1":
            d = input("Направление (W/A/S/D): ").strip().upper()
            moves = {"W": (0, -1), "S": (0, 1), "A": (-1, 0), "D": (1, 0)}
            if d in moves:
                print("\n" + self.field.move_unit(unit, *moves[d]))
                print("\n" + self.field.enemy_turn())  # Авто-ход врага
            else:
                print("Неверное направление.")

        elif act == "2":
            print("\n" + unit.use_ability())
            print("\n" + self.field.enemy_turn())  # Авто-ход врага

        elif act == "3":
            if unit.attack_range <= 1:
                print("Этот отряд сражается только в ближнем бою (шагните на врага через пункт 1)!")
                return
            # Показываем координаты всех живых врагов для удобства прицеливания
            enemies = self.field.enemy_base.units if self.field.enemy_base else []
            print("\nДоступные цели врага на карте:")
            for eu in enemies:
                dist = abs(unit.x - eu.x) + abs(unit.y - eu.y)
                print(f"  [{eu.get_symbol().lower()}] {eu.name} на ({eu.x}, {eu.y}) — HP: {eu.hp}, Дистанция: {dist}")
            if self.field.enemy_base and self.field.enemy_base.hp > 0:
                b_dist = abs(unit.x - self.field.enemy_base.x) + abs(unit.y - self.field.enemy_base.y)
                print(f"  [C] База врага на (9, 9) — HP: {self.field.enemy_base.hp}, Дистанция: {b_dist}")

            try:
                tx = int(input("Введите X цели: ").strip())
                ty = int(input("Введите Y цели: ").strip())
            except ValueError:
                print("Координаты должны быть числами!")
                return

            print("\n" + self.field.ranged_attack(unit, tx, ty))
            print("\n" + self.field.enemy_turn())

    def _handle_copy(self) -> None:
        print("\n1 - Скопировать текущее поле\n2 - Загрузить скопированное поле")
        c = input("Выбор: ").strip()
        if c == "1":
            self.saved_copy = self.field.copy_field()
            print("Копия поля успешно сохранена в памяти.")
        elif c == "2" and self.saved_copy:
            self.field = self.saved_copy.copy_field()
            print("Поле восстановлено из копии.")