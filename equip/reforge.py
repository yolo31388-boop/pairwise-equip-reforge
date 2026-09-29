"""装备重铸与词条洗练系统"""
import copy
import random
from dataclasses import dataclass, field

RARITY_WEIGHTS = {"common": 70, "rare": 20, "epic": 8, "legendary": 2}
PITY_THRESHOLD = 10      # 连续N次未出稀有后必出稀有
PITY_BOOST = 5           # 每次未出稀有转移给稀有档的权重
VALUE_MIN, VALUE_MAX = 10.0, 100.0
VALUE_MODE = 45.0        # 偏态分布峰值，极值概率低但存在
BASE_COST = 10
MAX_REFORGES = 50
MAX_LOCKED = 2

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

    def _roll_rarity(self, equip: Equipment) -> str:
        # 按稀有度加权，保底计数器逐步提升稀有概率直到必出
        pity = self.pity_counter.get(equip.eid, 0)
        weights = dict(RARITY_WEIGHTS)
        if pity >= PITY_THRESHOLD:
            weights["common"] = 0
        else:
            shift = min(weights["common"], pity * PITY_BOOST)
            weights["common"] -= shift
            weights["rare"] += shift
        rarities = list(weights)
        rarity = self.rng.choices(rarities, weights=[weights[r] for r in rarities])[0]
        if rarity == "common":
            self.pity_counter[equip.eid] = pity + 1
        else:
            self.pity_counter[equip.eid] = 0
        return rarity

    def roll_affix(self, equip: Equipment) -> Affix:
        rarity = self._roll_rarity(equip)
        name = self.rng.choice(self.affix_pool[rarity])
        # 偏态分布：多数落在中低档，极值概率低但存在
        value = self.rng.triangular(VALUE_MIN, VALUE_MAX, VALUE_MODE)
        return Affix(name, rarity, value)

    def get_material_cost(self, equip: Equipment) -> int:
        # 按装备等级、词条数量和已重铸次数递增
        level_factor = 1 + equip.level // 10
        affix_factor = max(1, len(equip.affixes))
        count_factor = 1 + equip.reforge_count
        return BASE_COST * level_factor * affix_factor * count_factor

    def reforge(self, equip: Equipment, locked_indices: list[int] = None) -> bool:
        locked_indices = locked_indices or []
        if len(locked_indices) > MAX_LOCKED:
            raise ValueError(f"最多锁定{MAX_LOCKED}个词条")
        if equip.reforge_count >= self.get_max_reforges(equip):
            return False
        # 保存历史记录，支持回退
        equip.history.append(copy.deepcopy(equip.affixes))
        new_affixes = []
        for i, affix in enumerate(equip.affixes):
            if i in locked_indices:
                new_affixes.append(affix)
            else:
                new_affixes.append(self.roll_affix(equip))
        equip.affixes = new_affixes
        equip.reforge_count += 1
        return True

    def rollback(self, equip: Equipment) -> bool:
        if not equip.history:
            return False
        equip.affixes = equip.history.pop()
        equip.reforge_count = max(0, equip.reforge_count - 1)
        return True

    def get_max_reforges(self, equip: Equipment) -> int:
        return MAX_REFORGES
