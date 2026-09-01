# -*- coding: utf-8 -*-
"""玄空飞星风水引擎：三元九运、运盘、山星盘、向星盘（洛书轨迹飞布）。
二十四山阴阳采用沈氏玄空通行分法；山/向也可直接传 shun=true/false 覆盖。
"""
from typing import Dict, Optional

from ..core.registry import register, InputSpec

# 洛书九宫后天顺序（坎1坤2震3巽4中5乾6兑7艮8离9）
GONG_NAME = {1: "坎", 2: "坤", 3: "震", 4: "巽", 5: "中", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
# 顺飞 / 逆飞时，从中宫起依次落宫
SHUN_PATH = [5, 6, 7, 8, 9, 1, 2, 3, 4]
NI_PATH = [5, 4, 3, 2, 1, 9, 8, 7, 6]
# 二十四山 → 洛书宫
MOUNTAIN_GONG = {}
for _ms, _g in [(["壬", "子", "癸"], 1), (["丑", "艮", "寅"], 8), (["甲", "卯", "乙"], 3),
                (["辰", "巽", "巳"], 4), (["丙", "午", "丁"], 9), (["未", "坤", "申"], 2),
                (["庚", "酉", "辛"], 7), (["戌", "乾", "亥"], 6)]:
    for _m in _ms:
        MOUNTAIN_GONG[_m] = _g
# 沈氏玄空：阳山顺飞、阴山逆飞
YANG_MOUNTAINS = set("甲庚丙壬辰戌丑未寅申巳亥")
STAR_NAME = {1: "一白贪狼", 2: "二黑巨门", 3: "三碧禄存", 4: "四绿文曲",
             5: "五黄廉贞", 6: "六白武曲", 7: "七赤破军", 8: "八白左辅", 9: "九紫右弼"}


def yun_of_year(year: int) -> int:
    """1864 起一运，每运 20 年，三元九运循环。"""
    idx = (year - 1864) // 20
    return idx % 9 + 1


def fly(center_star: int, shun: bool) -> Dict[int, int]:
    """某星入中，按顺/逆飞布九宫，返回 {宫: 星}。"""
    path = SHUN_PATH if shun else NI_PATH
    stars = [(center_star - 1 + (i if shun else -i)) % 9 + 1 for i in range(9)]
    return {gong: star for gong, star in zip(path, stars)}


def grid_view(pan: Dict[int, int]) -> str:
    """按洛书 3×3（巽离坤/震中兑/艮坎乾）渲染。"""
    order = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    return "\n".join(" ".join(f"{pan[g]}" for g in row) for row in order)


@register("xuankong", "玄空飞星", "A", "complete",
          inputs=[InputSpec("year", "int", True, help="建房/迁入公历年(定运)"),
                  InputSpec("mountain", "str", True, help="坐山二十四山，如 子"),
                  InputSpec("facing", "str", True, help="向山二十四山，如 午"),
                  InputSpec("m_shun", "bool", False, None, "覆盖坐山顺飞true/逆飞false"),
                  InputSpec("f_shun", "bool", False, None, "覆盖向山顺逆")],
          desc="三元九运 + 运盘/山盘/向盘洛书飞布")
def cast_xuankong(year: int, mountain: str, facing: str,
                  m_shun: Optional[bool] = None, f_shun: Optional[bool] = None) -> Dict:
    yun = yun_of_year(year)
    yun_pan = fly(yun, True)
    mg, fg = MOUNTAIN_GONG[mountain], MOUNTAIN_GONG[facing]
    m_center = yun_pan[mg]                    # 运盘坐山宫之星入中为山星
    f_center = yun_pan[fg]
    m_shun = mountain in YANG_MOUNTAINS if m_shun is None else m_shun
    f_shun = facing in YANG_MOUNTAINS if f_shun is None else f_shun
    m_pan = fly(m_center, m_shun)
    f_pan = fly(f_center, f_shun)
    res = {"三元九运": yun, "运星": STAR_NAME[yun],
           "坐山": mountain, "向山": facing,
           "运盘": yun_pan, "山星盘": m_pan, "向星盘": f_pan,
           "中宫山向": [m_pan[5], f_pan[5]]}
    L = [f"【玄空飞星】{year} 年属第{yun}运（{STAR_NAME[yun]}），坐{mountain}向{facing}",
         "运盘：\n" + grid_view(yun_pan),
         f"山星 {m_center} 入中，{'顺飞' if m_shun else '逆飞'}：\n" + grid_view(m_pan),
         f"向星 {f_center} 入中，{'顺飞' if f_shun else '逆飞'}：\n" + grid_view(f_pan),
         f"中宫山向组合：山星{m_pan[5]}、向星{f_pan[5]}（双星组合断法交模型）。"]
    res["text"] = "\n".join(L)
    return res
