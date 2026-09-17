#!/usr/bin/env python3
"""Scan files for URLs, API-ish paths, and well-known key shapes.

Usage:
    python3 scan_secrets.py <dir_or_file> [more...]
"""

from __future__ import annotations

import os
import re
import sys

SKIP_DIR = {".git", "node_modules", "__pycache__", "build"}
TEXT_EXT = {
    ".java", ".kt", ".xml", ".json", ".js", ".txt", ".properties",
    ".gradle", ".smali", ".html", ".jsbundle", ".plist", ".cfg", ".ini",
}

PATTERNS = [
    ("url", re.compile(r"https?://[^\s\"'<>\\]{4,200}", re.I)),
    ("api_path", re.compile(r"(?<![\w])(/api/|/v[12]/)[A-Za-z0-9_\-./]{2,80}")),
    ("google_api", re.compile(r"AIza[0-9A-Za-z\-_]{35}")),
    ("aws_akid", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("pem", re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----")),
    ("jwt", re.compile(r"eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")),
    ("firebase", re.compile(r"AAAA[A-Za-z0-9_\-]{7}:[A-Za-z0-9_\-]{20,}")),
    ("keyword", re.compile(
        r"(?i)(app[_-]?id|app[_-]?key|appkey|appsecret|secret[_-]?key|access[_-]?key|"
        r"aws_secret|oss[_-]?access|rong[_-]?cloud|zego)[^\n]{0,80}"
    )),
]


def iter_files(root: str):
    if os.path.isfile(root):
        yield root
        return
    for dirpath, dirnames, files in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR]
        for fn in files:
            yield os.path.join(dirpath, fn)


def is_probably_text(path: str) -> bool:
    ext = os.path.splitext(path)[1].lower()
    if ext in TEXT_EXT:
        return True
    base = os.path.basename(path).lower()
    if base in ("google-services.json", "network_security_config.xml"):
        return True
    if ext in (".so", ".dex", ".apk", ".zip", ".png", ".jpg", ".webp", ".mp4"):
        return False
    return ext in {".xml", ".json", ".txt"}


def scan_file(path: str) -> list[tuple[str, str]]:
    try:
        data = open(path, "rb").read(2_000_000)
    except OSError:
        return []
    if b"\x00" in data[:1024] and not path.endswith(".so"):
        # still allow strings-like extract from small xml-ish
        if not is_probably_text(path):
            text = "".join(chr(b) if 32 <= b < 127 else "\n" for b in data[:500000])
        else:
            text = data.decode("utf-8", errors="ignore")
    else:
        text = data.decode("utf-8", errors="ignore")
    hits = []
    for kind, pat in PATTERNS:
        for m in pat.finditer(text):
            s = m.group(0).strip()
            if len(s) > 300:
                s = s[:300] + "…"
            hits.append((kind, s))
    return hits


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    seen = set()
    n = 0
    for root in sys.argv[1:]:
        if not os.path.exists(root):
            print(f"# skip missing {root}", file=sys.stderr)
            continue
        for path in iter_files(root):
            if not is_probably_text(path) and not path.endswith(".so"):
                continue
            for kind, s in scan_file(path):
                key = (kind, s)
                if key in seen:
                    continue
                seen.add(key)
                n += 1
                print(f"{kind}\t{path}\t{s}")
    print(f"# unique hits: {n}", file=sys.stderr)


if __name__ == "__main__":
    main()
