# -*- coding: utf-8 -*-
"""引擎准确度测试：
1) 黄金历法锚点——日柱用儒略日数(JDN)纯算术独立验证，不依赖 lunar-python；
   锚点：1949-10-01 甲子日、2000-01-01 戊午日（史载/历算公认）。
2) 奇门拆补定局——用经典锚例（夏至上元甲子日 → 阴遁九局、冬至上元甲子日 → 阳遁一局）。
3) 六爻旬空 / 紫微六吉星禄存羊陀 / 神煞表——结构化断言。
"""
import datetime as dt

from dayan.core import wuxing as W
from dayan.engines import bazi, liuyao, qimen, ziwei


# ---------- 黄金锚点：日柱 JDN 纯算术 ----------
def jdn_day_ganzhi(y: int, m: int, d: int) -> str:
    """日柱 = (JDN + 49) % 60，甲子=0。JDN = 公历 toordinal + 1721425（格里历）。"""
    jdn = dt.date(y, m, d).toordinal() + 1721425
    return W.JIAZI[(jdn + 49) % 60]


def test_golden_day_pillar_anchors():
    """锚点本身先自证：1949-10-01 甲子日、2000-01-01 戊午日。"""
    assert jdn_day_ganzhi(1949, 10, 1) == "甲子"
    assert jdn_day_ganzhi(2000, 1, 1) == "戊午"


def test_bazi_day_pillar_matches_jdn():
    """八字引擎的日柱必须与 JDN 纯算术一致（覆盖跨年/立春/月末/闰日边界）。"""
    cases = [(1949, 10, 1), (2000, 1, 1), (2024, 2, 4), (2024, 2, 3),
             (1999, 12, 31), (2000, 2, 29), (1984, 2, 2), (2024, 6, 29)]
    for y, m, d in cases:
        r = bazi.cast_bazi(year=y, month=m, day=d, hour=12)
        assert r["pillars"]["day"]["ganzhi"] == jdn_day_ganzhi(y, m, d), (y, m, d)


def test_bazi_year_month_pillar_anchors():
    """年柱锚点 1949 己丑 / 2024 甲辰；月柱锚点 甲年卯月=丁卯（五虎遁，惊蛰后）。"""
    assert bazi.cast_bazi(year=1949, month=10, day=1)["pillars"]["year"]["ganzhi"][0] == "己"
    r = bazi.cast_bazi(year=2024, month=3, day=15)   # 惊蛰(3/5)后 → 卯月
    assert r["pillars"]["year"]["ganzhi"] == "甲辰"
    assert r["pillars"]["month"]["ganzhi"] == "丁卯"


# ---------- 奇门拆补定局 ----------
def test_qimen_chabu_summer_classic():
    """经典锚例：2024-06-29 夏至后甲子日（上元）→ 阴遁九局。"""
    assert jdn_day_ganzhi(2024, 6, 29) == "甲子"       # 先独立验证日柱
    info = qimen.resolve_ju(2024, 6, 29)
    assert info["term"] == "夏至" and info["fu_tou"] == "甲子"
    assert info["yuan"] == 0 and info["dun"] == "阴" and info["ju"] == 9


def test_qimen_chabu_winter():
    """冬至上元：2024-12-26 甲子日 → 阳遁一局；癸亥日（符头己未下元）→ 阳遁四局。"""
    assert jdn_day_ganzhi(2024, 12, 26) == "甲子"
    info = qimen.resolve_ju(2024, 12, 26)
    assert info["term"] == "冬至" and info["fu_tou"] == "甲子"
    assert info["yuan"] == 0 and info["dun"] == "阳" and info["ju"] == 1
    info2 = qimen.resolve_ju(2024, 12, 25)             # 癸亥日，符头己未 → 下元
    assert info2["fu_tou"] == "己未" and info2["yuan"] == 2 and info2["ju"] == 4


def test_qimen_ju_table_canonical_values():
    """局数表抽查通行口诀，且 24 节气齐全、三元局数均在 1-9。"""
    assert qimen.JU_TABLE["冬至"] == (1, 7, 4)
    assert qimen.JU_TABLE["夏至"] == (9, 3, 6)
    assert qimen.JU_TABLE["惊蛰"] == (1, 7, 4)
    assert qimen.JU_TABLE["大雪"] == (4, 7, 1)
    assert len(qimen.JU_TABLE) == 24
    assert len(qimen.YANG_TERMS) == 12
    for a, b, c in qimen.JU_TABLE.values():
        assert all(1 <= x <= 9 for x in (a, b, c))


def test_qimen_date_interface_and_manual_compat():
    """传日期自动定局+自动时柱；手动 dun/ju 旧接口不受影响。"""
    r = qimen.cast_qimen(year=2024, month=6, day=29, hour=10)
    assert r["遁"] == "阴遁9局" and r["定局"]["符头"] == "甲子"
    assert r["时柱"] and len(r["时柱"]) == 2
    r2 = qimen.cast_qimen(dun="阳", ju=1, hour_ganzhi="甲子")
    assert r2["遁"] == "阳遁1局" and "定局" not in r2


# ---------- 六爻旬空 ----------
def test_liuyao_xunkong():
    """甲子日旬空戌亥；乾卦上爻戌落空亡。"""
    r = liuyao.cast_liuyao(lines=[7, 7, 7, 7, 7, 7], day_gan="甲", day_ganzhi="甲子")
    assert r["旬空"] == ["戌", "亥"]
    assert r["六爻_初到上"][5]["zhi"] == "戌" and r["六爻_初到上"][5]["kongwang"]
    assert not r["六爻_初到上"][0]["kongwang"]
    r2 = liuyao.cast_liuyao(lines=[7, 7, 7, 7, 7, 7])  # 未提供日柱：向后兼容
    assert r2["旬空"] == []


# ---------- 紫微六吉星 / 禄存擎羊陀罗 ----------
def _aux_map(r):
    out = {}
    for p in r["十二宫"].values():
        for s in p["辅星"]:
            out[s] = p["地支"]
    return out


def test_ziwei_aux_stars_positions():
    """2024-02-15（甲辰年正月）子时：左辅辰/右弼戌/文昌戌/文曲辰/禄存寅/羊卯/陀丑。"""
    r = ziwei.cast_ziwei(year=2024, month=2, day=15, hour=0)
    aux = _aux_map(r)
    assert aux["左辅"] == "辰" and aux["右弼"] == "戌"
    assert aux["文昌"] == "戌" and aux["文曲"] == "辰"
    assert aux["禄存"] == "寅" and aux["擎羊"] == "卯" and aux["陀罗"] == "丑"


def test_ziwei_aux_stars_unique():
    """每颗辅星全盘恰好出现一次（12 宫不重不漏）。"""
    r = ziwei.cast_ziwei(year=1990, month=3, day=15, hour=12)
    aux = _aux_map(r)
    assert sorted(aux) == sorted(["左辅", "右弼", "文昌", "文曲",
                                  "禄存", "擎羊", "陀罗"])


# ---------- 八字神煞表 ----------
def test_shensha_tables_consistent():
    """神煞表与三合局互验：将星=帝旺支、华盖=墓库支、劫煞=绝位、亡神=禄位。"""
    for z in ("申", "子", "辰"):
        assert W.JIANGXING[z] == "子" and W.HUAGAI[z] == "辰"
        assert W.JIESHA[z] == "巳" and W.WANGSHEN[z] == "亥"
    for z in ("寅", "午", "戌"):
        assert W.JIANGXING[z] == "午" and W.HUAGAI[z] == "戌"
        assert W.JIESHA[z] == "亥" and W.WANGSHEN[z] == "巳"
    for z in ("巳", "酉", "丑"):
        assert W.JIANGXING[z] == "酉" and W.HUAGAI[z] == "丑"
        assert W.JIESHA[z] == "寅" and W.WANGSHEN[z] == "申"
    for z in ("亥", "卯", "未"):
        assert W.JIANGXING[z] == "卯" and W.HUAGAI[z] == "未"
        assert W.JIESHA[z] == "申" and W.WANGSHEN[z] == "寅"
    assert W.GUCHEN["子"] == "寅" and W.GUASU["子"] == "戌"
    assert len(W.JIANGXING) == 12 and len(W.GUCHEN) == 12


def test_bazi_shensha_rendered():
    """新神煞进入排盘输出（命中或空均可，但字段结构必须稳定）。"""
    r = bazi.cast_bazi(year=1990, month=3, day=15, hour=12)
    assert isinstance(r["shensha"], dict)
    assert all(isinstance(v, list) and v for v in r["shensha"].values())
