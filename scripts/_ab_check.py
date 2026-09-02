# -*- coding: utf-8 -*-
"""临时对拍脚本：验证 LunarYear LRU 缓存补丁不改变任何历法输出。
用法：python ab_check.py {plain|patched} <json 日期列表>"""
import json
import sys

sys.path.insert(0, "src")
patched = sys.argv[1] == "patched"
dates = json.loads(sys.argv[2])
if patched:
    import dayan.core.lunar_cal  # noqa: F401  导入即挂缓存补丁
from lunar_python import Solar

out = []
for y, m, d, h in dates:
    l = Solar.fromYmdHms(y, m, d, h, 0, 0).getLunar()
    ec = l.getEightChar()
    out.append([ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime(),
                l.getYearInGanZhi(), l.getMonthInGanZhi()])
print(json.dumps(out))
