# -*- coding: utf-8 -*-
from dayan.core import wuxing as W


def test_shishen():
    assert W.shishen("甲", "庚") == "七杀"      # 阳金克阳木，同阳
    assert W.shishen("甲", "乙") == "劫财"      # 同五行异阴阳
    assert W.shishen("甲", "丁") == "伤官"      # 木生火，异阴阳
    assert W.shishen("甲", "甲") == "比肩"      # 同字也为比肩而非日主


def test_nayin_and_jiazi():
    assert len(W.JIAZI) == 60
    assert W.NAYIN["甲子"] == "海中金"
    assert W.NAYIN["庚午"] == "路旁土"


def test_dun():
    assert W.month_gan("甲", "寅") == "丙"      # 五虎遁甲年丙寅月
    assert W.hour_gan("甲", "子") == "甲"       # 五鼠遁甲日甲子时
    assert W.hour_gan("甲", "丑") == "乙"


def test_xunkong():
    assert W.xunkong("甲", "子") == ["戌", "亥"]
    assert W.xunkong("丙", "寅") == ["戌", "亥"]   # 甲子旬
    assert W.xunkong("丁", "丑") == ["申", "酉"]   # 甲戌旬空申酉


def test_chong_hai_he():
    assert W.CHONG["子"] == "午"
    assert W.LIUHAI["子"] == "未"
    r = W.zhi_relations(["申", "子", "辰", "午"])
    assert ["子", "辰", "申", "水"] in r["三合"]
    assert any(pair == ["子", "午"] for pair in r["六冲"])
    g = W.gan_relations(["甲", "己", "丙"])
    assert ["甲", "己", "土"] in g["天干五合"]


def test_shensha():
    assert "丑" in W.TIANYI["甲"]
    assert W.WENCHANG["甲"] == "巳"
    assert W.TAOHUA["申"] == "酉" and W.YIMA["申"] == "寅"
