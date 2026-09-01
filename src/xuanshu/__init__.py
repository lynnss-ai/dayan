# -*- coding: utf-8 -*-
"""玄枢 xuanshu —— 多术数确定性规则引擎 + 玄学领域 SFT 数据工厂。
import xuanshu 即自动注册全部引擎；用 xuanshu.cast(引擎名, 参数) 统一调用。
"""
__version__ = "0.4.0"

from .core import wuxing, gua, lunar_cal, registry  # noqa: F401
from .core.registry import REGISTRY, get_engine, all_engines, cast, register  # noqa: F401
from . import engines  # noqa: F401  导入即注册
