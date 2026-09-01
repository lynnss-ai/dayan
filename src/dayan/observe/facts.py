# -*- coding: utf-8 -*-
"""确定性事实抽取：返回"任何正确回答都必须包含"的关键串。
抽取结果保证是引擎 text 的子串（去除空白后），因此用 gold 文本自检应得 100%。
模型答案做同样的去空白处理后做子串命中，避免标点/空格差异导致误判。
"""
import re


def norm(s: str) -> str:
    return re.sub(r"\s+", "", str(s))


def _facts_bazi(kw, r):
    return [p["ganzhi"] for p in r["pillars"].values()]


def _facts_almanac(kw, r):
    return [r.get("日干支", ""), r.get("建除十二神", "")]


def _facts_name(kw, r):
    out = []
    for lab, d in r.get("五格", {}).items():
        if isinstance(d, dict) and "数" in d:
            out.append(f"{lab}{d['数']}")
    return out


def _short(x):
    """去掉括号补充说明，只留主名，如 '益（风上雷下）' -> '益'。"""
    for ch in ("（", "("):
        if ch in str(x):
            x = str(x).split(ch)[0]
    return str(x)


def _facts_meihua(kw, r):
    return [_short(x) for x in (r.get("本卦"), r.get("变卦"), r.get("体卦")) if x]


def _facts_numerology(kw, r):
    return [f"生命路径数{r.get('生命路径数')}"]


def _facts_bazhai(kw, r):
    return [x for x in (r.get("命卦"), r.get("命组")) if x]


def _facts_zhouyi(kw, r):
    out = [r.get("卦名", "") + "卦"]
    for k in ("错卦", "综卦", "变卦"):
        if r.get(k):
            out.append(r[k])
    return out


def _facts_xuankong(kw, r):
    out = [f"第{r.get('三元九运')}运"]
    if r.get("坐山"):
        out.append(r["坐山"])
    if r.get("向山"):
        out.append(r["向山"])
    return out


def _facts_liuyao(kw, r):
    return [x for x in (r.get("本卦"), r.get("变卦"), r.get("卦宫")) if x]


def _facts_ziwei(kw, r):
    out = [r.get("五行局", "")]
    if r.get("紫微在"):
        out.append(f"紫微在{r['紫微在']}")
    return out


def _facts_qimen(kw, r):
    return [x for x in (r.get("时柱"), r.get("值使")) if x]


def _facts_liuren(kw, r):
    return [f"月将{r.get('月将')}", f"占时{r.get('占时')}"]


def _facts_astrology(kw, r):
    out = []
    for p in kw.get("planets", []):
        parts = str(p).split(":")
        if len(parts) >= 2:
            out += [parts[0], parts[1]]
    return out


def _facts_physiognomy(kw, r):
    out = []
    for f in kw.get("features", []):
        out += [x for x in str(f).split(":") if x]
    return out


def _facts_tarot(kw, r):
    return [c.get("牌", "") for c in r.get("抽牌", []) if c.get("牌")]


def _facts_oracle(kw, r):
    hit = r.get("命中") or []
    return [hit[0][0]] if hit and hit[0] else []


FACT_FNS = {
    "bazi": _facts_bazi, "almanac": _facts_almanac, "name": _facts_name,
    "meihua": _facts_meihua, "numerology": _facts_numerology,
    "bazhai": _facts_bazhai, "zhouyi": _facts_zhouyi,
    "xuankong": _facts_xuankong, "liuyao": _facts_liuyao,
    "ziwei": _facts_ziwei, "qimen": _facts_qimen, "liuren": _facts_liuren,
    "astrology": _facts_astrology, "physiognomy": _facts_physiognomy,
    "tarot": _facts_tarot, "oracle": _facts_oracle}


def expected_facts(engine, kw, result):
    fn = FACT_FNS.get(engine)
    if not fn:
        return []
    return [norm(x) for x in fn(kw, result) if norm(x)]


def check_answer(engine, kw, result, answer):
    """返回 (命中数, 总数, 缺失事实列表)。"""
    facts = expected_facts(engine, kw, result)
    hay = norm(answer)
    missing = [f for f in facts if f not in hay]
    return len(facts) - len(missing), len(facts), missing
