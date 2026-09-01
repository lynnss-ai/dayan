# -*- coding: utf-8 -*-
"""面相 / 手相 / 峦头【规则表 + 多模态接口】引擎（B 级）。
确定性的是"部位/线丘/形煞 → 传统含义"的对照规则；不确定的是从照片里
定位部位、判断气色与纹路——这部分由 Qwen3.8-27B 多模态先抽成结构化
features 再喂给 analyze_*。extract_from_image 仅给出接口约定。
"""
from typing import Dict, List

from ..core.registry import register, InputSpec

# 面相十二宫：部位 → 主管
FACE12 = {
    "命宫": "印堂，主整体运势与心境", "财帛": "鼻，主财运与现实获取",
    "兄弟": "眉，主手足同辈关系", "夫妻": "眼尾鱼尾，主婚姻感情",
    "子女": "泪堂卧蚕，主子息与亲缘", "疾厄": "山根，主健康根基",
    "迁移": "天仓边地，主外出远行", "交友": "地阁下巴，主部属晚运",
    "官禄": "额头天庭，主事业功名", "田宅": "眉眼之间，主家产居所",
    "福德": "眉尾上方，主福报享受", "父母": "日月角，主父母长辈"}
# 三停
SANTING = {"上停": "额（约15-30岁早年运）", "中停": "眉至鼻（约31-50岁中年运）",
           "下停": "鼻下至颌（约50岁后晚年运）"}
# 状态 → 传统判语（保守、非绝对）
FACE_STATE = {"明润": "传统视为气色舒展、较顺遂", "饱满": "传统视为根基厚实",
              "纹": "主操劳或波动，需结合部位", "痣": "按部位有不同说法，多为提示而非定论",
              "凹陷": "传统视为该宫偏弱、需多经营", "赤红": "主近期急躁或开销",
              "青暗": "传统提示休整、注意健康"}
# 手相主线与丘
PALM_LINE = {"生命线": "体质与精力节奏（非寿命长短）", "智慧线": "思维与学习方式",
             "感情线": "情感表达与关系模式", "命运线": "事业与人生主线（可无）",
             "婚姻线": "亲密关系走向（参考）"}
PALM_MOUNT = {"金星丘": "活力与情感欲求", "木星丘": "自信与领导欲", "土星丘": "责任与内省",
              "太阳丘": "审美与名声", "水星丘": "沟通与商业", "月丘": "想象与直觉"}
# 峦头：四灵与常见形煞
SILING = {"青龙": "左护（宜低缓有情）", "白虎": "右护（宜顺伏）",
          "朱雀": "前方明堂（宜开阔）", "玄武": "后方靠山（宜厚实）"}
XINGSHA = {"天斩煞": "两楼夹缝对窗，传统主波动，可用遮挡/绿植缓冲",
           "路冲": "道路直冲门户，传统主不稳，宜玄关/屏缓冲",
           "尖角煞": "建筑尖角对射，传统主摩擦，宜化挡",
           "反弓": "道路/水流反背，传统主离散，宜收气"}


def _parse(features: List[str]):
    out = {}
    for f in features:
        if ":" in f:
            k, v = f.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def analyze_face(features: Dict[str, str]) -> List[str]:
    rows = []
    for part, state in features.items():
        if part in FACE12 and state in FACE_STATE:
            rows.append(f"{part}（{FACE12[part]}）见「{state}」：{FACE_STATE[state]}")
    return rows


def analyze_palm(features: Dict[str, str]) -> List[str]:
    rows = []
    for part, state in features.items():
        base = PALM_LINE.get(part) or PALM_MOUNT.get(part)
        if base:
            rows.append(f"{part}（{base}）特征「{state}」：按传统手相作参考性解读")
    return rows


def extract_from_image(image_path: str):
    """多模态接口约定：由 Qwen3.8-27B 视觉模型把照片抽成
    {部位: 状态} / {线丘: 特征}，再调用 analyze_*。本环境不做 CV，故显式报错。"""
    raise NotImplementedError(
        "请用 Qwen3.8-27B 多模态将图片结构化为 features（如 命宫:明润），再传入分析；"
        f"收到图片路径 {image_path}，规则引擎本身不做像素识别。")


@register("physiognomy", "面相手相峦头", "B", "interface",
          inputs=[InputSpec("mode", "str", False, "face", "face/palm/fengshui"),
                  InputSpec("features", "strlist", False, [],
                            "部位:状态，逗号分隔，如 命宫:明润,财帛:饱满")],
          desc="部位/线丘/形煞→含义规则表；图像特征由多模态模型抽取")
def cast_physiognomy(mode: str = "face", features: List[str] = None) -> Dict:
    feats = _parse(features or [])
    if mode == "face":
        rows = analyze_face(feats)
        table = FACE12
        title = "面相十二宫"
    elif mode == "palm":
        rows = analyze_palm(feats)
        table = {**PALM_LINE, **PALM_MOUNT}
        title = "手相线丘"
    else:
        rows = [f"{k}：{v}" for k, v in SILING.items()] + \
               [f"{k}：{v}" for k, v in XINGSHA.items() if k in feats or not feats]
        table = {**SILING, **XINGSHA}
        title = "峦头四灵形煞"
    res = {"mode": mode, "规则表": title, "输入特征": feats, "解读": rows}
    L = [f"【{title}·规则层】输入：{feats}", *rows,
         "说明：部位/线丘含义为传统对照表；气色、纹路与实景需多模态先抽取，结论仅供文化参考。"]
    res["text"] = "\n".join(L)
    return res
