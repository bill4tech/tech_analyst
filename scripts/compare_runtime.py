#!/usr/bin/env python3
"""Diff two pull_app_data directories (guest vs authed).

Usage:
    python3 compare_runtime.py <guest_dir> <authed_dir>
"""

from __future__ import annotations

import os
import sys


SKIP = {".DS_Store"}


def files_of(root: str) -> dict[str, str]:
    out = {}
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if fn in SKIP:
                continue
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, root)
            try:
                out[rel] = open(path, "rb").read()
            except OSError:
                continue
    return out


def printable_strings(data: bytes, min_len: int = 8) -> set[str]:
    buf = []
    found = set()
    for b in data:
        if 32 <= b < 127:
            buf.append(chr(b))
        else:
            if len(buf) >= min_len:
                found.add("".join(buf))
            buf = []
    if len(buf) >= min_len:
        found.add("".join(buf))
    return found


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    guest, authed = sys.argv[1], sys.argv[2]
    g = files_of(guest)
    a = files_of(authed)

    only_a = sorted(set(a) - set(g))
    only_g = sorted(set(g) - set(a))
    both = sorted(set(a) & set(g))

    print("== 仅登录后存在的文件 ==")
    for rel in only_a:
        print(f"  + {rel} ({len(a[rel])} bytes)")
    print("== 仅游客存在的文件 ==")
    for rel in only_g:
        print(f"  - {rel}")
    print("== 内容有变化的文件 ==")
    for rel in both:
        if g[rel] == a[rel]:
            continue
        print(f"  * {rel}  guest={len(g[rel])}B authed={len(a[rel])}B")
        gs, aus = printable_strings(g[rel]), printable_strings(a[rel])
        new = sorted(aus - gs)
        for s in new[:40]:
            if any(k in s.lower() for k in ("key", "token", "appid", "app_id", "secret", "oss", "http", "zego", "rong")):
                print(f"      new: {s[:200]}")
        extra = [s for s in new if len(s) > 20][:15]
        for s in extra:
            print(f"      str: {s[:200]}")


if __name__ == "__main__":
    main()
