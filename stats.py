# -*- coding: utf-8 -*-
"""Thong ke theo NGAY cho tung kenh: so video dang + so reply.
Dung chung boi dang.py (video), cmt.py (reply), tool_gui.py (hien thi).
Luu o stats/<kenh>.json = {"YYYY-MM-DD": {"video": n, "reply": m}, ...}
"""
import os
import json
from datetime import date

_BASE = os.path.dirname(os.path.abspath(__file__))
STATS_DIR = os.path.join(_BASE, "stats")


def _path(channel):
    return os.path.join(STATS_DIR, channel + ".json")


def _load(channel):
    try:
        with open(_path(channel), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def bump(channel, kind, n=1):
    """Tang dem cua HOM NAY. kind = 'video' | 'reply'."""
    if not channel or n <= 0:
        return
    try:
        os.makedirs(STATS_DIR, exist_ok=True)
        d = _load(channel)
        today = date.today().isoformat()
        day = d.get(today) or {}
        day[kind] = int(day.get(kind, 0)) + n
        d[today] = day
        if len(d) > 45:                       # giu ~35 ngay gan nhat
            for k in sorted(d.keys())[:-35]:
                d.pop(k, None)
        with open(_path(channel), "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False)
    except Exception:
        pass


def today_counts(channel):
    """(so video hom nay, so reply hom nay)."""
    day = _load(channel).get(date.today().isoformat()) or {}
    return int(day.get("video", 0)), int(day.get("reply", 0))
