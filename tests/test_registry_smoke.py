# -*- coding: utf-8 -*-
"""注册表驱动的自动冒烟：任何新引擎放入 engines/ 并 @register 后，
无需改测试即被本文件逐引擎覆盖；失败时报出具体引擎名。"""
import random
import zlib

import pytest

from dayan.core.registry import REGISTRY
from dayan.sft.generator import SAMPLERS


@pytest.mark.parametrize("key", sorted(REGISTRY))
def test_engine_cast_smoke(key):
    sampler = SAMPLERS.get(key)
    if sampler is None:  # 引擎已注册但尚未接入 SFT 采样器
        pytest.fail(f"引擎 {key} 缺少 SFT 采样器（sft/generator.py SAMPLERS）")
    kw = sampler(random.Random(zlib.crc32(key.encode("utf-8"))))
    out = REGISTRY[key].cast(**kw)
    assert isinstance(out, dict) and out.get("text"), f"引擎 {key} cast 输出异常"
