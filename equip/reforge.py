"""装备重铸与词条洗练系统 - 含7个bug"""
import random
from dataclasses import dataclass, field

@dataclass
class Affix:
    name: str
    rarity: str  # common/rare/epic/legendary
    value: float
    locked: bool = False

@dataclass
class Equipment:
    eid: str
    level: int
    affixes: list[Affix] = field(default_factory=list)
    reforge_count: int = 0
    history: list = field(default_factory=list)

class ReforgeSystem:
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)
        self.pity_counter: dict[str, int] = {}
        self.affix_pool = {
            "common": ["atk", "def", "hp"],
            "rare": ["crit", "haste"],
            "epic": ["crit_dmg", "mastery"],
            "legendary": ["void_strike", "divine_shield"],
        }

    def roll_affix(self, equip: Equipment) -> Affix:
        # bug1: 完全随机无保底
        all_affixes = []
        for rarity, names in self.affix_pool.items():
            all_affixes.extend(names)
        name = self.rng.choice(all_affixes)
        # bug2: 稀有度无权重
        rarity = "common"
        for r, names in self.affix_pool.items():
            if name in names:
                rarity = r
                break
        # bug6: 均匀分布
        value = self.rng.uniform(10, 100)
        return Affix(name, rarity, value)

    def get_material_cost(self, equip: Equipment) -> int:
        # bug3: 固定消耗
        return 10

    def reforge(self, equip: Equipment, locked_indices: list[int] = None) -> bool:
        # bug4: 不支持锁定
        locked_indices = locked_indices or []
        new_affixes = []
        for i, affix in enumerate(equip.affixes):
            if i in locked_indices:
                new_affixes.append(affix)
            else:
                new_affixes.append(self.roll_affix(equip))
        # bug5: 不保存历史
        equip.affixes = new_affixes
        equip.reforge_count += 1
        return True

    def rollback(self, equip: Equipment) -> bool:
        # bug5续: 没有历史可回退
        if not equip.history:
            return False
        equip.affixes = equip.history.pop()
        return True

    def get_max_reforges(self, equip: Equipment) -> int:
        # bug7: 无次数限制
        return 999999
