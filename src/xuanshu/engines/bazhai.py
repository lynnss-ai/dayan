# -*- coding: utf-8 -*-
"""八宅明镜引擎：由出生年算命卦（东四/西四命），按大游年歌推八方游星吉凶。"""
from typing import Dict

from ..core import gua as G
from ..core.registry import register, InputSpec

# 后天洛书顺旋次序
CYCLE = ["坎", "艮", "震", "巽", "离", "坤", "兑", "乾"]
# 大游年歌：各伏位卦起，沿 CYCLE 下一卦依次配星（伏位自身为伏位）
SONG = {
    "乾": ["六煞", "天医", "五鬼", "祸害", "绝命", "延年", "生气"],
    "坎": ["五鬼", "天医", "生气", "延年", "绝命", "祸害", "六煞"],
    "艮": ["六煞", "绝命", "祸害", "生气", "延年", "天医", "五鬼"],
    "震": ["延年", "生气", "祸害", "绝命", "五鬼", "天医", "六煞"],
    "巽": ["天医", "五鬼", "六煞", "祸害", "生气", "绝命", "延年"],
    "离": ["六煞", "五鬼", "绝命", "延年", "祸害", "生气", "天医"],
    "坤": ["天医", "延年", "绝命", "生气", "祸害", "五鬼", "六煞"],
    "兑": ["生气", "祸害", "延年", "绝命", "六煞", "五鬼", "天医"]}
JI = {"生气", "天医", "延年", "伏位"}
XIONG = {"绝命", "五鬼", "六煞", "祸害"}
NUM_GUA = {1: "坎", 2: "坤", 3: "震", 4: "巽", 6: "乾", 7: "兑", 8: "艮", 9: "离"}
DONG_SI = {"坎", "离", "震", "巽"}


def _digit_root(n: int) -> int:
    while n >= 10:
        n = sum(int(c) for c in str(n))
    return n or 9


def ming_gua(year: int, gender: str) -> str:
    y2 = year % 100
    s = _digit_root(y2)
    male = str(gender).lower() in ("male", "m", "男", "1")
    k = (10 - s) if year < 2000 else (9 - s)
    if not male:
        k = (5 + s) if year < 2000 else (6 + s)
    k = ((k - 1) % 9) + 1
    if k == 5:                      # 中宫无卦，男寄坤、女寄艮
        k = 2 if male else 8
    return NUM_GUA[k]


def you_nian(fu: str) -> Dict[str, Dict[str, str]]:
    """以 fu 为伏位，推其余七卦游星。"""
    start = (CYCLE.index(fu) + 1) % 8
    out = {fu: {"星": "伏位", "方位": G.TRIGRAM_DIR[fu], "吉凶": "吉"}}
    stars = SONG[fu]
    for i, star in enumerate(stars):
        t = CYCLE[(start + i) % 8]
        out[t] = {"星": star, "方位": G.TRIGRAM_DIR[t],
                  "吉凶": "吉" if star in JI else "凶"}
    return out


@register("bazhai", "八宅风水", "S", "complete",
          inputs=[InputSpec("year", "int", True, help="出生公历年"),
                  InputSpec("gender", "str", False, "male")],
          desc="命卦 + 东四/西四命 + 大游年八方吉凶位")
def cast_bazhai(year: int, gender: str = "male") -> Dict:
    mg = ming_gua(year, gender)
    yn = you_nian(mg)
    group = "东四命" if mg in DONG_SI else "西四命"
    jiwei = {t: v["星"] for t, v in yn.items() if v["吉凶"] == "吉"}
    xw = {t: v["星"] for t, v in yn.items() if v["吉凶"] == "凶"}
    res = {"命卦": mg, "命卦五行": G.TRIGRAM_WX[mg], "命组": group,
           "东四宅卦": sorted(DONG_SI), "西四宅卦": sorted(set(G.TRIGRAMS) - DONG_SI),
           "游年八方": yn, "四吉位": jiwei, "四凶位": xw}
    L = [f"【八宅命卦】{year} 年生 → 命卦「{mg}」（{G.TRIGRAM_WX[mg]}），属{group}",
         "四吉位：" + "、".join(f"{t}方-{s}" for t, s in jiwei.items()),
         "四凶位：" + "、".join(f"{t}方-{s}" for t, s in xw.items()),
         "配宅原则：东四命配东四宅（坎离震巽），西四命配西四宅（乾坤艮兑）。"]
    res["text"] = "\n".join(L)
    return res
