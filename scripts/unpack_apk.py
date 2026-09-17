#!/usr/bin/env python3
"""Unpack apk / apks / xapk into work_dir/input/. Prints JSON summary to stdout.

Usage:
    python3 unpack_apk.py <input_file> <work_dir>
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import zipfile


def die(msg: str, code: int = 1) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(code)


def list_apks(z: zipfile.ZipFile) -> list[str]:
    return [n for n in z.namelist() if n.lower().endswith(".apk") and not n.endswith("/")]


def pick_base(names: list[str]) -> str:
    lower = {n: os.path.basename(n).lower() for n in names}
    for n, b in lower.items():
        if b == "base.apk":
            return n
    # xapk often has a single large apk named after the package
    if len(names) == 1:
        return names[0]
    # prefer non-split
    non_split = [n for n in names if "split" not in lower[n] and "config." not in lower[n]]
    if len(non_split) == 1:
        return non_split[0]
    return names[0]


def abi_from_name(name: str) -> str | None:
    b = os.path.basename(name).lower()
    if "arm64" in b:
        return "arm64-v8a"
    if "armeabi" in b or "armv7" in b:
        return "armeabi-v7a"
    if "x86_64" in b:
        return "x86_64"
    if "x86" in b:
        return "x86"
    return None


def main() -> None:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    src = os.path.abspath(sys.argv[1])
    work = os.path.abspath(sys.argv[2])
    if not os.path.isfile(src):
        die(f"file not found: {src}")

    input_dir = os.path.join(work, "input")
    for sub in ("input", "static", "jadx", "decrypt", "runtime", "report"):
        os.makedirs(os.path.join(work, sub), exist_ok=True)

    ext = os.path.splitext(src)[1].lower()
    extracted = []
    base_apk = None
    splits = []

    if ext == ".apk":
        dest = os.path.join(input_dir, os.path.basename(src))
        if os.path.abspath(src) != dest:
            shutil.copy2(src, dest)
        base_apk = dest
        extracted = [dest]
    elif ext in (".apks", ".xapk", ".zip"):
        if not zipfile.is_zipfile(src):
            die("not a zip (apks/xapk should be zip)")
        with zipfile.ZipFile(src) as z:
            apks = list_apks(z)
            if not apks:
                die("no .apk inside archive")
            base_name = pick_base(apks)
            for n in apks:
                out = os.path.join(input_dir, os.path.basename(n))
                with z.open(n) as inf, open(out, "wb") as outf:
                    shutil.copyfileobj(inf, outf)
                extracted.append(out)
                if n == base_name:
                    base_apk = out
                else:
                    splits.append(out)
    else:
        die(f"unsupported extension: {ext}")

    abis = []
    for p in extracted:
        a = abi_from_name(p)
        if a and a not in abis:
            abis.append(a)

    summary = {
        "source": src,
        "work_dir": work,
        "base_apk": base_apk,
        "splits": splits,
        "all_apks": extracted,
        "abis_from_filenames": abis,
        "install_hint": "adb install-multiple -r " + " ".join(extracted),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
