# -*- coding: utf-8 -*-
"""导入各术数引擎模块即完成注册。新增引擎：在此追加一行 import。"""
from . import (bazi, almanac, name_fivegrid, meihua, numerology, bazhai, zhouyi,
               xuankong, liuyao, ziwei, qimen, liuren, astrology,
               physiognomy, tarot, oracle)  # noqa: F401

ENGINE_ORDER = ["bazi", "almanac", "name", "meihua", "numerology", "bazhai",
                "zhouyi", "xuankong", "liuyao", "ziwei", "qimen", "liuren",
                "astrology", "physiognomy", "tarot", "oracle"]
