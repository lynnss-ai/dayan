# -*- coding: utf-8 -*-
"""周易卦爻引擎：给定上下卦（或先天数/卦名）与动爻，论卦宫、世应、错综互变。
卦辞爻辞文本属知识库，建议走 RAG，本引擎只做确定性卦爻结构。
"""
from typing import Dict, List, Optional

from ..core import gua as G
from ..core.registry import register, InputSpec


def _resolve(upper: Optional[str], lower: Optional[str],
             n1: Optional[int], n2: Optional[int], name: Optional[str]):
    if name:
        u, l = G._GUA_LOOKUP[name]
        return u, l
    if n1 is not None and n2 is not None:
        return G.NUM_XIAN_TIAN[((n1 - 1) % 8) + 1], G.NUM_XIAN_TIAN[((n2 - 1) % 8) + 1]
    if upper and lower:
        return upper, lower
    raise ValueError("需提供 卦名 name，或上下卦 upper/lower，或先天数 n1/n2")


@register("zhouyi", "周易卦爻", "S", "complete",
          inputs=[InputSpec("upper", "str", False, help="上卦：乾兑离震巽坎艮坤"),
                  InputSpec("lower", "str", False, help="下卦"),
                  InputSpec("n1", "int", False, help="上卦先天数1-8"),
                  InputSpec("n2", "int", False, help="下卦先天数1-8"),
                  InputSpec("name", "str", False, help="直接给卦名，如 泰"),
                  InputSpec("dong", "intlist", False, [], "动爻1-6，逗号分隔")],
          desc="卦宫/世应/错卦/综卦/互卦/变卦的确定性结构")
def cast_zhouyi(upper: Optional[str] = None, lower: Optional[str] = None,
                n1: Optional[int] = None, n2: Optional[int] = None,
                name: Optional[str] = None, dong: Optional[List[int]] = None) -> Dict:
    up, lo = _resolve(upper, lower, n1, n2, name)
    gname = G.gua_name(up, lo)
    lines = G.lines_of(up, lo)
    palace, idx = G.palace_of(gname)
    shi, ying = G.shi_ying(gname)
    hu_up, hu_lo = G.hu_gua(lines)
    dong = [d - 1 for d in (dong or []) if 1 <= d <= 6]
    bian_name = None
    if dong:
        bian_name, _ = G.bian_gua(lines, dong)
    res = {"卦名": gname, "上卦": up, "下卦": lo, "卦五行": G.TRIGRAM_WX[up],
           "卦宫": f"{palace}宫{G.TRIGRAM_WX[palace]}", "宫内序": idx,
           "世爻": shi + 1, "应爻": ying + 1,
           "错卦": G.cuo_gua(lines), "综卦": G.zong_gua(lines),
           "互卦": G.gua_name(hu_up, hu_lo), "变卦": bian_name,
           "六爻_自下而上": ["阳" if x else "阴" for x in lines]}
    L = [f"【周易】{gname}卦：上{up}下{lo}，属{res['卦宫']}",
         f"世爻在第{shi + 1}爻、应爻在第{ying + 1}爻",
         f"错卦「{res['错卦']}」、综卦「{res['综卦']}」、互卦「{res['互卦']}」" +
         (f"、变卦「{bian_name}」" if bian_name else "（无动爻则无变卦）"),
         "六爻自下而上：" + " ".join(res["六爻_自下而上"])]
    res["text"] = "\n".join(L)
    return res
