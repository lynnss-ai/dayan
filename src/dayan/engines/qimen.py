# -*- coding: utf-8 -*-
"""时家奇门遁甲引擎（转盘法）：排地盘六仪三奇、天盘九星与天盘干、八门、八神，
并定 值符/值使。定局支持两种方式：
  1) 手动传入 dun/ju（由上层定局）；
  2) 传入公历 year/month/day（+hour），按通行**拆补法**自动定局：
     以日柱往前最近的甲/己日为符头，符头支 子午卯酉→上元、寅申巳亥→中元、
     辰戌丑未→下元，再查节气三元局数表（冬至一七四……大雪四七一）。
"""
from typing import Dict, Optional

from ..core import wuxing as W
from ..core.lunar_cal import hour_zhi_index, lunar_from_ymd
from ..core.registry import register, InputSpec

YI_SEQ = ["戊", "己", "庚", "辛", "壬", "癸", "丁", "丙", "乙"]
FIXED_STAR = {1: "天蓬", 8: "天任", 3: "天冲", 4: "天辅", 9: "天英",
              2: "天芮", 7: "天柱", 6: "天心", 5: "天禽"}
FIXED_DOOR = {1: "休门", 8: "生门", 3: "伤门", 4: "杜门", 9: "景门",
              2: "死门", 7: "惊门", 6: "开门", 5: "中宫"}
# 后天盘顺序（跳中五）
HOUTIAN = [1, 8, 3, 4, 9, 2, 7, 6]
GODS = ["值符", "腾蛇", "太阴", "六合", "白虎", "玄武", "九地", "九天"]
# 旬首地支 → 所遁六仪（甲子戊、甲戌己、甲申庚、甲午辛、甲辰壬、甲寅癸）
XUN_YI = {"子": "戊", "戌": "己", "申": "庚", "午": "辛", "辰": "壬", "寅": "癸"}

# ---------- 节气三元局数表（上元, 中元, 下元）· 通行拆补口径 ----------
YANG_TERMS = {"冬至", "小寒", "大寒", "立春", "雨水", "惊蛰",
              "春分", "清明", "谷雨", "立夏", "小满", "芒种"}
JU_TABLE: Dict[str, tuple] = {
    "冬至": (1, 7, 4), "小寒": (2, 8, 5), "大寒": (3, 9, 6),
    "立春": (8, 5, 2), "雨水": (9, 6, 3), "惊蛰": (1, 7, 4),
    "春分": (3, 9, 6), "清明": (4, 1, 7), "谷雨": (5, 2, 8),
    "立夏": (4, 1, 7), "小满": (5, 2, 8), "芒种": (6, 3, 9),
    "夏至": (9, 3, 6), "小暑": (8, 2, 5), "大暑": (7, 1, 4),
    "立秋": (2, 5, 8), "处暑": (1, 4, 7), "白露": (9, 3, 6),
    "秋分": (7, 1, 4), "寒露": (6, 9, 3), "霜降": (5, 8, 2),
    "立冬": (6, 9, 3), "小雪": (5, 8, 2), "大雪": (4, 7, 1)}
# 符头日支 → 三元（拆补法）
FU_YUAN = {}
for _z in ("子", "午", "卯", "酉"):
    FU_YUAN[_z] = 0
for _z in ("寅", "申", "巳", "亥"):
    FU_YUAN[_z] = 1
for _z in ("辰", "戌", "丑", "未"):
    FU_YUAN[_z] = 2


def resolve_ju(year: int, month: int, day: int) -> Dict:
    """拆补法定局：返回 {dun, ju, yuan, fu_tou, term}（供引擎与测试共用）。"""
    l = lunar_from_ymd(year, month, day, 12)
    term = l.getPrevJieQi(True).getName()
    day_idx = W.jiazi_index(l.getEightChar().getDay()[:1],
                            l.getEightChar().getDay()[1:])
    fu_idx = day_idx - (day_idx % 5)          # 甲/己日 idx%5==0，往前最近符头
    fu_gz = W.JIAZI[fu_idx]
    yuan = FU_YUAN[fu_gz[1]]
    dun = "阳" if term in YANG_TERMS else "阴"
    ju = JU_TABLE[term][yuan]
    return {"dun": dun, "ju": ju, "yuan": yuan, "fu_tou": fu_gz, "term": term}


def _ring_step(a: int, b: int, forward: bool) -> int:
    return ((b - a) if forward else (a - b)) % 9


def _anchor(g: int) -> int:
    """中五宫无位，值符/八神落中宫时寄坤二宫。"""
    return 2 if g == 5 else g


@register("qimen", "奇门遁甲", "A", "core",
          inputs=[InputSpec("dun", "str", False, help="阳/阴遁：阳 或 阴（与 ju 一起手动定局）"),
                  InputSpec("ju", "int", False, help="局数1-9（与 dun 一起手动定局）"),
                  InputSpec("hour_ganzhi", "str", False, help="时柱干支，如 甲子；传日期时可省略"),
                  InputSpec("year", "int", False, help="公历年（拆补法定局）"),
                  InputSpec("month", "int", False), InputSpec("day", "int", False),
                  InputSpec("hour", "int", False, 12, help="0-23 时，省 hour_ganzhi 时必填")],
          desc="转盘奇门：拆补自动定局或手动 dun/ju，地盘/天盘九星/八门/八神")
def cast_qimen(dun: Optional[str] = None, ju: Optional[int] = None,
               hour_ganzhi: Optional[str] = None,
               year: Optional[int] = None, month: Optional[int] = None,
               day: Optional[int] = None, hour: int = 12) -> Dict:
    dated = year is not None and month is not None and day is not None
    if dun and ju:                                   # 手动定局（原接口）
        if not 1 <= ju <= 9:
            raise ValueError("局数 1-9")
        ju_info = None
    elif dated:                                      # 拆补自动定局
        info = resolve_ju(year, month, day)
        dun, ju = info["dun"], info["ju"]
        ju_info = info
        if not hour_ganzhi:                          # 时柱：日干五鼠遁 + 时支
            l = lunar_from_ymd(year, month, day, hour)
            day_gan = l.getEightChar().getDay()[:1]
            hz = W.ZHI[hour_zhi_index(hour)]
            hour_ganzhi = W.hour_gan(day_gan, hz) + hz
    else:
        raise ValueError("需提供 dun+ju（手动定局）或 year+month+day（拆补自动定局）")
    if not hour_ganzhi:
        raise ValueError("手动定局需提供 hour_ganzhi")
    forward = dun == "阳"
    # 1) 地盘六仪三奇
    dipan: Dict[int, str] = {}
    for i, yi in enumerate(YI_SEQ):
        g = ((ju - 1 + i) if forward else (ju - 1 - i)) % 9 + 1
        dipan[g] = yi
    # 2) 旬首 → 值符仪 → 值符宫/值使门
    hg, hz = hour_ganzhi[0], hour_ganzhi[1]
    idx = W.jiazi_index(hg, hz)
    head_gz = W.JIAZI[(idx // 10) * 10]
    head_yi = XUN_YI[head_gz[1]]
    zhifu_gong = [g for g, y in dipan.items() if y == head_yi][0]
    # 3) 时干落宫（甲遁于旬首仪）
    seek = head_yi if hg == "甲" else hg
    target_gong = [g for g, y in dipan.items() if y == seek][0]
    shift = _ring_step(_anchor(zhifu_gong) - 1, _anchor(target_gong) - 1, forward)
    # 4) 天盘九星 + 天盘干（整体转盘）
    star_pan, gan_pan = {}, {}
    for g in range(1, 10):
        old = ((g - 1 - shift) if forward else (g - 1 + shift)) % 9 + 1
        star_pan[g] = FIXED_STAR[old]
        gan_pan[g] = dipan[old]
    # 5) 八门：值使门随时宫，旬首宫起子时顺/逆数到时支
    door_shift = ((W.ZHI.index(hz) - W.ZHI.index(head_gz[1]))
                  if forward else (W.ZHI.index(head_gz[1]) - W.ZHI.index(hz))) % 9
    door_pan = {}
    for g in range(1, 10):
        old = ((g - 1 - door_shift) if forward else (g - 1 + door_shift)) % 9 + 1
        door_pan[g] = FIXED_DOOR[old]
    # 6) 八神：值符神随值符星落宫，沿后天盘顺/逆布
    god_pan = {}
    start_i = HOUTIAN.index(_anchor(target_gong))
    for i, god in enumerate(GODS):
        g = HOUTIAN[(start_i + i) % 8 if forward else (start_i - i) % 8]
        god_pan[g] = god
    cells = {}
    for g in range(1, 10):
        cells[g] = {"宫": g, "地盘": dipan[g], "天盘干": gan_pan[g],
                    "九星": star_pan[g], "八门": door_pan[g],
                    "八神": god_pan.get(g, "")}
    res = {"遁": f"{dun}遁{ju}局", "时柱": hour_ganzhi, "旬首": head_gz,
           "值符": f"{FIXED_STAR[zhifu_gong]}({head_yi})落{target_gong}宫",
           "值使": f"{FIXED_DOOR[zhifu_gong]}", "九宫": cells}
    if ju_info:
        res["定局"] = {"方式": "拆补", "节气": ju_info["term"],
                       "三元": "上中下元"[ju_info["yuan"]],
                       "符头": ju_info["fu_tou"]}
    order = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    L = [f"【奇门遁甲】{dun}遁{ju}局，时柱{hour_ganzhi}（旬首{head_gz}）" +
         (f"，{ju_info['term']}{'上中下'[ju_info['yuan']]}元（符头{ju_info['fu_tou']}，拆补）"
          if ju_info else ""),
         f"值符 {res['值符']}；值使 {res['值使']}",
         "（每格：神 / 天盘干+地盘 / 星 / 门）"]
    for row in order:
        L.append("　|　".join(
            f"{g}宫 {god_pan.get(g,'')} {gan_pan[g]}{dipan[g]} "
            f"{star_pan[g]} {door_pan[g]}" for g in row))
    res["text"] = "\n".join(L)
    return res
