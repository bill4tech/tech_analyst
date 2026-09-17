#!/usr/bin/env python3
"""Batch Base64+XOR string decrypt (StringFog / obfuscated two-arg calls).

Usage:
    python3 decrypt_strings.py <jadx_sources_dir> [--pattern REGEX] [keywords...]
    python3 decrypt_strings.py --pair CIPHER KEY
    python3 decrypt_strings.py <dir> --json

Default patterns:
    StringFog.decrypt("c","k")
    .O("c","k")   # common obfuscated name; override with --pattern after you confirm
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys

DEFAULT_PATTERNS = [
    r'StringFog\.decrypt\("((?:[^"\\]|\\.)*)",\s*"((?:[^"\\]|\\.)*)"\)',
    r'\.O\("((?:[^"\\]|\\.)*)",\s*"((?:[^"\\]|\\.)*)"\)',
]

NOISE_PREFIX = ("null cannot be cast", "type inference failed")
DEFAULT_KEEP = ("http", "api/", "appkey", "app_key", "token", "secret", "oss", "zego", "rong")


def decrypt(cipher: str, key: str) -> str:
    c = cipher.replace("\\n", "\n")
    k = key.replace("\\n", "\n")
    cb = base64.b64decode(c)
    kb = base64.b64decode(k)
    if not kb:
        raise ValueError("empty key")
    return bytes(cb[i] ^ kb[i % len(kb)] for i in range(len(cb))).decode(
        "utf-8", errors="replace"
    )


def should_keep(plain: str, filters: list[str]) -> bool:
    low = plain.lower()
    if any(low.startswith(p) for p in NOISE_PREFIX):
        return False
    if filters:
        return any(f.lower() in low for f in filters)
    if any(t in low for t in DEFAULT_KEEP):
        return True
    return len(plain) > 20 and plain.isprintable()


def walk_java(src_dir: str):
    for root, _, files in os.walk(src_dir):
        for fn in files:
            if fn.endswith(".java") or fn.endswith(".kt"):
                yield os.path.join(root, fn)


def main() -> None:
    if len(sys.argv) >= 2 and sys.argv[1] == "--pair":
        if len(sys.argv) != 4:
            print("用法: decrypt_strings.py --pair <密文> <密钥>", file=sys.stderr)
            sys.exit(1)
        print(decrypt(sys.argv[2], sys.argv[3]))
        return

    p = argparse.ArgumentParser()
    p.add_argument("src_dir")
    p.add_argument("--pattern", action="append", default=[], help="自定义调用正则，需含两个捕获组")
    p.add_argument("--json", action="store_true")
    p.add_argument("keywords", nargs="*")
    args = p.parse_args()

    if not os.path.isdir(args.src_dir):
        print(f"error: 目录不存在: {args.src_dir}", file=sys.stderr)
        sys.exit(1)

    raw_pats = args.pattern or DEFAULT_PATTERNS
    compiled = [re.compile(x) for x in raw_pats]
    results = []
    for path in walk_java(args.src_dir):
        try:
            src = open(path, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        rel = os.path.relpath(path, args.src_dir)
        for pat in compiled:
            for m in pat.finditer(src):
                cipher, key = m.group(1), m.group(2)
                try:
                    plain = decrypt(cipher, key)
                except Exception:
                    continue
                if not plain or not should_keep(plain, args.keywords):
                    continue
                results.append({"file": rel, "plain": plain})

    uniq = []
    seen = set()
    for r in results:
        if r["plain"] in seen:
            continue
        seen.add(r["plain"])
        uniq.append(r)

    if args.json:
        print(json.dumps(uniq, ensure_ascii=False, indent=2))
    else:
        for r in uniq:
            print(f"{r['file']}: {r['plain']}")
        print(f"\n--- 共解密 {len(uniq)} 条唯一字符串 ---", file=sys.stderr)


if __name__ == "__main__":
    main()
