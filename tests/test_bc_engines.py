# -*- coding: utf-8 -*-
import pytest
from xuanshu.engines import physiognomy, oracle


def test_face_rules():
    r = physiognomy.cast_physiognomy("face", ["命宫:明润", "财帛:饱满"])
    assert len(r["解读"]) == 2


def test_palm_rules():
    r = physiognomy.cast_physiognomy("palm", ["生命线:深长", "智慧线:清晰"])
    assert len(r["解读"]) == 2


def test_fengshui_luantou():
    r = physiognomy.cast_physiognomy("fengshui", [])
    assert any("青龙" in x for x in r["解读"])


def test_image_interface_guarded():
    with pytest.raises(NotImplementedError):
        physiognomy.extract_from_image("x.jpg")


def test_oracle_dream():
    r = oracle.cast_oracle("dream", "梦见掉牙流血")
    assert r["命中"] and r["命中"][0][0] == "掉牙"


def test_oracle_qian():
    r = oracle.cast_oracle("qian", no=1)
    assert r["签"]["no"] == 1
