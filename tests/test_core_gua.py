# -*- coding: utf-8 -*-
from dayan.core import gua as G


def test_64_lookup():
    assert G.gua_name("坤", "乾") == "泰"      # 地天泰
    assert G.gua_name("乾", "坤") == "否"      # 天地否
    assert G.gua_name("坎", "离") == "既济"
    assert len(G._GUA_LOOKUP) == 64


def test_cuo_zong_hu():
    lines = G.lines_of("坤", "乾")             # 泰
    assert G.cuo_gua(lines) == "否"
    assert G.zong_gua(lines) == "否"
    hu_up, hu_lo = G.hu_gua(lines)
    assert G.gua_name(hu_up, hu_lo) == "归妹"


def test_palace_shi_ying():
    palace, idx = G.palace_of("泰")
    assert palace == "坤" and idx == 3         # 坤宫三世
    shi, ying = G.shi_ying("泰")
    assert (shi, ying) == (2, 5)              # 世三应上（0 起）


def test_nazhi_liuqin():
    # 既济属坎宫水：初爻寅木=子孙、三爻午火=妻财
    yao = G.nazhi_yao("既济")
    assert yao[0]["ganzhi"] == "戊寅" and yao[0]["liuqin"] == "子孙"
    assert yao[2]["ganzhi"] == "戊午" and yao[2]["liuqin"] == "妻财"
    assert yao[3]["liuqin"] == "父母"          # 申金生水
