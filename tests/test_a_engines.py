# -*- coding: utf-8 -*-
from lunar_python import Solar
from dayan.engines import bazi, ziwei, liuyao, qimen, liuren, astrology


def test_bazi_matches_lunar():
    r = bazi.cast_bazi(1990, 3, 15, 12, 0, "male")
    ec = Solar.fromYmdHms(1990, 3, 15, 12, 0, 0).getLunar().getEightChar()
    p = r["pillars"]
    assert p["year"]["ganzhi"] == ec.getYear() == "庚午"
    assert p["day"]["ganzhi"] == ec.getDay() == "己卯"
    assert r["day_master"] == "己"
    assert r["xunkong"] and "relations" in r and "shensha" in r
    assert r["liunian"][0]["ganzhi"] == "庚午"      # 1990 流年
    assert len(r["dayun"]["list"]) == 8


def test_ziwei_consistency():
    r = ziwei.cast_ziwei(1990, 3, 15, 12, "male")
    assert r["命宫"].startswith("乙酉") and r["五行局"] == "水2局"
    assert r["紫微在"] == "午" and r["天府在"] == "戌"
    stars = [s for p in r["十二宫"].values() for s in p["主星"]]
    assert len(stars) == 14 and len(set(stars)) == 14   # 十四正曜不重不漏
    assert r["生年四化"]["太阳"] == "化禄"               # 庚干


def test_liuyao():
    r = liuyao.cast_liuyao(lines=[7, 8, 9, 8, 7, 6], day_gan="甲")
    assert r["本卦"] == "既济" and r["变卦"] == "益"
    assert r["世爻"] == 3 and r["应爻"] == 6
    yao = {x["pos"]: x for x in r["六爻_初到上"]}
    assert yao[0]["liuishen"] == "青龙" and yao[0]["liuqin"] == "子孙"


def test_qimen_base_case():
    r = qimen.cast_qimen("阳", 1, "甲子")
    cells = r["九宫"]
    assert cells[1]["地盘"] == "戊" and cells[1]["九星"] == "天蓬"
    assert cells[1]["八门"] == "休门" and cells[1]["八神"] == "值符"
    assert cells[9]["地盘"] == "乙"                # 阳一局三奇顺布至离宫


def test_liuren():
    r = liuren.cast_liuren("亥", "子", "甲", "子")
    assert r["天地盘"]["子"] == "亥"               # 月将加时
    ke1 = r["四课"][0]
    assert ke1["下"] == "寅" and ke1["上"] == "丑"  # 甲寄寅，寅上丑


def test_astrology_aspect():
    r = astrology.cast_astrology(["太阳:白羊:10", "火星:巨蟹:10"])
    asp = [(a["相位"]) for a in r["相位"]]
    assert "刑相" in asp                       # 白羊0宫与巨蟹3宫差90°
    assert r["元素分布"]["火"] == 1 and r["元素分布"]["水"] == 1
