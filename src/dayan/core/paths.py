# -*- coding: utf-8 -*-
"""输出文件统一写入入口：所有"把结果写到磁盘"的代码都应经由 safe_write，
在此单点完成白名单校验（输出必须位于当前工作目录内、不能是目录）后打开文件，
避免散落各处的直接写盘绕过校验。"""
import os


def resolve_out(path: str) -> str:
    """校验并返回绝对化输出路径：必须位于当前工作目录内、不能是目录本身。"""
    root = os.path.realpath(os.getcwd())
    p = os.path.realpath(os.path.join(root, os.path.expanduser(path)))
    if p != root and not p.startswith(root + os.sep):
        raise ValueError(f"输出路径必须位于当前工作目录内：{p}")
    if os.path.isdir(p):
        raise ValueError(f"输出路径不能是目录：{p}")
    parent = os.path.dirname(p)
    if parent:
        os.makedirs(parent, exist_ok=True)
    return p


def safe_write(path: str, encoding: str = "utf-8"):
    """校验并打开输出文件，返回写句柄（配合 with 使用）。"""
    p = resolve_out(path)
    fd = os.open(p, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o644)
    return os.fdopen(fd, "w", encoding=encoding)
