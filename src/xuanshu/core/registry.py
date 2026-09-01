# -*- coding: utf-8 -*-
"""引擎注册表：每个术数引擎用 @register 声明元信息与 cast 入口，CLI/SFT 统一调度。
maturity 成熟度说明（诚实标注，便于后续补齐）：
- complete ：纯规则可完整复算，已有单测
- core     ：核心排布可算，深层断法/流派细节交模型或留接口
- partial  ：仅完成确定性前段，后段（如三传九宗门）留接口
- rules    ：规则层完整，原始输入（如行星位置）需外部库/上游提供
- interface：规则表完整，特征提取依赖多模态模型，提供接口
- sample   ：检索类，内置样例库，生产需替换为真实语料/向量库
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

REGISTRY: Dict[str, "EngineSpec"] = {}


@dataclass
class InputSpec:
    name: str
    type: str = "str"               # int/float/str/bool/intlist/strlist
    required: bool = False
    default: Any = None
    help: str = ""


@dataclass
class EngineSpec:
    key: str
    name_cn: str
    tier: str                       # S/A/B/C 可规则化等级
    maturity: str
    cast: Callable[..., Dict[str, Any]]
    inputs: List[InputSpec] = field(default_factory=list)
    desc: str = ""

    def coerce(self, raw: Dict[str, str]) -> Dict[str, Any]:
        """把 CLI 传入的字符串参数按 inputs 声明转类型并补默认值。"""
        out: Dict[str, Any] = {}
        declared = {s.name: s for s in self.inputs}
        for name, spec in declared.items():
            if name in raw and raw[name] != "":
                out[name] = _convert(raw[name], spec.type)
            elif spec.required:
                raise ValueError(f"引擎 {self.key} 缺少必填参数 {name}")
            else:
                out[name] = spec.default
        # 允许引擎接收未在 spec 中声明的额外参数（原样透传字符串）
        for k, v in raw.items():
            if k not in out:
                out[k] = v
        return out


def _convert(v: str, t: str):
    if t == "int":
        return int(v)
    if t == "float":
        return float(v)
    if t == "bool":
        return str(v).lower() in ("1", "true", "yes", "y", "是")
    if t == "intlist":
        return [int(x) for x in str(v).replace("，", ",").split(",") if x != ""]
    if t == "strlist":
        return [x for x in str(v).replace("，", ",").split(",") if x != ""]
    return v


def register(key: str, name_cn: str, tier: str, maturity: str,
             inputs: Optional[List[InputSpec]] = None, desc: str = ""):
    def deco(fn: Callable[..., Dict[str, Any]]):
        REGISTRY[key] = EngineSpec(key=key, name_cn=name_cn, tier=tier,
                                   maturity=maturity, cast=fn,
                                   inputs=inputs or [], desc=desc)
        return fn
    return deco


def get_engine(key: str) -> EngineSpec:
    if key not in REGISTRY:
        raise KeyError(f"未注册的引擎：{key}，可用：{sorted(REGISTRY)}")
    return REGISTRY[key]


def all_engines() -> List[EngineSpec]:
    return [REGISTRY[k] for k in sorted(REGISTRY)]


def cast(key: str, raw: Optional[Dict[str, Any]] = None, **kw) -> Dict[str, Any]:
    spec = get_engine(key)
    params = dict(raw or {})
    params.update(kw)
    return spec.cast(**params)
