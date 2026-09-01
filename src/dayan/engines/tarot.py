# -*- coding: utf-8 -*-
"""塔罗引擎（C 级，结构确定、解读交模型）：78 张牌库、正逆位、牌阵、种子可复现抽牌。"""
import random
from typing import Dict, List, Optional

from ..core.registry import register, InputSpec

MAJOR = ["愚者", "魔术师", "女祭司", "皇后", "皇帝", "教皇", "恋人", "战车",
         "力量", "隐者", "命运之轮", "正义", "倒吊人", "死神", "节制", "恶魔",
         "高塔", "星星", "月亮", "太阳", "审判", "世界"]
SUITS = {"权杖": "火·行动与创造", "圣杯": "水·情感与关系",
         "宝剑": "风·思维与冲突", "星币": "土·物质与现实"}
RANKS = ["首牌", "二", "三", "四", "五", "六", "七", "八", "九", "十",
         "侍从", "骑士", "王后", "国王"]
SPREADS = {"single": ["现状"],
           "three": ["过去", "现在", "未来"],
           "choice": ["现状", "选项A", "选项B"],
           "celtic": ["现状", "阻碍", "根基", "近过去", "理想", "近未来",
                      "自我", "外部环境", "希望与恐惧", "结果"]}


def _deck() -> List[Dict[str, str]]:
    cards = [{"name": n, "suit": "大阿尔克那", "theme": "人生主轴/关键课题"} for n in MAJOR]
    for suit, theme in SUITS.items():
        for rank in RANKS:
            cards.append({"name": f"{suit}{rank}", "suit": suit, "theme": theme})
    return cards


@register("tarot", "塔罗", "C", "complete",
          inputs=[InputSpec("spread", "str", False, "three",
                            "single/three/choice/celtic"),
                  InputSpec("seed", "int", False, 42),
                  InputSpec("reversed", "bool", False, True, "是否允许逆位")],
          desc="牌库+牌阵+正逆位抽牌（牌意组合解读交模型）")
def cast_tarot(spread: str = "three", seed: int = 42,
               reversed: bool = True) -> Dict:
    if spread not in SPREADS:
        raise ValueError(f"未知牌阵：{spread}")
    rng = random.Random(seed)
    deck = _deck()
    rng.shuffle(deck)
    positions = SPREADS[spread]
    draw = []
    for i, pos in enumerate(positions):
        card = deck[i]
        rev = reversed and rng.random() < 0.5
        draw.append({"位置": pos, "牌": card["name"], "花色/组": card["suit"],
                     "主题": card["theme"], "正逆": "逆位" if rev else "正位"})
    res = {"牌阵": spread, "抽牌": draw}
    L = [f"【塔罗·{spread}牌阵】（种子{seed}，结果可复现）"]
    for d in draw:
        L.append(f"{d['位置']}：{d['牌']}（{d['正逆']}，{d['主题']}）")
    L.append("牌意×位置×正逆的组合叙事由模型生成，引擎只保证抽牌与牌阵结构确定。")
    res["text"] = "\n".join(L)
    return res
