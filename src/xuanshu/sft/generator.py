# -*- coding: utf-8 -*-
"""多术数 SFT 数据工厂：为每个引擎随机造合法入参 → 规则引擎出标准答案，
组装 messages（ShareGPT/OpenAI 风格），并按比例生成「先调用通用排盘工具」的
工具调用样本。确定性答案全部来自引擎，模型只学表达与解读。
"""
import json
import os
import random
from typing import Callable, Dict, List, Optional, Tuple

from ..core import wuxing as W
from ..core import gua as G
from ..core.registry import REGISTRY, get_engine
from .prompts import system_prompt, DISCLAIMER

TRIGRAMS = G.TRIGRAMS
SIGNS = ["白羊", "金牛", "双子", "巨蟹", "狮子", "处女",
         "天秤", "天蝎", "射手", "摩羯", "水瓶", "双鱼"]
PLANETS = ["太阳", "月亮", "水星", "金星", "火星", "木星", "土星"]
MOUNTAINS = ["壬", "子", "癸", "丑", "艮", "寅", "甲", "卯", "乙", "辰", "巽", "巳",
             "丙", "午", "丁", "未", "坤", "申", "庚", "酉", "辛", "戌", "乾", "亥"]
OPPOSITE = {"子": "午", "午": "子", "壬": "丙", "丙": "壬", "癸": "丁", "丁": "癸",
            "艮": "坤", "坤": "艮", "丑": "未", "未": "丑", "寅": "申", "申": "寅",
            "卯": "酉", "酉": "卯", "甲": "庚", "庚": "甲", "乙": "辛", "辛": "乙",
            "巽": "乾", "乾": "巽", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}


def _rdate(rng: random.Random, lo=1970, hi=2005):
    import datetime as dt
    d = dt.date.fromordinal(rng.randint(dt.date(lo, 1, 1).toordinal(),
                                        dt.date(hi, 12, 31).toordinal()))
    return d.year, d.month, d.day


# ---------- 每引擎：随机合法入参 ----------
def _s_bazi(rng):
    y, m, d = _rdate(rng)
    return dict(year=y, month=m, day=d, hour=rng.randint(0, 23),
                gender=rng.choice(["male", "female"]))


def _s_almanac(rng):
    y, m, d = _rdate(rng, 2000, 2025)
    return dict(year=y, month=m, day=d)


def _s_name(rng):
    return dict(surname=[rng.randint(3, 18)], given=[rng.randint(3, 18), rng.randint(3, 18)])


def _s_meihua(rng):
    return dict(mode="number", n1=rng.randint(1, 99), n2=rng.randint(1, 99))


def _s_numerology(rng):
    y, m, d = _rdate(rng)
    return dict(year=y, month=m, day=d)


def _s_bazhai(rng):
    y, _, _ = _rdate(rng, 1960, 2005)
    return dict(year=y, gender=rng.choice(["male", "female"]))


def _s_zhouyi(rng):
    return dict(upper=rng.choice(TRIGRAMS), lower=rng.choice(TRIGRAMS),
                dong=sorted(rng.sample(range(1, 7), rng.randint(0, 2))))


def _s_xuankong(rng):
    y, _, _ = _rdate(rng, 1990, 2030)
    mt = rng.choice(MOUNTAINS)
    return dict(year=y, mountain=mt, facing=OPPOSITE[mt])


def _s_liuyao(rng):
    return dict(lines=[rng.choice([6, 7, 8, 9]) for _ in range(6)],
                day_gan=rng.choice(W.GAN))


def _s_ziwei(rng):
    y, m, d = _rdate(rng)
    return dict(year=y, month=m, day=d, hour=rng.randint(0, 23),
                gender=rng.choice(["male", "female"]))


def _s_qimen(rng):
    return dict(dun=rng.choice(["阳", "阴"]), ju=rng.randint(1, 9),
                hour_ganzhi=rng.choice(W.JIAZI))


def _s_liuren(rng):
    return dict(month_jiang=rng.choice(W.ZHI), hour_zhi=rng.choice(W.ZHI),
                day_gan=rng.choice(W.GAN), day_zhi=rng.choice(W.ZHI))


def _s_astrology(rng):
    chosen = rng.sample(PLANETS, rng.randint(3, 5))
    entr = [f"{p}:{rng.choice(SIGNS)}:{rng.randint(0, 29)}.{rng.randint(0,9)}" for p in chosen]
    return dict(planets=entr)


def _s_physio(rng):
    return dict(mode=rng.choice(["face", "palm", "fengshui"]),
                features=rng.sample(["命宫:明润", "财帛:饱满", "夫妻:纹", "迁移:赤红"], 2))


def _s_tarot(rng):
    return dict(spread=rng.choice(["single", "three", "choice"]), seed=rng.randint(1, 9999))


def _s_oracle(rng):
    return dict(mode="dream", query=rng.choice(["梦见水", "梦见掉牙", "梦见飞", "梦见蛇", "梦见考试"]))


SAMPLERS: Dict[str, Callable] = {
    "bazi": _s_bazi, "almanac": _s_almanac, "name": _s_name, "meihua": _s_meihua,
    "numerology": _s_numerology, "bazhai": _s_bazhai, "zhouyi": _s_zhouyi,
    "xuankong": _s_xuankong, "liuyao": _s_liuyao, "ziwei": _s_ziwei,
    "qimen": _s_qimen, "liuren": _s_liuren, "astrology": _s_astrology,
    "physiognomy": _s_physio, "tarot": _s_tarot, "oracle": _s_oracle}

# 自然问法（每种两条，{a} 为可读入参）
ASK: Dict[str, List[str]] = {
    "bazi": ["帮我排个八字：{a}", "排盘看看，{a}"],
    "almanac": ["查一下黄历：{a}", "这天宜忌如何？{a}"],
    "name": ["算下姓名五格：{a}", "五格剖象看看，{a}"],
    "meihua": ["用梅花易数起卦：{a}", "数字起卦解一下，{a}"],
    "numerology": ["算生命灵数：{a}", "我的生命路径数是多少？{a}"],
    "bazhai": ["算八宅命卦：{a}", "我是东四命还是西四命？{a}"],
    "zhouyi": ["排一下周易卦爻：{a}", "看看世应错综互变，{a}"],
    "xuankong": ["排玄空飞星盘：{a}", "帮我排运盘山向星，{a}"],
    "liuyao": ["装六爻卦：{a}", "纳甲世应六亲排一下，{a}"],
    "ziwei": ["排紫微斗数命盘：{a}", "安星看看主星，{a}"],
    "qimen": ["排奇门盘：{a}", "时家奇门起一局，{a}"],
    "liuren": ["起大六壬课：{a}", "月将加时排四课，{a}"],
    "astrology": ["分析星盘相位：{a}", "看看元素和相位，{a}"],
    "physiognomy": ["看一下：{a}", "按传统相法解读，{a}"],
    "tarot": ["抽一组塔罗：{a}", "用牌阵帮我抽牌，{a}"],
    "oracle": ["解个梦：{a}", "这梦什么寓意？{a}"]}


def human_args(key: str, kw: Dict) -> str:
    if key in ("bazi", "ziwei"):
        g = "男" if kw.get("gender") == "male" else "女"
        return f"{kw['year']}年{kw['month']}月{kw['day']}日{kw.get('hour',12)}时，{g}"
    if key in ("almanac", "numerology"):
        return f"{kw['year']}年{kw['month']}月{kw['day']}日"
    if key == "name":
        return f"康熙笔画 姓{kw['surname']} 名{kw['given']}"
    if key == "meihua":
        return f"数字 {kw['n1']}、{kw['n2']}"
    if key == "bazhai":
        return f"{kw['year']}年生，{'男' if kw['gender']=='male' else '女'}"
    if key == "zhouyi":
        return f"上{kw['upper']}下{kw['lower']}，动爻{kw['dong'] or '无'}"
    if key == "xuankong":
        return f"{kw['year']}年，坐{kw['mountain']}向{kw['facing']}"
    if key == "liuyao":
        return f"六爻{kw['lines']}，{kw['day_gan']}日"
    if key == "qimen":
        return f"{kw['dun']}遁{kw['ju']}局，{kw['hour_ganzhi']}时"
    if key == "liuren":
        return f"月将{kw['month_jiang']}，{kw['hour_zhi']}时，{kw['day_gan']}{kw['day_zhi']}日"
    if key == "astrology":
        return "行星 " + "，".join(kw["planets"])
    if key == "physiognomy":
        return f"{kw['mode']}，特征{kw['features']}"
    if key == "tarot":
        return f"{kw['spread']}牌阵"
    return json.dumps(kw, ensure_ascii=False)


def build_example(key: str, rng: random.Random, use_tool: bool) -> Dict:
    kw = SAMPLERS[key](rng)
    result = get_engine(key).cast(**kw)
    q = rng.choice(ASK[key]).format(a=human_args(key, kw))
    answer = result["text"] + "\n" + DISCLAIMER
    if use_tool:
        messages = [
            {"role": "system", "content": system_prompt(key)},
            {"role": "user", "content": q},
            {"role": "assistant", "content": None,
             "tool_calls": [{"id": "call_1", "type": "function",
                             "function": {"name": "xuanshu_cast",
                                          "arguments": json.dumps(
                                              {"engine": key, "params": kw},
                                              ensure_ascii=False)}}]},
            {"role": "tool", "name": "xuanshu_cast",
             "content": json.dumps({"engine": key, "result": result}, ensure_ascii=False)},
            {"role": "assistant", "content": answer}]
    else:
        messages = [{"role": "system", "content": system_prompt(key)},
                    {"role": "user", "content": q},
                    {"role": "assistant", "content": answer}]
    return {"engine": key, "kind": "tool_call" if use_tool else "direct", "messages": messages}


def generate(domains: Optional[List[str]] = None, per_domain: int = 40, seed: int = 42,
             val_ratio: float = 0.1, outdir: str = "data",
             tool_ratio: float = 0.4) -> Tuple[int, int, Dict[str, int]]:
    domains = domains or list(SAMPLERS.keys())
    rng = random.Random(seed)
    train, val, count = [], [], {}
    for key in domains:
        group = []
        for _ in range(per_domain):
            use_tool = rng.random() < tool_ratio
            ex = build_example(key, rng, use_tool)
            count[f"{key}:{ex['kind']}"] = count.get(f"{key}:{ex['kind']}", 0) + 1
            group.append(ex)
        rng.shuffle(group)
        n_v = max(1, int(len(group) * val_ratio)) if group else 0
        val.extend(group[:n_v])
        train.extend(group[n_v:])
    rng.shuffle(train)
    rng.shuffle(val)
    rows = train + val
    os.makedirs(outdir, exist_ok=True)
    for name, data in [("sft_train.jsonl", train), ("sft_val.jsonl", val)]:
        with open(os.path.join(outdir, name), "w", encoding="utf-8") as f:
            for r in data:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(train), len(val), count
