# -*- coding: utf-8 -*-
"""生命灵数引擎：由公历生日计算生命路径数、天赋数与对应特质（纯加法规则）。"""
from typing import Dict, List

from ..core.registry import register, InputSpec

NUM_TRAIT = {
    1: "独立、开创、领导力强，注意自我与合作的平衡",
    2: "敏感、善协调、重关系，注意优柔与依赖",
    3: "表达力强、有创意、善社交，注意分散",
    4: "务实、稳定、重秩序，注意僵化与安全感",
    5: "自由、变化、适应力强，注意浮躁与承诺",
    6: "负责、重家庭、有疗愈力，注意付出过度",
    7: "内省、求真、擅分析，注意疏离与多疑",
    8: "务实、事业心强、重成就，注意掌控与压力",
    9: "理想、博爱、富同理心，注意界限与放下"}
MASTER = {11: "灵性与直觉敏锐（大师数11，落到2）",
          22: "具构建大局的潜能（大师数22，落到4）",
          33: "具奉献与服务的高阶潜能（大师数33，落到6）"}


def _reduce(n: int, keep: List[int]):
    """连加至个位；过程中若命中大师数则记录。"""
    masters = []
    while n >= 10:
        if n in keep:
            masters.append(n)
        n = sum(int(c) for c in str(n))
    return n, masters


@register("numerology", "生命灵数", "S", "complete",
          inputs=[InputSpec("year", "int", True), InputSpec("month", "int", True),
                  InputSpec("day", "int", True)],
          desc="生命路径数/天赋数（纯数字加法）")
def cast_numerology(year: int, month: int, day: int) -> Dict:
    total = sum(int(c) for c in f"{year}{month:02d}{day:02d}")
    gifted = [int(c) for c in str(total)]
    life, masters = _reduce(total, [11, 22, 33])
    # 生日数
    bd, _ = _reduce(day, [])
    res = {"生命路径数": life, "天赋数": gifted, "大师数": masters,
           "生日数": bd, "路径特质": NUM_TRAIT[life]}
    L = [f"【生命灵数】{year}-{month:02d}-{day:02d}",
         f"各位相加得 {total}，天赋数 {gifted}，生命路径数 {life}",
         f"路径数{life}：{NUM_TRAIT[life]}"]
    if masters:
        L.append("含大师数 " + "、".join(MASTER[m] for m in masters))
    L.append(f"生日数 {bd}：{NUM_TRAIT.get(bd, '')}")
    res["text"] = "\n".join(L)
    return res
