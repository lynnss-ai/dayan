# -*- coding: utf-8 -*-
"""八卦 / 六十四卦 / 京房八宫 / 纳甲纳支 / 错综互变 纯规则层。
为梅花易数、六爻纳甲、周易卦爻三个引擎共用。
爻位统一自下而上记为 0..5（初爻在下）。
"""
from typing import Dict, List, Optional, Tuple

from .wuxing import ZHI, ZHI_WX

# ---------- 三爻经卦 ----------
# 爻自下而上，1=阳爻 0=阴爻
TRIGRAM_LINES: Dict[str, List[int]] = {
    "乾": [1, 1, 1], "兑": [1, 1, 0], "离": [1, 0, 1], "震": [1, 0, 0],
    "巽": [0, 1, 1], "坎": [0, 1, 0], "艮": [0, 0, 1], "坤": [0, 0, 0]}
# 先天八卦数（梅花起卦用）
XIAN_TIAN_NUM: Dict[str, int] = {"乾": 1, "兑": 2, "离": 3, "震": 4,
                                 "巽": 5, "坎": 6, "艮": 7, "坤": 8}
NUM_XIAN_TIAN: Dict[int, str] = {v: k for k, v in XIAN_TIAN_NUM.items()}
# 后天洛书宫数（奇门/玄空/八宅用）
HOU_TIAN_GONG: Dict[str, int] = {"坎": 1, "坤": 2, "震": 3, "巽": 4,
                                 "中": 5, "乾": 6, "兑": 7, "艮": 8, "离": 9}
GONG_HOU_TIAN: Dict[int, str] = {v: k for k, v in HOU_TIAN_GONG.items()}
TRIGRAM_WX: Dict[str, str] = {"乾": "金", "兑": "金", "震": "木", "巽": "木",
                              "坎": "水", "离": "火", "艮": "土", "坤": "土"}
TRIGRAM_NATURE: Dict[str, str] = {"乾": "天", "兑": "泽", "离": "火", "震": "雷",
                                  "巽": "风", "坎": "水", "艮": "山", "坤": "地"}
# 后天方位
TRIGRAM_DIR: Dict[str, str] = {"坎": "北", "艮": "东北", "震": "东", "巽": "东南",
                               "离": "南", "坤": "西南", "兑": "西", "乾": "西北"}
TRIGRAMS = ["乾", "兑", "离", "震", "巽", "坎", "艮", "坤"]

# ---------- 六十四卦名：NAME64[上卦][下卦] ----------
NAME64: Dict[str, Dict[str, str]] = {
    "乾": {"乾": "乾", "兑": "履", "离": "同人", "震": "无妄", "巽": "姤", "坎": "讼", "艮": "遁", "坤": "否"},
    "兑": {"乾": "夬", "兑": "兑", "离": "革", "震": "随", "巽": "大过", "坎": "困", "艮": "咸", "坤": "萃"},
    "离": {"乾": "大有", "兑": "睽", "离": "离", "震": "噬嗑", "巽": "鼎", "坎": "未济", "艮": "旅", "坤": "晋"},
    "震": {"乾": "大壮", "兑": "归妹", "离": "丰", "震": "震", "巽": "恒", "坎": "解", "艮": "小过", "坤": "豫"},
    "巽": {"乾": "小畜", "兑": "中孚", "离": "家人", "震": "益", "巽": "巽", "坎": "涣", "艮": "渐", "坤": "观"},
    "坎": {"乾": "需", "兑": "节", "离": "既济", "震": "屯", "巽": "井", "坎": "坎", "艮": "蹇", "坤": "比"},
    "艮": {"乾": "大畜", "兑": "损", "离": "贲", "震": "颐", "巽": "蛊", "坎": "蒙", "艮": "艮", "坤": "剥"},
    "坤": {"乾": "泰", "兑": "临", "离": "明夷", "震": "复", "巽": "升", "坎": "师", "艮": "谦", "坤": "坤"},
}
# 卦名 → (上卦, 下卦)
_GUA_LOOKUP: Dict[str, Tuple[str, str]] = {}
for _u, row in NAME64.items():
    for _l, _name in row.items():
        _GUA_LOOKUP[_name] = (_u, _l)
# 爻型 → 卦名（模块加载时预计算，排卦热路径免重建）
_LINES_TO_TRIGRAM: Dict[Tuple[int, ...], str] = {tuple(v): k
                                                 for k, v in TRIGRAM_LINES.items()}


def lines_of(upper: str, lower: str) -> List[int]:
    """六爻自下而上：下卦三爻 + 上卦三爻。"""
    return TRIGRAM_LINES[lower] + TRIGRAM_LINES[upper]


def split_trigrams(lines: List[int]) -> Tuple[str, str]:
    """由六爻反推 (上卦, 下卦)。"""
    low, up = lines[:3], lines[3:]
    return _LINES_TO_TRIGRAM[tuple(up)], _LINES_TO_TRIGRAM[tuple(low)]


def gua_name(upper: str, lower: str) -> str:
    return NAME64[upper][lower]


def cuo_gua(lines: List[int]) -> str:
    """错卦：阴阳全变。"""
    flipped = [1 - x for x in lines]
    u, l = split_trigrams(flipped)
    return gua_name(u, l)


def zong_gua(lines: List[int]) -> str:
    """综卦：上下颠倒（旋转 180°）。"""
    rev = list(reversed(lines))
    u, l = split_trigrams(rev)
    return gua_name(u, l)


def hu_gua(lines: List[int]) -> Tuple[str, str]:
    """互卦：下互为 2,3,4 爻，上互为 3,4,5 爻（爻位 0 起）。"""
    lower = _LINES_TO_TRIGRAM[tuple(lines[1:4])]
    upper = _LINES_TO_TRIGRAM[tuple(lines[2:5])]
    return upper, lower


def bian_gua(lines: List[int], dong: List[int]) -> Tuple[str, List[int]]:
    """变卦：动爻（0 起）阴阳翻转，返回 (变卦名, 变后六爻)。"""
    new = list(lines)
    for d in dong:
        new[d] = 1 - new[d]
    u, l = split_trigrams(new)
    return gua_name(u, l), new


# ---------- 京房八宫：宫序、世爻位置、纳支 ----------
# 每宫：本宫(纯卦)、一世、二世、三世、四世、五世、游魂、归魂
EIGHT_PALACE: Dict[str, List[str]] = {
    "乾": ["乾", "姤", "遁", "否", "观", "剥", "晋", "大有"],
    "坎": ["坎", "节", "屯", "既济", "革", "丰", "明夷", "师"],
    "艮": ["艮", "贲", "大畜", "损", "睽", "履", "中孚", "渐"],
    "震": ["震", "豫", "解", "恒", "升", "井", "大过", "随"],
    "巽": ["巽", "小畜", "家人", "益", "无妄", "噬嗑", "颐", "蛊"],
    "离": ["离", "旅", "鼎", "未济", "蒙", "涣", "讼", "同人"],
    "坤": ["坤", "复", "临", "泰", "大壮", "夬", "需", "比"],
    "兑": ["兑", "困", "萃", "咸", "蹇", "谦", "小过", "归妹"],
}
# 世爻位置（爻位 0 起）：纯卦上爻5；一世0…五世4；游魂3；归魂2
SHI_POS = [5, 0, 1, 2, 3, 4, 3, 2]
GUA_TO_PALACE: Dict[str, Tuple[str, int]] = {}
for _palace, _gs in EIGHT_PALACE.items():
    for _i, _gname in enumerate(_gs):
        GUA_TO_PALACE[_gname] = (_palace, _i)
# 本宫纯卦的纳支（初爻→上爻），同宫各卦按爻位沿用本宫纳支
NAZHI: Dict[str, List[str]] = {
    "乾": ["子", "寅", "辰", "午", "申", "戌"],
    "坎": ["寅", "辰", "午", "申", "戌", "子"],
    "艮": ["辰", "午", "申", "戌", "子", "寅"],
    "震": ["子", "寅", "辰", "午", "申", "戌"],
    "坤": ["未", "巳", "卯", "丑", "亥", "酉"],
    "巽": ["丑", "亥", "酉", "未", "巳", "卯"],
    "离": ["卯", "丑", "亥", "酉", "未", "巳"],
    "兑": ["巳", "卯", "丑", "亥", "酉", "未"],
}
# 纳甲（本宫纯卦各爻配天干），阳卦配一干、阴卦配一干
NA_GAN: Dict[str, List[str]] = {
    "乾": ["甲", "甲", "甲", "壬", "壬", "壬"], "坎": ["戊"] * 6,
    "艮": ["丙"] * 6, "震": ["庚"] * 6,
    "坤": ["乙", "乙", "乙", "癸", "癸", "癸"], "巽": ["辛"] * 6,
    "离": ["己"] * 6, "兑": ["丁"] * 6}


def palace_of(gua: str) -> Tuple[str, int]:
    """卦名 → (所属宫, 宫内序号0..7)。"""
    return GUA_TO_PALACE[gua]


def shi_ying(gua: str) -> Tuple[int, int]:
    """返回 (世爻位, 应爻位)，爻位 0 起；应与世隔两位。"""
    _, idx = GUA_TO_PALACE[gua]
    shi = SHI_POS[idx]
    ying = (shi + 3) % 6
    return shi, ying


def nazhi_yao(gua: str) -> List[Dict[str, str]]:
    """给某卦六爻配纳干支、五行、六亲。"""
    from .wuxing import liuqin
    palace, _ = GUA_TO_PALACE[gua]
    palace_wx = TRIGRAM_WX[palace]
    zhi_list = NAZHI[palace]
    gan_list = NA_GAN[palace]
    out = []
    for pos in range(6):
        z = zhi_list[pos]
        out.append({
            "pos": pos, "gan": gan_list[pos], "zhi": z,
            "ganzhi": gan_list[pos] + z, "wuxing": ZHI_WX[z],
            "liuqin": liuqin(palace_wx, ZHI_WX[z])})
    return out
