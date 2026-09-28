"""装备重铸与词条洗练系统 - 红态测试"""
import pytest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from equip.reforge import ReforgeSystem, Equipment, Affix

class TestPity:
    def test_pity_guarantees_rare_affix(self):
        rs = ReforgeSystem(seed=1)
        equip = Equipment("e1", 100, affixes=[Affix("atk", "common", 10)])
        # 连续重铸，保底应该确保出稀有
        got_rare = False
        for _ in range(50):
            rs.reforge(equip)
            if any(a.rarity in ("rare", "epic", "legendary") for a in equip.affixes):
                got_rare = True
                break
        assert got_rare == True  # bug1: 可能50次不出

class TestRarityWeight:
    def test_legendary_less_common_than_common(self):
        rs = ReforgeSystem(seed=42)
        equip = Equipment("e1", 100, affixes=[Affix("atk", "common", 10)])
        common_count = 0
        leg_count = 0
        for _ in range(200):
            rs.reforge(equip)
            for a in equip.affixes:
                if a.rarity == "common": common_count += 1
                if a.rarity == "legendary": leg_count += 1
        assert common_count > leg_count  # bug2: 权重一样可能leg更多

class TestMaterialCost:
    def test_cost_scales_with_level(self):
        rs = ReforgeSystem()
        e1 = Equipment("e1", 1)
        e100 = Equipment("e100", 100)
        assert rs.get_material_cost(e100) > rs.get_material_cost(e1)  # bug3: 都是10

class TestLockAffix:
    def test_locked_affix_not_changed(self):
        rs = ReforgeSystem(seed=42)
        equip = Equipment("e1", 100, affixes=[
            Affix("atk", "common", 50),
            Affix("crit", "rare", 20),
        ])
        original = equip.affixes[0].name
        rs.reforge(equip, locked_indices=[0])
        assert equip.affixes[0].name == original  # bug4: 被重铸了

class TestHistoryRollback:
    def test_reforge_history_saved(self):
        rs = ReforgeSystem(seed=42)
        equip = Equipment("e1", 100, affixes=[Affix("atk", "common", 10)])
        before = [a.name for a in equip.affixes]
        rs.reforge(equip)
        assert len(equip.history) > 0  # bug5: 没保存
        rs.rollback(equip)
        assert [a.name for a in equip.affixes] == before

class TestValueDistribution:
    def test_extreme_values_exist(self):
        rs = ReforgeSystem(seed=1)
        equip = Equipment("e1", 100, affixes=[Affix("atk", "common", 10)])
        values = []
        for _ in range(100):
            rs.reforge(equip)
            values.extend([a.value for a in equip.affixes])
        # 应该有接近最大值和最小值的
        assert max(values) > 90  # bug6: 均匀分布但可能没有极值
        assert min(values) < 20

class TestReforgeLimit:
    def test_reforge_has_daily_limit(self):
        rs = ReforgeSystem()
        equip = Equipment("e1", 100)
        assert rs.get_max_reforges(equip) < 100  # bug7: 999999
