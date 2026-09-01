# -*- coding: utf-8 -*-
"""择日择吉（黄历）引擎：建除十二神、值神黄黑道、二十八宿、宜忌、冲煞、
吉神凶煞、彭祖百忌、喜神方位、十二时辰干支。原始数据取自 lunar-python。
"""
from typing import Dict, Optional

from ..core import wuxing as W
from ..core.lunar_cal import lunar_from_ymd
from ..core.registry import register, InputSpec


def _shichen_ganzhi(day_gan: str):
    """五鼠遁排十二时辰干支。"""
    out = []
    for i, zhi in enumerate(W.ZHI):
        out.append({"时辰": f"{zhi}时", "ganzhi": W.hour_gan(day_gan, zhi) + zhi,
                    "clock": f"{(2 * i - 1) % 24:02d}:00-{(2 * i + 1) % 24:02d}:00"})
    return out


@register("almanac", "择日黄历", "S", "complete",
          inputs=[InputSpec("year", "int", True), InputSpec("month", "int", True),
                  InputSpec("day", "int", True), InputSpec("hour", "int", False, 12)],
          desc="某日黄历：建除/值神/星宿/宜忌/冲煞/时辰")
def cast_almanac(year: int, month: int, day: int, hour: int = 12) -> Dict:
    l = lunar_from_ymd(year, month, day, hour)
    day_gz = l.getDayGan() + l.getDayZhi()
    zhishen_type = l.getDayTianShenType()       # 黄道/黑道
    res = {
        "公历": f"{year}-{month:02d}-{day:02d}",
        "农历": l.toString(),
        "日干支": day_gz, "纳音": W.NAYIN.get(day_gz, ""),
        "生肖": l.getAnimal(),
        "建除十二神": l.getZhiXing(),
        "值神": f"{l.getDayTianShen()}（{zhishen_type}）",
        "黄黑": zhishen_type,
        "二十八宿": f"{l.getXiu()}{l.getZheng()}（{l.getAnimal()}）",
        "宜": l.getDayYi(), "忌": l.getDayJi(),
        "冲煞": f"冲{l.getChong()}（{l.getDayChongDesc()}）煞{l.getSha()}",
        "喜神方位": l.getDayPositionXiDesc(),
        "吉神宜趋": l.getDayJiShen(), "凶煞宜忌": l.getDayXiongSha(),
        "彭祖百忌": [l.getPengZuGan(), l.getPengZuZhi()],
        "十二时辰": _shichen_ganzhi(l.getDayGan()),
    }
    L = [f"【{res['公历']} 黄历】{res['农历']}",
         f"日干支 {day_gz}（{res['纳音']}），建除「{res['建除十二神']}」，"
         f"值神 {res['值神']}",
         f"二十八宿：{res['二十八宿']}；{res['冲煞']}；喜神 {res['喜神方位']}",
         "宜：" + "、".join(res["宜"]) if res["宜"] else "宜：无",
         "忌：" + "、".join(res["忌"]) if res["忌"] else "忌：无",
         f"吉神：{'、'.join(res['吉神宜趋'])}；凶煞：{'、'.join(res['凶煞宜忌'])}",
         "彭祖百忌：" + "；".join(res["彭祖百忌"])]
    res["text"] = "\n".join(L)
    return res
