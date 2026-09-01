# -*- coding: utf-8 -*-
"""姓名学·五格剖象引擎：由康熙笔画计算天人地外总五格、81 数理吉凶、三才五行。
注意：本引擎只做数学与查表；简体→康熙笔画需外部字典（assets 内附样例）。
"""
from typing import Dict, List, Optional

from ..core.registry import register, InputSpec

# 81 数理吉凶（通行版本，流派略有差异）：吉/半吉/凶
_NUM81 = [
    "吉", "凶", "吉", "凶", "吉", "吉", "吉", "半吉", "凶", "凶",
    "吉", "凶", "吉", "凶", "吉", "吉", "吉", "半吉", "凶", "凶",
    "吉", "凶", "吉", "吉", "半吉", "半吉", "半吉", "凶", "吉", "半吉",
    "吉", "吉", "吉", "凶", "吉", "凶", "吉", "半吉", "吉", "半吉",
    "吉", "凶", "半吉", "凶", "吉", "凶", "吉", "吉", "半吉", "半吉",
    "半吉", "吉", "半吉", "凶", "半吉", "凶", "吉", "半吉", "凶", "凶",
    "半吉", "凶", "吉", "凶", "吉", "凶", "吉", "吉", "凶", "凶",
    "半吉", "凶", "半吉", "凶", "半吉", "凶", "半吉", "半吉", "凶", "凶", "吉"]
# 数理暗示（简表，用于解读）
NUM_HINT = {"吉": "吉祥顺遂之数", "半吉": "吉凶参半、需配合他格", "凶": "传统判为波折之数"}


# 个位 → 五行
def _num_wx(n: int) -> str:
    d = n % 10
    return {1: "木", 2: "木", 3: "火", 4: "火", 5: "土",
            6: "土", 7: "金", 8: "金", 9: "水", 0: "水"}[d]


def num81(n: int) -> str:
    while n > 81:
        n -= 80
    return _NUM81[n - 1]


@register("name", "姓名五格", "S", "complete",
          inputs=[InputSpec("surname", "intlist", True, help="姓氏康熙笔画，复姓传两个"),
                  InputSpec("given", "intlist", True, help="名字康熙笔画，单名传一个"),
                  InputSpec("name", "str", False, "")],
          desc="五格剖象：天人地外总格 + 81数理 + 三才五行（笔画需康熙字典）")
def cast_name(surname: List[int], given: List[int], name: str = "") -> Dict:
    sx, gx = list(surname), list(given)
    tian = sum(sx) + (1 if len(sx) == 1 else 0)          # 单姓天格=姓+1
    ren = sx[-1] + gx[0]                                  # 人格=姓末+名首
    di = sum(gx) + (1 if len(gx) == 1 else 0)            # 单名地格=名+1
    zong = sum(sx) + sum(gx)
    wai = zong - ren + 1
    grids = {"天格": tian, "人格": ren, "地格": di, "外格": wai, "总格": zong}
    detail = {k: {"数": v, "五行": _num_wx(v), "吉凶": num81(v),
                  "暗示": NUM_HINT[num81(v)]} for k, v in grids.items()}
    sancai = _num_wx(tian) + _num_wx(ren) + _num_wx(di)
    # 三才简判：相邻两格五行相生/比和为顺，相克为逆
    seq = [_num_wx(tian), _num_wx(ren), _num_wx(di)]
    from ..core.wuxing import SHENG, KE
    marks = []
    for a, b in zip(seq, seq[1:]):
        if a == b or SHENG[a] == b:
            marks.append(f"{a}→{b}相生/比和")
        elif KE[a] == b:
            marks.append(f"{a}→{b}相克")
        elif KE[b] == a:
            marks.append(f"{b}→{a}反克")
        else:
            marks.append(f"{a}、{b}无直接生克")
    res = {"姓名": name, "康熙笔画": {"姓": sx, "名": gx}, "五格": detail,
           "三才五行": sancai, "三才关系_简化": marks}
    L = [f"【五格剖象{('·'+name) if name else ''}】康熙笔画 姓{sx} 名{gx}"]
    for k, v in detail.items():
        L.append(f"{k} {v['数']}（{v['五行']}）：{v['吉凶']}，{v['暗示']}")
    L.append(f"三才：{sancai}（" + "；".join(marks) + "）")
    L.append("说明：81数理与三才为通行版本，简体字需先换算康熙笔画再代入。")
    res["text"] = "\n".join(L)
    return res
