# -*- coding: utf-8 -*-
"""紫微斗数引擎（核心安星）：命身宫、五行局、定紫微与天府、安十四正曜、
生年四化、大限。采用通行安星口诀；闰月处理与个别流派差异处已在 README 标注，
生产 SFT 前建议与专业排盘软件抽样核对。
"""
from typing import Dict

from ..core import wuxing as W
from ..core.lunar_cal import hour_zhi_index, lunar_from_ymd
from ..core.registry import register, InputSpec

JU_OF_WX = {"水": 2, "木": 3, "金": 4, "土": 5, "火": 6}
# 紫微地支序号 → 天府地支序号（以寅申线镜像，寅申同宫）
ZIWEI_TIANFU = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 11, 6: 10,
                7: 9, 8: 8, 9: 7, 10: 6, 11: 5}
# 紫微系（逆行为负）与天府系（顺行为正）相对本宫的偏移
ZW_STARS = {"紫微": 0, "天机": -1, "太阳": -3, "武曲": -4, "天同": -5, "廉贞": -8}
TF_STARS = {"天府": 0, "太阴": 1, "贪狼": 2, "巨门": 3, "天相": 4,
            "天梁": 5, "七杀": 6, "破军": 10}
GONG12 = ["命宫", "兄弟", "夫妻", "子女", "财帛", "疾厄",
          "迁移", "交友", "官禄", "田宅", "福德", "父母"]
# 生年四化：年干 → (化禄, 化权, 化科, 化忌)
SIHUA = {
    "甲": ("廉贞", "破军", "武曲", "太阳"),
    "乙": ("天机", "天梁", "紫微", "太阴"),
    "丙": ("天同", "天机", "文昌", "廉贞"),
    "丁": ("太阴", "天同", "天机", "巨门"),
    "戊": ("贪狼", "太阴", "右弼", "天机"),
    "己": ("武曲", "贪狼", "天梁", "文曲"),
    "庚": ("太阳", "武曲", "太阴", "天同"),
    "辛": ("巨门", "太阳", "文曲", "文昌"),
    "壬": ("天梁", "紫微", "左辅", "武曲"),
    "癸": ("破军", "巨门", "太阴", "贪狼")}
SIHUA_NAME = ["化禄", "化权", "化科", "化忌"]
# 六吉星与禄存擎羊陀罗（通行口诀）
LU_CUN = {"甲": "寅", "乙": "卯", "丙": "巳", "戊": "巳", "丁": "午",
          "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}


def ziwei_pos(day: int, ju: int) -> int:
    """定紫微星（紫微斗数全书通行口诀），返回地支序号。"""
    yin = W.ZHI.index("寅")
    q, r = divmod(day, ju)
    if r == 0:                                   # 整除：商奇顺、商偶逆
        return (yin + (q - 1)) % 12 if q % 2 == 1 else (yin - (q - 1)) % 12
    k = q + 1
    back = ju - r
    if k % 2 == 1:                               # 商+1 奇：先顺 k 再逆退补数
        return (yin + (k - 1) - back) % 12
    return (yin - (k - 1) + back) % 12           # 偶：先逆 k 再顺进补数


@register("ziwei", "紫微斗数", "A", "core",
          inputs=[InputSpec("year", "int", True), InputSpec("month", "int", True),
                  InputSpec("day", "int", True), InputSpec("hour", "int", False, 12),
                  InputSpec("gender", "str", False, "male")],
          desc="核心安星：命身宫/五行局/十四主星/四化/大限")
def cast_ziwei(year: int, month: int, day: int, hour: int = 12,
               gender: str = "male") -> Dict:
    l = lunar_from_ymd(year, month, day, hour)
    year_gan = l.getYearGan()
    lm = abs(int(l.getMonth()))
    ld = int(l.getDay())
    ti = hour_zhi_index(hour)
    # 命宫：寅起正月顺至生月，再起子时逆至生时；身宫顺至生时
    month_palace = (W.ZHI.index("寅") + lm - 1) % 12
    ming = (month_palace - ti) % 12
    shen = (month_palace + ti) % 12
    ming_gan = W.month_gan(year_gan, W.ZHI[ming])
    ming_gz = ming_gan + W.ZHI[ming]
    ju_wx = W.NAYIN[ming_gz][-1]
    ju = JU_OF_WX[ju_wx]
    zw = ziwei_pos(ld, ju)
    tf = ZIWEI_TIANFU[zw]
    stars: Dict[int, list] = {i: [] for i in range(12)}
    for star, off in ZW_STARS.items():
        stars[(zw + off) % 12].append(star)
    for star, off in TF_STARS.items():
        stars[(tf + off) % 12].append(star)
    # 六吉星 + 禄存擎羊陀罗（辅星，单列不与主星混排）
    aux: Dict[int, list] = {i: [] for i in range(12)}
    aux[(W.ZHI.index("辰") + lm - 1) % 12].append("左辅")     # 辰起正月顺行
    aux[(W.ZHI.index("戌") - lm + 1) % 12].append("右弼")     # 戌起正月逆行
    aux[(W.ZHI.index("戌") - ti) % 12].append("文昌")         # 戌起子时逆数
    aux[(W.ZHI.index("辰") + ti) % 12].append("文曲")         # 辰起子时顺数
    lu = W.ZHI.index(LU_CUN[year_gan])
    aux[lu].append("禄存")
    aux[(lu + 1) % 12].append("擎羊")                         # 禄前一位
    aux[(lu - 1) % 12].append("陀罗")                         # 禄后一位
    # 十二人事宫：命宫起顺时针
    palaces = {}
    for k, pname in enumerate(GONG12):
        z = (ming + k) % 12
        palaces[pname] = {"地支": W.ZHI[z], "主星": stars[z], "辅星": aux[z]}
    # 四化
    sihua = {star: SIHUA_NAME[i] for i, star in enumerate(SIHUA[year_gan])}
    # 大限：五行局数起岁，阳男阴女顺，阴男阳女逆
    male = str(gender).lower() in ("male", "m", "男", "1")
    yang = W.is_yang_gan(year_gan)
    forward = (yang and male) or ((not yang) and not male)
    dayun = []
    for k in range(12):
        step = k if forward else -k
        z = (ming + step) % 12
        dayun.append({"宫": GONG12[k], "地支": W.ZHI[z], "主星": stars[z],
                      "辅星": aux[z], "起岁": ju + k * 10, "止岁": ju + k * 10 + 9})
    res = {"命宫": f"{ming_gz}（{W.ZHI[ming]}）", "身宫": W.ZHI[shen],
           "五行局": f"{ju_wx}{ju}局", "紫微在": W.ZHI[zw], "天府在": W.ZHI[tf],
           "生年四化": sihua, "十二宫": palaces, "大限": dayun}
    L = [f"【紫微斗数】{year}-{month:02d}-{day:02d} {hour:02d}时，"
         f"命宫{ming_gz}、身宫{W.ZHI[shen]}，{res['五行局']}",
         f"紫微在{W.ZHI[zw]}、天府在{W.ZHI[tf]}。十四主星落宫："]
    for pname in GONG12:
        p = palaces[pname]
        if p["主星"] or p["辅星"]:
            marks = [s + (f"({sihua[s]})" if s in sihua else "") for s in p["主星"]]
            aux_s = f"＋{'、'.join(p['辅星'])}" if p["辅星"] else ""
            L.append(f"  {pname}({p['地支']})：{'、'.join(marks) or '空宫'}{aux_s}")
        else:
            L.append(f"  {pname}({p['地支']})：空宫")
    L.append("大限" + ("顺行" if forward else "逆行") +
             "，" + " → ".join(f"{d['地支']}({d['起岁']}-{d['止岁']}岁)" for d in dayun[:6]))
    res["text"] = "\n".join(L)
    return res
