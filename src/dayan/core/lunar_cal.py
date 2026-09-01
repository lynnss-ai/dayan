# -*- coding: utf-8 -*-
"""历法层：统一封装 lunar-python（八字、择日、紫微、梅花时间起卦共用）。"""
import datetime as dt
from dataclasses import dataclass
from typing import Optional, Tuple

from lunar_python import Solar


@dataclass
class Subject:
    year: int
    month: int
    day: int
    hour: int = 12
    minute: int = 0
    gender: str = "male"               # male/female
    longitude: Optional[float] = None


def gender_code(gender: str) -> int:
    g = str(gender).lower()
    if g in ("male", "m", "男", "1"):
        return 1
    if g in ("female", "f", "女", "0"):
        return 0
    raise ValueError("gender 必须是 male/female")


def true_solar_time(subj: Subject) -> Tuple[int, int, int, int, int]:
    """平太阳时校正：相对东八区标准经线 120°，每偏 1° 差 4 分钟。"""
    y, mo, d, h, mi = subj.year, subj.month, subj.day, subj.hour, subj.minute
    if subj.longitude is None:
        return y, mo, d, h, mi
    base = dt.datetime(y, mo, d, h, mi)
    adj = base + dt.timedelta(minutes=(subj.longitude - 120.0) * 4.0)
    return adj.year, adj.month, adj.day, adj.hour, adj.minute


def to_lunar(subj: Subject):
    """Subject → (lunar, eightchar, gender_code)，已做可选真太阳时校正。"""
    y, mo, d, h, mi = true_solar_time(subj)
    solar = Solar.fromYmdHms(y, mo, d, h, mi, 0)
    lunar = solar.getLunar()
    return lunar, lunar.getEightChar(), gender_code(subj.gender)


def lunar_from_ymd(year: int, month: int, day: int, hour: int = 12, minute: int = 0):
    solar = Solar.fromYmdHms(year, month, day, hour, minute, 0)
    return solar.getLunar()
