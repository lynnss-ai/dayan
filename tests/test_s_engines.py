# -*- coding: utf-8 -*-
from dayan.engines import (almanac, name_fivegrid, meihua, numerology,
                             bazhai, zhouyi, xuankong, tarot)


def test_almanac():
    r = almanac.cast_almanac(2024, 3, 15)
    assert r["日干支"] == "戊寅"
    assert r["值神"].startswith("青龙") and r["黄黑"] == "黄道"
    assert len(r["十二时辰"]) == 12
    assert r["十二时辰"][0]["ganzhi"] == "壬子"     # 戊日五鼠遁起壬子


def test_name_fivegrid():
    r = name_fivegrid.cast_name([11], [9, 7])
    g = r["五格"]
    assert (g["天格"]["数"], g["人格"]["数"], g["地格"]["数"],
            g["总格"]["数"], g["外格"]["数"]) == (12, 20, 16, 27, 8)
    assert name_fivegrid.num81(16) == "吉" and name_fivegrid.num81(34) == "凶"


def test_meihua():
    r = meihua.cast_meihua(mode="number", n1=5, n2=8)
    assert r["本卦"].startswith("观") and r["动爻"] == 1
    assert r["体卦"] == "巽" and r["用卦"] == "坤" and r["变卦"] == "益"


def test_numerology():
    r = numerology.cast_numerology(1990, 3, 15)
    assert r["生命路径数"] == 1


def test_bazhai():
    r = bazhai.cast_bazhai(1990, "male")
    assert r["命卦"] == "坎" and r["命组"] == "东四命"
    assert r["游年八方"]["巽"]["星"] == "生气"
    assert r["游年八方"]["离"]["星"] == "延年"


def test_zhouyi():
    r = zhouyi.cast_zhouyi(name="泰", dong=[1])
    assert r["错卦"] == "否" and r["变卦"] == "升" and r["世爻"] == 3


def test_xuankong():
    r = xuankong.cast_xuankong(2024, "子", "午")
    assert r["三元九运"] == 9
    assert r["运盘"][5] == 9 and r["山星盘"][5] == 5 and r["向星盘"][5] == 4


def test_tarot_reproducible():
    a = tarot.cast_tarot("three", 123)
    b = tarot.cast_tarot("three", 123)
    assert [x["牌"] for x in a["抽牌"]] == [x["牌"] for x in b["抽牌"]]
    c = tarot.cast_tarot("celtic", 1)
    assert len(c["抽牌"]) == 10
