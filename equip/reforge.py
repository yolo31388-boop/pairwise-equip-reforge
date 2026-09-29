"""装备重铸与词条洗练系统"""
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
    # 稀有度权重: 稀有词条概率低
    RARITY_WEIGHTS = {"common": 70, "rare": 20, "epic": 8, "legendary": 2}
    # 保底: 连续N次不出稀有则必出, 期间概率逐步提升
    PITY_THRESHOLD = 20
    PITY_BOOST_PER_MISS = 5
    # 材料与次数
    BASE_COST = 10
    MAX_REFORGES = 50
    MAX_LOCKED = 2
    # 数值区间
    VALUE_MIN = 10.0
    VALUE_MAX = 100.0
    EXTREME_CHANCE = 0.05

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
        pity = self.pity_counter.get(equip.eid, 0)
        rarities = list(self.affix_pool.keys())
        weights = []
        for rarity in rarities:
            weight = self.RARITY_WEIGHTS[rarity]
            if rarity != "common":
                # 保底计数越高, 稀有词条权重越大
                weight += pity * self.PITY_BOOST_PER_MISS
            weights.append(weight)
        if pity >= self.PITY_THRESHOLD:
            # 达到保底次数, 必出稀有及以上
            weights[0] = 0
        rarity = self.rng.choices(rarities, weights=weights, k=1)[0]
        name = self.rng.choice(self.affix_pool[rarity])
        value = self._roll_value()
        return Affix(name, rarity, value)

    def _roll_value(self) -> float:
        # 偏态分布: 大部分中等偏下, 极值概率低但存在
        roll = self.rng.random()
        if roll < self.EXTREME_CHANCE:
            return self.rng.uniform(self.VALUE_MAX - 10, self.VALUE_MAX)
        if roll < self.EXTREME_CHANCE * 2:
            return self.rng.uniform(self.VALUE_MIN, self.VALUE_MIN + 10)
        return self.VALUE_MIN + self.rng.betavariate(2, 5) * (self.VALUE_MAX - self.VALUE_MIN)

    def get_material_cost(self, equip: Equipment) -> int:
        # 按装备等级、词条数量递增, 且随重铸次数越来越贵
        level_factor = 1 + equip.level // 10
        affix_factor = max(1, len(equip.affixes))
        escalation = 1 + equip.reforge_count // 5
        return self.BASE_COST * level_factor * affix_factor * escalation

    def reforge(self, equip: Equipment, locked_indices: list[int] = None) -> bool:
        locked_indices = locked_indices or []
        if len(locked_indices) > self.MAX_LOCKED:
            raise ValueError("最多锁定2个词条")
        if equip.reforge_count >= self.get_max_reforges(equip):
            return False
        # 保存历史快照, 支持回退
        equip.history.append([
            Affix(a.name, a.rarity, a.value, a.locked) for a in equip.affixes
        ])
        locked = set(locked_indices)
        new_affixes = []
        for i, affix in enumerate(equip.affixes):
            if i in locked:
                new_affixes.append(affix)
            else:
                new_affixes.append(self.roll_affix(equip))
        equip.affixes = new_affixes
        equip.reforge_count += 1
        # 更新保底计数: 出稀有则清零, 否则累加
        if any(a.rarity != "common" for a in new_affixes):
            self.pity_counter[equip.eid] = 0
        else:
            self.pity_counter[equip.eid] = self.pity_counter.get(equip.eid, 0) + 1
        return True

    def rollback(self, equip: Equipment) -> bool:
        if not equip.history:
            return False
        equip.affixes = equip.history.pop()
        equip.reforge_count = max(0, equip.reforge_count - 1)
        return True

    def get_max_reforges(self, equip: Equipment) -> int:
        return self.MAX_REFORGES
