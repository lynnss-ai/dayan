# -*- coding: utf-8 -*-
"""梅花易数引擎：时间/数字起卦，定本卦、互卦、变卦，分体用并论体用生克与卦气。"""
from typing import Dict, Optional

from ..core import wuxing as W
from ..core import gua as G
from ..core.lunar_cal import hour_zhi_index, lunar_from_ymd
from ..core.registry import register, InputSpec


def _mod8(n: int) -> int:
    r = n % 8
    return 8 if r == 0 else r


def _mod6(n: int) -> int:
    r = n % 6
    return 6 if r == 0 else r


def _build(upper: str, lower: str, dong_pos: int, month_wx: Optional[str]) -> Dict:
    lines = G.lines_of(upper, lower)
    ben = G.gua_name(upper, lower)
    hu_up, hu_lo = G.hu_gua(lines)
    bian_name, bian_lines = G.bian_gua(lines, [dong_pos])
    # 体用：动爻所在经卦为用，另一为体
    if dong_pos >= 3:
        yong, ti = upper, lower
    else:
        yong, ti = lower, upper
    ti_wx, yong_wx = G.TRIGRAM_WX[ti], G.TRIGRAM_WX[yong]
    rel = W.relation(ti_wx, yong_wx)
    rel_text = {"同我": "体用比和（吉，谋事顺遂）", "我生": "体生用（耗，付出多）",
                "我克": "体克用（小吉，可成而劳）", "克我": "用克体（凶，事多阻）",
                "生我": "用生体（吉，有助益）"}[rel]
    guaqi = W.wangxiang_state(ti_wx, month_wx) if month_wx else "需月令"
    res = {
        "本卦": f"{ben}（{G.TRIGRAM_NATURE[upper]}上{G.TRIGRAM_NATURE[lower]}下）",
        "上卦": upper, "下卦": lower, "动爻": dong_pos + 1,
        "互卦": G.gua_name(hu_up, hu_lo), "变卦": bian_name,
        "体卦": ti, "用卦": yong, "体五行": ti_wx, "用五行": yong_wx,
        "体用关系": rel, "体用断语": rel_text, "体卦卦气": guaqi}
    L = [f"【梅花易数】本卦「{ben}」（上{upper}下{lower}），第{dong_pos + 1}爻动",
         f"互卦「{res['互卦']}」，变卦「{bian_name}」",
         f"体卦{ti}（{ti_wx}），用卦{yong}（{yong_wx}）：{rel_text}",
         f"体卦于月令处「{guaqi}」地。卦象排布确定，断卦结合外应交模型。"]
    res["text"] = "\n".join(L)
    return res


@register("meihua", "梅花易数", "S", "complete",
          inputs=[InputSpec("mode", "str", False, "time", "time=时间起卦/number=数字起卦"),
                  InputSpec("year", "int", False), InputSpec("month", "int", False),
                  InputSpec("day", "int", False), InputSpec("hour", "int", False, 12),
                  InputSpec("n1", "int", False, help="数字起卦上卦数"),
                  InputSpec("n2", "int", False, help="数字起卦下卦数")],
          desc="时间/数字起卦，本互变、体用生克、卦气")
def cast_meihua(mode: str = "time", year: int = 2000, month: int = 1, day: int = 1,
                hour: int = 12, n1: Optional[int] = None,
                n2: Optional[int] = None) -> Dict:
    if mode == "number":
        if n1 is None or n2 is None:
            raise ValueError("数字起卦需提供 n1,n2")
        up = G.NUM_XIAN_TIAN[_mod8(n1)]
        lo = G.NUM_XIAN_TIAN[_mod8(n2)]
        dong = _mod6(n1 + n2) - 1
        return _build(up, lo, dong, None)
    l = lunar_from_ymd(year, month, day, hour)
    nian_zhi = l.getYearZhi()
    ynum = W.ZHI.index(nian_zhi) + 1            # 年支数 子1..亥12
    mnum = abs(int(l.getMonth()))
    dnum = int(l.getDay())
    tnum = hour_zhi_index(hour) + 1
    up = G.NUM_XIAN_TIAN[_mod8(ynum + mnum + dnum)]
    lo = G.NUM_XIAN_TIAN[_mod8(ynum + mnum + dnum + tnum)]
    dong = _mod6(ynum + mnum + dnum + tnum) - 1
    month_wx = W.ZHI_WX[l.getEightChar().getMonth()[1]]
    res = _build(up, lo, dong, month_wx)
    res["起卦数"] = {"年支数": ynum, "农历月": mnum, "农历日": dnum, "时支数": tnum}
    return res
