# -*- coding: utf-8 -*-
"""时家奇门遁甲引擎（转盘法·核心排布）：给定阴阳遁、局数与时柱，
排地盘六仪三奇、天盘九星与天盘干、八门、八神，并定 值符/值使。
节气定局（拆补/置闰/茅山）属上层，本引擎只接收已确定的 dun/ju，保证排布确定。
"""
from typing import Dict

from ..core import wuxing as W
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


def _ring_step(a: int, b: int, forward: bool) -> int:
    return ((b - a) if forward else (a - b)) % 9


def _anchor(g: int) -> int:
    """中五宫无位，值符/八神落中宫时寄坤二宫。"""
    return 2 if g == 5 else g


@register("qimen", "奇门遁甲", "A", "core",
          inputs=[InputSpec("dun", "str", True, help="阳/阴遁：阳 或 阴"),
                  InputSpec("ju", "int", True, help="局数1-9"),
                  InputSpec("hour_ganzhi", "str", True, help="时柱干支，如 甲子")],
          desc="转盘奇门：地盘/天盘九星/八门/八神（定局由上层传入）")
def cast_qimen(dun: str, ju: int, hour_ganzhi: str) -> Dict:
    if not 1 <= ju <= 9:
        raise ValueError("局数 1-9")
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
    order = [[4, 9, 2], [3, 5, 7], [8, 1, 6]]
    L = [f"【奇门遁甲】{dun}遁{ju}局，时柱{hour_ganzhi}（旬首{head_gz}）",
         f"值符 {res['值符']}；值使 {res['值使']}",
         "（每格：神 / 天盘干+地盘 / 星 / 门）"]
    for row in order:
        L.append("　|　".join(
            f"{g}宫 {god_pan.get(g,'')} {gan_pan[g]}{dipan[g]} "
            f"{star_pan[g]} {door_pan[g]}" for g in row))
    res["text"] = "\n".join(L)
    return res
