# -*- coding: utf-8 -*-
"""西方占星【规则层】引擎：给定行星所在星座/度数，计算元素与模式分布、
相位（含容许度 orb）、宫主星与飞星。行星位置本身属天文计算，可选装
pyswisseph（瑞士星历表）由 compute_positions() 得到；无星历时由调用方传入。
"""
from typing import Dict, List, Optional

from ..core.registry import register, InputSpec

SIGNS = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
         "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
SIGN_ELEM = {s: ["火", "土", "风", "水"][i % 4] for i, s in enumerate(SIGNS)}
SIGN_MODE = {s: ["基本", "固定", "变动"][i % 3] for i, s in enumerate(SIGNS)}
# 现代守护星（传统守护见注释）
RULER = {"白羊": "火星", "金牛": "金星", "双子": "水星", "巨蟹": "月亮",
         "狮子": "太阳", "处女": "水星", "天秤": "金星", "天蝎": "冥王",
         "射手": "木星", "摩羯": "土星", "水瓶": "天王", "双鱼": "海王"}
# 相位 → (目标角, 默认容许度)
ASPECTS = {"合相": (0, 8), "六分": (60, 4), "刑相": (90, 6),
           "三分": (120, 6), "对分": (180, 8)}


def _parse_planets(entries: List[str]) -> Dict[str, Dict]:
    out = {}
    for e in entries:
        p, sign, deg = e.split(":")
        out[p] = {"sign": sign, "degree": float(deg),
                  "lon": SIGNS.index(sign) * 30 + float(deg)}
    return out


def find_aspects(planets: Dict[str, Dict]) -> List[Dict]:
    names = list(planets)
    out = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = planets[names[i]], planets[names[j]]
            d = abs(a["lon"] - b["lon"]) % 360
            d = min(d, 360 - d)
            for asp, (target, orb) in ASPECTS.items():
                if abs(d - target) <= orb:
                    out.append({"行星对": [names[i], names[j]], "相位": asp,
                                "实际角": round(d, 2), "容许差": round(abs(d - target), 2)})
    return out


def compute_positions_utc(year: int, month: int, day, lat: float, lon: float,
                          hour_utc: float = 12.0):
    """可选：用 pyswisseph 计算行星黄经。未安装时给出明确指引。"""
    try:
        import swisseph as swe  # noqa: F401
    except Exception:
        raise RuntimeError("未安装 pyswisseph，无法自行计算行星位置；"
                           "请 pip install pyswisseph 并放置星历，或直接传入 planets。")
    raise NotImplementedError("星历适配请按部署环境的 ephe 路径补全 swe.julday/calc")


@register("astrology", "西方占星", "A", "rules",
          inputs=[InputSpec("planets", "strlist", True,
                            help="行星:星座:度数，如 太阳:狮子:15.2，多个用逗号分隔"),
                  InputSpec("houses", "intlist", False, [],
                            help="12宫宫头星座序号0-11，逗号分隔，可选")],
          desc="相位/元素模式/宫主星飞星（行星位置需星历或上游传入）")
def cast_astrology(planets: List[str], houses: Optional[List[int]] = None) -> Dict:
    pl = _parse_planets(planets)
    elem = {"火": 0, "土": 0, "风": 0, "水": 0}
    mode = {"基本": 0, "固定": 0, "变动": 0}
    for p, v in pl.items():
        elem[SIGN_ELEM[v["sign"]]] += 1
        mode[SIGN_MODE[v["sign"]]] += 1
    aspects = find_aspects(pl)
    feixing = []
    if houses and len(houses) == 12:
        for h, si in enumerate(houses, start=1):
            sign = SIGNS[si]
            ruler = RULER[sign]
            loc = next((p for p, v in pl.items() if p == ruler), None)
            if loc:
                feixing.append({"宫": h, "宫头": sign, "宫主星": ruler,
                                "宫主所在": pl[loc]["sign"]})
    res = {"行星落座": {p: f"{v['sign']}{round(v['degree'],1)}°" for p, v in pl.items()},
           "元素分布": elem, "模式分布": mode, "相位": aspects, "飞星": feixing}
    L = ["【西方占星·规则层】",
         "落座：" + "，".join(f"{p} {v}" for p, v in res["行星落座"].items()),
         "元素：" + "、".join(f"{k}{v}" for k, v in elem.items()) +
         "；模式：" + "、".join(f"{k}{v}" for k, v in mode.items())]
    for a in aspects:
        L.append(f"相位：{a['行星对'][0]}–{a['行星对'][1]} {a['相位']}"
                 f"（{a['实际角']}°，差{a['容许差']}°）")
    if feixing:
        L.append("飞星：" + "；".join(f"{x['宫主星']}主{x['宫']}宫落{x['宫主所在']}" for x in feixing))
    L.append("行星位置由星历/上游提供，落座后的格局解读交模型。")
    res["text"] = "\n".join(L)
    return res
