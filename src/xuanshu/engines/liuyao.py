# -*- coding: utf-8 -*-
"""六爻纳甲引擎：起卦（铜钱六次/三数）、装纳甲、定世应、安六亲六神、变卦。
吉凶应期的综合断法交模型；本引擎只保证装卦结构确定。
"""
from typing import Dict, List, Optional

from ..core import wuxing as W
from ..core import gua as G
from ..core.registry import register, InputSpec

LIUSHEN_START = {"甲": "青龙", "乙": "青龙", "丙": "朱雀", "丁": "朱雀", "戊": "勾陈",
                 "己": "腾蛇", "庚": "白虎", "辛": "白虎", "壬": "玄武", "癸": "玄武"}
LIUSHEN_ORDER = ["青龙", "朱雀", "勾陈", "腾蛇", "白虎", "玄武"]
# 铜钱三枚：6 老阴(动) 7 少阳 8 少阴 9 老阳(动)
YANG_VALUE = {7, 9}
DONG_VALUE = {6, 9}


def _from_numbers(n1: int, n2: int, n3: int):
    """三数起卦：上卦 n1、下卦 n2（先天数），动爻 n3。"""
    up = G.NUM_XIAN_TIAN[((n1 - 1) % 8) + 1]
    lo = G.NUM_XIAN_TIAN[((n2 - 1) % 8) + 1]
    lines = G.lines_of(up, lo)
    dong = [(n3 - 1) % 6]
    vals = [9 if (i in dong) else (7 if lines[i] else 8) for i in range(6)]
    return vals


@register("liuyao", "六爻纳甲", "A", "core",
          inputs=[InputSpec("lines", "intlist", False, help="六爻自下而上，6/7/8/9"),
                  InputSpec("n1", "int", False), InputSpec("n2", "int", False),
                  InputSpec("n3", "int", False),
                  InputSpec("day_gan", "str", False, "甲", "起卦日干，安六神")],
          desc="装卦：纳甲/世应/六亲/六神/变卦（断卦交模型）")
def cast_liuyao(lines: Optional[List[int]] = None, n1: Optional[int] = None,
                n2: Optional[int] = None, n3: Optional[int] = None,
                day_gan: str = "甲") -> Dict:
    if not lines:
        if n1 is None:
            raise ValueError("需提供六爻 lines，或三数 n1,n2,n3")
        lines = _from_numbers(n1, n2, n3 or 1)
    if len(lines) != 6:
        raise ValueError("六爻必须 6 个值")
    yang = [v in YANG_VALUE for v in lines]
    dong = [i for i, v in enumerate(lines) if v in DONG_VALUE]
    inv = {tuple(v): k for k, v in G.TRIGRAM_LINES.items()}
    up, lo = inv[tuple(yang[3:])], inv[tuple(yang[:3])]
    gname = G.gua_name(up, lo)
    palace, pidx = G.palace_of(gname)
    shi, ying = G.shi_ying(gname)
    nazhi = G.nazhi_yao(gname)
    start = LIUSHEN_ORDER.index(LIUSHEN_START[day_gan])
    for pos in range(6):
        nazhi[pos]["liuishen"] = LIUSHEN_ORDER[(start + pos) % 6]
        nazhi[pos]["is_shi"] = pos == shi
        nazhi[pos]["is_ying"] = pos == ying
        nazhi[pos]["dong"] = pos in dong
        nazhi[pos]["yao"] = "阳" if yang[pos] else "阴"
    bian_name = None
    if dong:
        bian_name, _ = G.bian_gua([1 if y else 0 for y in yang], dong)
    res = {"本卦": gname, "卦宫": f"{palace}宫{G.TRIGRAM_WX[palace]}",
           "世爻": shi + 1, "应爻": ying + 1, "动爻": [d + 1 for d in dong],
           "变卦": bian_name, "六爻_初到上": nazhi}
    L = [f"【六爻纳甲】本卦「{gname}」（{res['卦宫']}），世{shi+1}应{ying+1}" +
         (f"，动爻 {[d+1 for d in dong]}，变卦「{bian_name}」" if dong else "，静卦")]
    for pos in range(5, -1, -1):
        x = nazhi[pos]
        tags = []
        if x["is_shi"]: tags.append("世")
        if x["is_ying"]: tags.append("应")
        if x["dong"]: tags.append("动")
        L.append(f"第{pos+1}爻 {x['ganzhi']} {x['yao']} {x['liuishen']} "
                 f"{x['liuqin']}{('【'+'/'.join(tags)+'】') if tags else ''}")
    res["text"] = "\n".join(L)
    return res
