# -*- coding: utf-8 -*-
"""跨术数共享的阴阳五行 / 天干地支 / 六十甲子 / 刑冲合害 / 神煞 纯规则层。
不依赖任何历法库，全部为确定性表与函数，便于单元测试与审计。
八字、择日、六爻、紫微、八宅等引擎共用本模块。
"""
from typing import Dict, List, Optional, Tuple

# ---------- 天干地支 ----------
GAN: List[str] = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI: List[str] = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
# 生肖
SHENGXIAO: Dict[str, str] = dict(zip(ZHI, ["鼠", "牛", "虎", "兔", "龙", "蛇",
                                           "马", "羊", "猴", "鸡", "狗", "猪"]))
GAN_WX: Dict[str, str] = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
ZHI_WX: Dict[str, str] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
# 地支藏干（本气、中气、余气）
HIDE: Dict[str, List[str]] = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"], "卯": ["乙"],
    "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"], "午": ["丁", "己"],
    "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"], "酉": ["辛"],
    "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"]}

# ---------- 五行生克 ----------
WUXING: List[str] = ["木", "火", "土", "金", "水"]
SHENG: Dict[str, str] = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}
KE: Dict[str, str] = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}
# 旺相休囚死：以月令为我，见 wangxiang_state()

# ---------- 六十甲子纳音 ----------
_NAYIN_SEQ: List[str] = [
    "海中金", "炉中火", "大林木", "路旁土", "剑锋金", "山头火", "涧下水", "城头土",
    "白蜡金", "杨柳木", "泉中水", "屋上土", "霹雳火", "松柏木", "长流水", "沙中金",
    "山下火", "平地木", "壁上土", "金箔金", "覆灯火", "天河水", "大驿土", "钗钏金",
    "桑柘木", "大溪水", "沙中土", "天上火", "石榴木", "大海水"]
JIAZI: List[str] = [GAN[i % 10] + ZHI[i % 12] for i in range(60)]
_JIAZI_INDEX: Dict[str, int] = {jz: i for i, jz in enumerate(JIAZI)}
NAYIN: Dict[str, str] = {JIAZI[i]: _NAYIN_SEQ[i // 2] for i in range(60)}
# 纳音五行（取末字）
NAYIN_WX: Dict[str, str] = {k: v[-1] for k, v in NAYIN.items()}

# ---------- 十神 ----------
SHISHEN_TABLE: Dict[Tuple[str, bool], str] = {
    ("同我", True): "比肩", ("同我", False): "劫财",
    ("我生", True): "食神", ("我生", False): "伤官",
    ("我克", True): "偏财", ("我克", False): "正财",
    ("克我", True): "七杀", ("克我", False): "正官",
    ("生我", True): "偏印", ("生我", False): "正印"}
# 六亲（六爻用）：以宫五行为我
LIUQIN_TABLE: Dict[str, str] = {
    "同我": "兄弟", "我生": "子孙", "我克": "妻财",
    "克我": "官鬼", "生我": "父母"}


def is_yang_gan(gan: str) -> bool:
    return GAN.index(gan) % 2 == 0


def is_yang_zhi(zhi: str) -> bool:
    return ZHI.index(zhi) % 2 == 0


def relation(me_wx: str, ot_wx: str) -> str:
    """ot 相对 me 的关系：同我/我生/我克/克我/生我。"""
    if ot_wx == me_wx:
        return "同我"
    if SHENG[me_wx] == ot_wx:
        return "我生"
    if KE[me_wx] == ot_wx:
        return "我克"
    if KE[ot_wx] == me_wx:
        return "克我"
    if SHENG[ot_wx] == me_wx:
        return "生我"
    raise ValueError(f"无法判定五行关系: {me_wx} -> {ot_wx}")


def shishen(day_gan: str, other_gan: str) -> str:
    rel = relation(GAN_WX[day_gan], GAN_WX[other_gan])
    same_yy = is_yang_gan(day_gan) == is_yang_gan(other_gan)
    return SHISHEN_TABLE[(rel, same_yy)]


def liuqin(palace_wx: str, yao_wx: str) -> str:
    return LIUQIN_TABLE[relation(palace_wx, yao_wx)]


def wangxiang_state(day_wx: str, month_wx: str) -> str:
    """以月令 month_wx 为我，求 day_wx 的旺相休囚死。"""
    if day_wx == month_wx:
        return "旺"
    if SHENG[month_wx] == day_wx:
        return "相"
    if SHENG[day_wx] == month_wx:
        return "休"
    if KE[day_wx] == month_wx:
        return "囚"
    if KE[month_wx] == day_wx:
        return "死"
    raise ValueError("旺相休囚死判定失败")


# ---------- 五虎遁 / 五鼠遁 ----------
# 年干 → 正月（寅月）天干
_WUHUDUN = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚",
            "辛": "庚", "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}


def month_gan(year_gan: str, month_zhi: str) -> str:
    """五虎遁：由年干、月支求月干。"""
    start = GAN.index(_WUHUDUN[year_gan])           # 寅月天干
    offset = (ZHI.index(month_zhi) - ZHI.index("寅")) % 12
    return GAN[(start + offset) % 10]


# 日干 → 子时天干
_WUSHUDUN = {"甲": "甲", "己": "甲", "乙": "丙", "庚": "丙", "丙": "戊",
             "辛": "戊", "丁": "庚", "壬": "庚", "戊": "壬", "癸": "壬"}


def hour_gan(day_gan: str, hour_zhi: str) -> str:
    """五鼠遁：由日干、时支求时干。"""
    start = GAN.index(_WUSHUDUN[day_gan])
    offset = ZHI.index(hour_zhi)                    # 子时为 0
    return GAN[(start + offset) % 10]


def jiazi_index(gan: str, zhi: str) -> int:
    """六十甲子序号 0..59（预计算表直查）。"""
    try:
        return _JIAZI_INDEX[gan + zhi]
    except KeyError:
        raise ValueError(f"非法干支 {gan}{zhi}") from None


# ---------- 天干合化 / 地支刑冲合害 ----------
# 天干五合（化出五行）
GAN_HE: Dict[str, Tuple[str, str]] = {
    "甲": ("己", "土"), "己": ("甲", "土"), "乙": ("庚", "金"), "庚": ("乙", "金"),
    "丙": ("辛", "水"), "辛": ("丙", "水"), "丁": ("壬", "木"), "壬": ("丁", "木"),
    "戊": ("癸", "火"), "癸": ("戊", "火")}
# 地支六合（化出五行/化气）
ZHI_LIUHE: Dict[str, Tuple[str, str]] = {
    "子": ("丑", "土"), "丑": ("子", "土"), "寅": ("亥", "木"), "亥": ("寅", "木"),
    "卯": ("戌", "火"), "戌": ("卯", "火"), "辰": ("酉", "金"), "酉": ("辰", "金"),
    "巳": ("申", "水"), "申": ("巳", "水"), "午": ("未", "土"), "未": ("午", "土")}
# 三合局：任一支 → (另两支, 局五行)
_SANHE_GROUPS = [
    (["申", "子", "辰"], "水"), (["寅", "午", "戌"], "火"),
    (["巳", "酉", "丑"], "金"), (["亥", "卯", "未"], "木")]
SANHE: Dict[str, Tuple[List[str], str]] = {}
for grp, wx in _SANHE_GROUPS:
    for z in grp:
        SANHE[z] = ([x for x in grp if x != z], wx)
# 三会方
_SANHUI_GROUPS = [
    (["寅", "卯", "辰"], "木"), (["巳", "午", "未"], "火"),
    (["申", "酉", "戌"], "金"), (["亥", "子", "丑"], "水")]
SANHUI: Dict[str, Tuple[List[str], str]] = {}
for grp, wx in _SANHUI_GROUPS:
    for z in grp:
        SANHUI[z] = ([x for x in grp if x != z], wx)
# 六冲（对位，index 差 6）
CHONG: Dict[str, str] = {z: ZHI[(ZHI.index(z) + 6) % 12] for z in ZHI}
# 六害
LIUHAI: Dict[str, str] = {
    "子": "未", "未": "子", "丑": "午", "午": "丑", "寅": "巳", "巳": "寅",
    "卯": "辰", "辰": "卯", "申": "亥", "亥": "申", "酉": "戌", "戌": "酉"}
# 相破
XIANGPO: Dict[str, str] = {
    "子": "酉", "酉": "子", "午": "卯", "卯": "午", "巳": "申", "申": "巳",
    "寅": "亥", "亥": "寅", "辰": "丑", "丑": "辰", "戌": "未", "未": "戌"}
# 三刑：返回与该支构成刑的支
SANXING: Dict[str, List[str]] = {
    "寅": ["巳", "申"], "巳": ["申", "寅"], "申": ["寅", "巳"],   # 寅巳申 恃势之刑
    "丑": ["戌", "未"], "戌": ["未", "丑"], "未": ["丑", "戌"],   # 丑戌未 无恩之刑
    "子": ["卯"], "卯": ["子"],                                   # 子卯 无礼之刑
    "辰": ["辰"], "午": ["午"], "酉": ["酉"], "亥": ["亥"]}       # 自刑


def xunkong(gan: str, zhi: str) -> List[str]:
    """旬空：某干支所在旬空亡的两个地支。"""
    idx = jiazi_index(gan, zhi)
    head = (idx // 10) * 10                 # 旬首六十甲子序号
    head_zhi = head % 12
    return [ZHI[(head_zhi + 10) % 12], ZHI[(head_zhi + 11) % 12]]


# ---------- 常用神煞（以日干或年支/日支查，地支为出现位置） ----------
# 天乙贵人（日干 → 两个贵人地支）
TIANYI: Dict[str, List[str]] = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"], "辛": ["寅", "午"]}
# 文昌贵人（日干 → 文昌地支）
WENCHANG: Dict[str, str] = {
    "甲": "巳", "乙": "午", "丙": "申", "戊": "申", "丁": "酉", "己": "酉",
    "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯"}
# 桃花/咸池（按三合局年支或日支查）
TAOHUA: Dict[str, str] = {"申": "酉", "子": "酉", "辰": "酉",
                          "寅": "卯", "午": "卯", "戌": "卯",
                          "巳": "午", "酉": "午", "丑": "午",
                          "亥": "子", "卯": "子", "未": "子"}
# 驿马
YIMA: Dict[str, str] = {"申": "寅", "子": "寅", "辰": "寅",
                        "寅": "申", "午": "申", "戌": "申",
                        "巳": "亥", "酉": "亥", "丑": "亥",
                        "亥": "巳", "卯": "巳", "未": "巳"}
# 羊刃（阳干为主）
YANGREN: Dict[str, str] = {"甲": "卯", "丙": "午", "戊": "午",
                           "庚": "酉", "壬": "子"}

# ---------- 三合局衍生神煞：将星(帝旺)/华盖(墓库)/劫煞(绝位)/亡神(禄位) ----------
# 组序与 _SANHE_GROUPS 一致：申子辰水、寅午戌火、巳酉丑金、亥卯未木
_SANHE_META = [
    (["申", "子", "辰"], "子", "辰", "巳", "亥"),
    (["寅", "午", "戌"], "午", "戌", "亥", "巳"),
    (["巳", "酉", "丑"], "酉", "丑", "寅", "申"),
    (["亥", "卯", "未"], "卯", "未", "申", "寅")]
JIANGXING: Dict[str, str] = {}
HUAGAI: Dict[str, str] = {}
JIESHA: Dict[str, str] = {}
WANGSHEN: Dict[str, str] = {}
for _grp, _jx, _hg, _js, _ws in _SANHE_META:
    for _z in _grp:
        JIANGXING[_z] = _jx
        HUAGAI[_z] = _hg
        JIESHA[_z] = _js
        WANGSHEN[_z] = _ws
# 孤辰寡宿（以年支所在三会方查）
GUCHEN: Dict[str, str] = {
    "亥": "寅", "子": "寅", "丑": "寅", "寅": "巳", "卯": "巳", "辰": "巳",
    "巳": "申", "午": "申", "未": "申", "申": "亥", "酉": "亥", "戌": "亥"}
GUASU: Dict[str, str] = {
    "亥": "戌", "子": "戌", "丑": "戌", "寅": "丑", "卯": "丑", "辰": "丑",
    "巳": "辰", "午": "辰", "未": "辰", "申": "未", "酉": "未", "戌": "未"}


def zhi_relations(zhis: List[str]) -> Dict[str, list]:
    """对一组地支（如四柱地支）统计六冲/六合/三合/三会/三刑/六害/相破。"""
    out: Dict[str, list] = {"六冲": [], "六合": [], "三合": [], "三会": [],
                            "三刑": [], "六害": [], "相破": []}
    s = list(zhis)
    for i in range(len(s)):
        for j in range(i + 1, len(s)):
            a, b = s[i], s[j]
            if CHONG[a] == b:
                out["六冲"].append([a, b])
            if ZHI_LIUHE.get(a, (None,))[0] == b:
                out["六合"].append([a, b, ZHI_LIUHE[a][1]])
            if LIUHAI[a] == b:
                out["六害"].append([a, b])
            if XIANGPO[a] == b:
                out["相破"].append([a, b])
            # 三刑（两支相刑，寅巳申需三支全另判）
            if b in SANXING.get(a, []):
                out["三刑"].append([a, b])
        # 三合 / 三会：另外两支都出现才算成局
        need, wx = SANHE[a]
        if need[0] in s and need[1] in s:
            grp = sorted({a, need[0], need[1]}, key=ZHI.index)
            rec = grp + [wx]
            if rec not in out["三合"]:
                out["三合"].append(rec)
        need2, wx2 = SANHUI[a]
        if need2[0] in s and need2[1] in s:
            grp = sorted({a, need2[0], need2[1]}, key=ZHI.index)
            rec = grp + [wx2]
            if rec not in out["三会"]:
                out["三会"].append(rec)
    # 寅巳申 / 丑戌未 三支齐全才算完整三刑
    for grp in (["寅", "巳", "申"], ["丑", "戌", "未"]):
        if all(x in s for x in grp):
            out["三刑"].append(grp + ["三刑齐"])
    return out


def gan_relations(gans: List[str]) -> Dict[str, list]:
    """对一组天干统计五合。"""
    out = {"天干五合": []}
    for i in range(len(gans)):
        for j in range(i + 1, len(gans)):
            a, b = gans[i], gans[j]
            if GAN_HE.get(a, (None,))[0] == b:
                out["天干五合"].append([a, b, GAN_HE[a][1]])
    return out
