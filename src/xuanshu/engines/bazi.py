# -*- coding: utf-8 -*-
"""八字（四柱）引擎：四柱干支、藏干十神、纳音、五行力量、旺衰、大运，
并扩展干支刑冲合害、常用神煞、旬空与流年十神。历法层仍由 lunar-python 负责。
"""
from typing import Dict, List, Optional

from ..core import wuxing as W
from ..core.lunar_cal import Subject, to_lunar
from ..core.registry import register, InputSpec

PILLAR_ORDER = ["year", "month", "day", "time"]
PILLAR_LABEL = {"year": "年柱", "month": "月柱", "day": "日柱", "time": "时柱"}


def _build_pillar(prefix: str, ganzhi: str, day_gan: str) -> Dict:
    gan, zhi = ganzhi[0], ganzhi[1]
    hide = [{"gan": hg, "wuxing": W.GAN_WX[hg], "shishen": W.shishen(day_gan, hg)}
            for hg in W.HIDE[zhi]]
    return {"ganzhi": ganzhi, "gan": gan, "zhi": zhi,
            "gan_wuxing": W.GAN_WX[gan], "zhi_wuxing": W.ZHI_WX[zhi],
            "gan_shishen": "日主" if prefix == "day" else W.shishen(day_gan, gan),
            "hide": hide, "nayin": W.NAYIN[ganzhi]}


def _wuxing_strength(pillars: Dict[str, Dict]) -> Dict:
    stem = {w: 0.0 for w in W.WUXING}
    full = {w: 0.0 for w in W.WUXING}
    for name in PILLAR_ORDER:
        p = pillars[name]
        stem[p["gan_wuxing"]] += 1.0
        full[p["gan_wuxing"]] += 1.0
        for i, h in enumerate(p["hide"]):
            full[h["wuxing"]] += (1.0 if i == 0 else 0.5)
    return {"stem_only": {k: round(v, 2) for k, v in stem.items()},
            "with_hidden_weighted": {k: round(v, 2) for k, v in full.items()},
            "missing": [w for w, v in full.items() if v == 0]}


def _day_strength(day_gan: str, pillars: Dict[str, Dict]) -> Dict:
    dm = W.GAN_WX[day_gan]
    month_zhi = pillars["month"]["zhi"]
    month_wx = W.ZHI_WX[month_zhi]
    state = W.wangxiang_state(dm, month_wx)
    support = drain = 0.0
    for name, p in pillars.items():
        units = [(p["gan_wuxing"], 1.0)]
        for i, h in enumerate(p["hide"]):
            w = 1.0 if i == 0 else 0.5
            if name == "month" and i == 0:
                w *= 2.0
            units.append((h["wuxing"], w))
        for wx, w in units:
            if W.relation(dm, wx) in ("同我", "生我"):
                support += w
            else:
                drain += w
    total = support + drain
    ratio = round(support / total, 3) if total else 0.0
    adj = {"旺": 0.15, "相": 0.10, "休": 0.0, "囚": -0.10, "死": -0.15}[state]
    score = (ratio * 2 - 1) + adj
    label = "偏强" if score >= 0.12 else ("偏弱" if score <= -0.12 else "中和")
    favor = ["食伤", "财星", "官杀"] if label == "偏强" else \
            (["印星", "比劫"] if label == "偏弱" else [])
    return {"月令": month_zhi, "月令五行": month_wx, "月令旺衰状态": state,
            "帮扶分": round(support, 2), "克泄耗分": round(drain, 2),
            "帮扶占比": ratio, "旺衰修正分": round(score, 3),
            "初步强弱": label, "喜用倾向_入门规则": favor}


def _shensha(day_gan: str, year_zhi: str, day_zhi: str,
             pillars: Dict[str, Dict]) -> Dict:
    """以日干为主、兼顾年日两支，统计四柱地支上的常用神煞。"""
    hits: Dict[str, List[str]] = {}

    def add(name, pillar_key, zhi):
        hits.setdefault(name, []).append(f"{PILLAR_LABEL[pillar_key]}{zhi}")

    for key in PILLAR_ORDER:
        z = pillars[key]["zhi"]
        if z in W.TIANYI.get(day_gan, []):
            add("天乙贵人", key, z)
        if W.WENCHANG.get(day_gan) == z:
            add("文昌贵人", key, z)
        if W.YANGREN.get(day_gan) == z:
            add("羊刃", key, z)
        for anchor in (year_zhi, day_zhi):
            if W.TAOHUA.get(anchor) == z:
                add("桃花(咸池)", key, z)
            if W.YIMA.get(anchor) == z:
                add("驿马", key, z)
    return hits


def _liunian(day_gan: str, start_year: int, n: int = 10) -> List[Dict]:
    """流年：以 1984 甲子为基准推算干支，并标注相对日主的十神。"""
    out = []
    for y in range(start_year, start_year + n):
        idx = (y - 1984) % 60
        gz = W.JIAZI[idx]
        out.append({"year": y, "ganzhi": gz,
                    "gan_shishen": W.shishen(day_gan, gz[0]),
                    "zhi_shishen": _zhi_shishen(day_gan, gz[1])})
    return out


def _zhi_shishen(day_gan: str, zhi: str) -> str:
    """以地支本气藏干论十神。"""
    return W.shishen(day_gan, W.HIDE[zhi][0])


def render_bazi(c: Dict) -> str:
    p = c["pillars"]
    L = ["【四柱八字】",
         "　".join(f"{PILLAR_LABEL[k]} {p[k]['ganzhi']}" for k in PILLAR_ORDER), "",
         "【天干地支·藏干·十神·纳音】"]
    for k in PILLAR_ORDER:
        x = p[k]
        hide = "、".join(f"{h['gan']}({h['shishen']})" for h in x["hide"])
        tag = "＝日主" if k == "day" else f"天干十神：{x['gan_shishen']}"
        L.append(f"{PILLAR_LABEL[k]} {x['ganzhi']}：天干{x['gan']}({x['gan_wuxing']})，"
                 f"地支{x['zhi']}({x['zhi_wuxing']})，藏干[{hide}]，纳音{x['nayin']}；{tag}")
    rel = c["relations"]
    L += ["", "【干支作用】"]
    for name in ("天干五合", "六合", "三合", "三会", "六冲", "三刑", "六害", "相破"):
        v = rel.get(name)
        if v:
            L.append(f"{name}：{v}")
    if c["shensha"]:
        L.append("神煞：" + "；".join(f"{k}×{len(v)}" for k, v in c["shensha"].items()))
    L.append("旬空：" + "、".join(c["xunkong"]))
    L += ["", f"【日主】{c['day_master']}（{c['day_master_wuxing']}，{c['day_master_yinyang']}）"]
    wx = c["wuxing"]
    L.append("【五行力量】含藏干加权：" + "，".join(f"{k}{v}" for k, v in wx["with_hidden_weighted"].items()))
    L.append("　　　　　五行缺失：" + ("、".join(wx["missing"]) or "无明显缺失"))
    s = c["strength"]
    L.append(f"【旺衰(入门)】月令{s['月令']}处「{s['月令旺衰状态']}」地，"
             f"初步{s['初步强弱']}，喜用倾向：{'、'.join(s['喜用倾向_入门规则']) or '需综合判断'}")
    du = c["dayun"]
    L.append(f"【大运】{du['direction']}：" +
             " → ".join(f"{d['ganzhi']}({d['start_age']}-{d['end_age']}岁)" for d in du["list"]))
    return "\n".join(L)


@register("bazi", "八字四柱", "A", "complete",
          inputs=[InputSpec("year", "int", True, help="公历年"),
                  InputSpec("month", "int", True), InputSpec("day", "int", True),
                  InputSpec("hour", "int", False, 12), InputSpec("minute", "int", False, 0),
                  InputSpec("gender", "str", False, "male"),
                  InputSpec("longitude", "float", False, None),
                  InputSpec("n_dayun", "int", False, 8),
                  InputSpec("liunian_from", "int", False, None, "流年起始年，默认出生年")],
          desc="确定性四柱排盘 + 刑冲合害/神煞/大运/流年")
def cast_bazi(year: int, month: int, day: int, hour: int = 12, minute: int = 0,
              gender: str = "male", longitude: Optional[float] = None,
              n_dayun: int = 8, liunian_from: Optional[int] = None) -> Dict:
    subj = Subject(year, month, day, hour, minute, gender, longitude)
    lunar, ec, gcode = to_lunar(subj)
    gz = {"year": ec.getYear(), "month": ec.getMonth(),
          "day": ec.getDay(), "time": ec.getTime()}
    day_gan = ec.getDayGan()
    pillars = {k: _build_pillar(k, v, day_gan) for k, v in gz.items()}
    wx_count = _wuxing_strength(pillars)
    strength = _day_strength(day_gan, pillars)
    yun = ec.getYun(gcode)
    year_yang = W.is_yang_gan(gz["year"][0])
    forward = (year_yang and gcode == 1) or ((not year_yang) and gcode == 0)
    dayun_list = [{"ganzhi": d.getGanZhi(), "start_age": d.getStartAge(),
                   "end_age": d.getEndAge(), "start_year": d.getStartYear(),
                   "end_year": d.getEndYear()} for d in yun.getDaYun()[1:1 + n_dayun]]
    dayun = {"direction": "顺行" if forward else "逆行",
             "start_offset": {"year": yun.getStartYear(), "month": yun.getStartMonth(),
                              "day": yun.getStartDay()},
             "start_solar": yun.getStartSolar().toYmd(), "list": dayun_list}
    gans = [pillars[k]["gan"] for k in PILLAR_ORDER]
    zhis = [pillars[k]["zhi"] for k in PILLAR_ORDER]
    relations = {}
    relations.update(W.gan_relations(gans))
    relations.update(W.zhi_relations(zhis))
    relations = {k: v for k, v in relations.items() if v}
    chart = {
        "input": {"solar": f"{year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}",
                  "gender": gender, "longitude": longitude},
        "lunar": lunar.toString(), "pillars": pillars,
        "day_master": day_gan, "day_master_wuxing": W.GAN_WX[day_gan],
        "day_master_yinyang": "阳" if W.is_yang_gan(day_gan) else "阴",
        "wuxing": wx_count, "strength": strength,
        "relations": relations,
        "xunkong": W.xunkong(gz["day"][0], gz["day"][1]),
        "shensha": _shensha(day_gan, gz["year"][1], gz["day"][1], pillars),
        "liunian": _liunian(day_gan, liunian_from or year, 10),
        "dayun": dayun}
    chart["text"] = render_bazi(chart)
    return chart
