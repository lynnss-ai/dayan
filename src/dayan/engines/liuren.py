# -*- coding: utf-8 -*-
"""大六壬引擎（确定性前段）：月将加时排天地盘、日干寄宫、立四课。
三传九宗门（贼克/比用/涉害/遥克/昴星/别责/八专/伏吟/返吟）规则分支繁多，
本版保留接口与四课输入，三传交后续版本/模型，成熟度 partial。
"""
from typing import Dict

from ..core import wuxing as W
from ..core.registry import register, InputSpec

# 日干寄宫（地支）
GAN_JI = {"甲": "寅", "乙": "辰", "丙": "巳", "戊": "巳", "丁": "未",
          "己": "未", "庚": "申", "辛": "戌", "壬": "亥", "癸": "丑"}


def tianpan(month_jiang: str, hour_zhi: str) -> Dict[str, str]:
    """月将加时：地盘每支上的天盘支。"""
    j, t = W.ZHI.index(month_jiang), W.ZHI.index(hour_zhi)
    return {g: W.ZHI[(j + (W.ZHI.index(g) - t)) % 12] for g in W.ZHI}


@register("liuren", "大六壬", "A", "partial",
          inputs=[InputSpec("month_jiang", "str", True, help="月将地支"),
                  InputSpec("hour_zhi", "str", True, help="占时地支"),
                  InputSpec("day_gan", "str", True, help="日干"),
                  InputSpec("day_zhi", "str", True, help="日支")],
          desc="月将加时天地盘 + 四课（三传九宗门留接口）")
def cast_liuren(month_jiang: str, hour_zhi: str, day_gan: str, day_zhi: str) -> Dict:
    tp = tianpan(month_jiang, hour_zhi)
    ganji = GAN_JI[day_gan]
    ke1_up = tp[ganji]
    ke2_up = tp[ke1_up]
    ke3_up = tp[day_zhi]
    ke4_up = tp[ke3_up]
    lessons = [
        {"课": "第一课(干上)", "下": ganji, "上": ke1_up},
        {"课": "第二课(干阴)", "下": ke1_up, "上": ke2_up},
        {"课": "第三课(支上)", "下": day_zhi, "上": ke3_up},
        {"课": "第四课(支阴)", "下": ke3_up, "上": ke4_up}]
    res = {"月将": month_jiang, "占时": hour_zhi, "天地盘": tp,
           "四课": lessons, "三传": "待九宗门规则补全（本版留接口）"}
    L = [f"【大六壬】月将{month_jiang}加占时{hour_zhi}",
         "天盘（地盘支→天盘上神）：" +
         "，".join(f"{g}上{tp[g]}" for g in W.ZHI),
         f"日干{day_gan}寄{ganji}："]
    for k in lessons:
        L.append(f"  {k['课']}：{k['下']}上{k['上']}")
    L.append("三传（初/中/末）需按九宗门择取，本版输出四课，断法交模型。")
    res["text"] = "\n".join(L)
    return res
