# -*- coding: utf-8 -*-
"""灵签 / 解梦【检索类】引擎（C 级）：内置为小样例库，演示关键词检索与签文结构；
生产环境请替换为完整签文语料或向量 RAG。规则引擎只做确定性匹配，不做"通灵"。
"""
from typing import Dict, List, Optional

from ..core.registry import register, InputSpec

# 样例签库（结构示例，非完整一百签）
SAMPLE_QIAN = [
    {"no": 1, "title": "上上签·龙腾变化", "level": "上上",
     "poem": "云开见日正分明，水路征途事已成；恰如弓开秋夜月，自然万里快人情。",
     "jie": "谋事渐入顺境，仍需自身努力，守正待时。"},
    {"no": 18, "title": "上签·金乌西坠", "level": "上",
     "poem": "金乌西坠兔东升，日夜循环至古今；僧道得之衣禄好，士农工贾各遂心。",
     "jie": "阴阳轮转，此消彼长，宜顺应节奏、各安其位。"},
    {"no": 45, "title": "中平签·温和守常", "level": "中平",
     "poem": "温柔自古胜刚强，积善之门大吉昌；若是有人占此卦，宛如止渴遇琼浆。",
     "jie": "以柔克刚、稳中求进，不宜冒进。"},
    {"no": 88, "title": "中下签·守静待时", "level": "中下",
     "poem": "木为一虎在当门，须是有威不害人；分明说事无防碍，却被迟疑有恐惊。",
     "jie": "眼前似险实安，忌疑神疑鬼，缓行可过。"}]
# 样例解梦关键词表（生产请换大语料）
DREAM_KW = {
    "水": "传统解梦中多与情绪、财源相关，清水为顺、浊水主烦",
    "掉牙": "多与变化、人际或健康焦虑有关，非实际凶兆",
    "飞": "象征求突破与自由感，上升为舒展、下坠多为压力",
    "考试": "常对应现实中的被评价感与准备状态",
    "蛇": "传统中亦正亦邪，多主变化与隐忧，需结合情境"}


def _score(q: str, text: str) -> int:
    return sum(1 for ch in q if ch and ch in text)


@register("oracle", "灵签解梦", "C", "sample",
          inputs=[InputSpec("mode", "str", False, "dream", "qian=求签/dream=解梦"),
                  InputSpec("query", "str", False, "", "解梦关键词或所问"),
                  InputSpec("no", "int", False, None, "指定签号(1-样例范围)")],
          desc="样例签库/关键词检索（生产替换为完整语料或向量RAG）")
def cast_oracle(mode: str = "dream", query: str = "",
                no: Optional[int] = None) -> Dict:
    if mode == "qian":
        item = next((x for x in SAMPLE_QIAN if x["no"] == no), None)
        if item is None:
            scored = sorted(SAMPLE_QIAN, key=lambda x: -_score(query, x["poem"] + x["jie"]))
            item = scored[0]
        res = {"签": item, "库规模": f"样例{len(SAMPLE_QIAN)}签（非完整签书）"}
        res["text"] = (f"【灵签·样例库】第{item['no']}签 {item['title']}\n"
                       f"签诗：{item['poem']}\n解曰：{item['jie']}\n"
                       "（内置仅为结构样例，生产请接入完整签文/RAG）")
        return res
    # 解梦：关键词重叠打分
    hits = [(kw, mean) for kw, mean in DREAM_KW.items() if kw in query]
    if not hits:
        best = sorted(DREAM_KW.items(), key=lambda kv: -_score(query, kv[0]))[:1]
        hits = best if best and query else []
    res = {"问": query, "命中": hits, "库规模": f"样例{len(DREAM_KW)}条"}
    lines = [f"【解梦·样例库】所问：{query or '（空）'}"]
    lines += [f"·{kw}：{mean}" for kw, mean in hits] or ["未命中样例词表，生产环境由 RAG 召回。"]
    res["text"] = "\n".join(lines)
    return res
