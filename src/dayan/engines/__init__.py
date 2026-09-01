# -*- coding: utf-8 -*-
"""引擎自动发现：导入 engines 包即自动注册本目录全部引擎模块。
新增引擎只需放入新 .py 文件并用 @register 声明，无需再改本文件。"""
import importlib
import pkgutil

for _m in pkgutil.iter_modules(__path__):
    if not _m.name.startswith("_"):
        importlib.import_module(f".{_m.name}", __name__)
