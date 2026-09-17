#!/usr/bin/env python3
"""
APK 静态信息提取器 — 只提取纯事实数据，不做分析判断。
用法:
    python3 extract_info.py <apk_path>
    python3 extract_info.py <apk_path> --json        # 仅输出 JSON（便于管道）
输出: 基本信息/权限/组件/类数/包名前缀/框架标记/native库/assets
"""

import glob
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter


def find_aapt():
    p = shutil.which("aapt")
    if p:
        return p
    roots = [
        os.path.expanduser("~/Library/Android/sdk/build-tools"),
        os.path.expanduser("~/Android/Sdk/build-tools"),
    ]
    for root in roots:
        hits = sorted(glob.glob(os.path.join(root, "*", "aapt")))
        if hits:
            return hits[-1]
    return None


def aapt_facts(apk_path):
    """Minimal facts when androguard cannot parse the DEX."""
    aapt = find_aapt()
    if not aapt:
        return {"aapt_error": "aapt not found"}
    try:
        out = subprocess.check_output(
            [aapt, "dump", "badging", apk_path],
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
    except Exception as e:
        return {"aapt_error": str(e)}
    facts = {"aapt_ok": True}
    m = re.search(r"package: name='([^']+)'", out)
    if m:
        facts["package_name"] = m.group(1)
    m = re.search(r"versionName='([^']+)'", out)
    if m:
        facts["version_name"] = m.group(1)
    m = re.search(r"versionCode='([^']+)'", out)
    if m:
        facts["version_code"] = m.group(1)
    m = re.search(r"sdkVersion:'([^']+)'", out)
    if m:
        facts["min_sdk"] = m.group(1)
    m = re.search(r"targetSdkVersion:'([^']+)'", out)
    if m:
        facts["target_sdk"] = m.group(1)
    m = re.search(r"native-code: ([^\n]+)", out)
    if m:
        facts["native_code"] = m.group(1).replace("'", "").split()
    m = re.search(r"launchable-activity: name='([^']+)'", out)
    if m:
        facts["launchable_activity"] = m.group(1)
    facts["permissions"] = re.findall(r"uses-permission: name='([^']+)'", out)
    return facts


def extract_prefixes(class_names, min_count=3):
    """从类名提取包名前缀并统计频次。
    例: Lio/rong/imlib/NativeObject; → io.rong / io.rong.imlib
    """
    prefixes = Counter()
    for cls in class_names:
        cls = cls.lstrip("L").rstrip(";").replace("/", ".")
        parts = cls.split(".")
        for depth in range(2, len(parts)):
            prefixes[".".join(parts[:depth])] += 1
    return {k: v for k, v in prefixes.items() if v >= min_count}


def extract_apk_info(apk_path):
    result = {
        "file_name": os.path.basename(apk_path),
        "file_size_mb": round(os.path.getsize(apk_path) / (1024 * 1024), 2),
    }
    try:
        from loguru import logger
        logger.disable("androguard")
        from androguard.misc import AnalyzeAPK

        apk, dex_list, _ = AnalyzeAPK(apk_path)

        result["package_name"] = apk.get_package()
        result["version_name"] = apk.get_androidversion_name()
        result["version_code"] = apk.get_androidversion_code()
        result["target_sdk"] = apk.get_target_sdk_version()
        result["min_sdk"] = apk.get_min_sdk_version()
        result["permissions"] = sorted(apk.get_permissions())
        result["component_counts"] = {
            "activities": len(apk.get_activities()),
            "services": len(apk.get_services()),
            "receivers": len(apk.get_receivers()),
            "providers": len(apk.get_providers()),
        }

        all_files = apk.get_files()
        result["native_libs"] = sorted(
            f for f in all_files if f.startswith("lib/") and f.endswith(".so")
        )
        result["assets_files"] = sorted(f for f in all_files if f.startswith("assets/"))

        assets_text = " ".join(result["assets_files"]).lower()
        all_files_text = " ".join(all_files).lower()
        result["framework_markers"] = {
            "react_native": any(k in assets_text for k in ["index.android.bundle", "react-native"]),
            "flutter": "flutter_assets" in assets_text,
            "unity": "unity" in all_files_text,
            "cordova": "cordova" in assets_text,
            "xamarin": "mono" in all_files_text,
        }

        # — DEX 解析；class_count == 0 表示可能加壳 —
        class_count = 0
        all_classes = []
        for dex in dex_list:
            try:
                classes = dex.get_classes_names()
                class_count += len(classes)
                all_classes.extend(classes)
            except Exception:
                pass
        result["class_count"] = class_count

        if all_classes:
            result["package_prefixes"] = dict(
                sorted(extract_prefixes(all_classes).items(), key=lambda x: -x[1])
            )
        else:
            result["package_prefixes"] = {}
            result["dex_parse_failed"] = True  # 解析失败≠已加固，对照 packers.md

        result["has_kotlin"] = any("kotlin" in c.lower() for c in all_classes) or any(
            "kotlin" in f.lower() for f in all_files
        )

    except Exception as e:
        result["error"] = str(e)
        result["androguard_failed"] = True
        for k, v in aapt_facts(apk_path).items():
            result.setdefault(k, v)
    return result


def main():
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        sys.exit(1)
    apk_path = sys.argv[1]
    if not os.path.exists(apk_path):
        print(f"error: file not found: {apk_path}", file=sys.stderr)
        sys.exit(1)

    result = extract_apk_info(apk_path)
    if "--json" in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # 人类可读输出
    print(f"包名:     {result.get('package_name')}")
    print(f"版本:     {result.get('version_name')} / code {result.get('version_code')}")
    print(f"SDK:      {result.get('min_sdk')} -> {result.get('target_sdk')}")
    warn = ""
    if result.get("androguard_failed"):
        warn = "  ⚠️ androguard 失败，已用 aapt 保底"
    elif result.get("class_count") == 0:
        warn = "  ⚠️ DEX 无类名（可能加固或解析失败，对照 packers.md）"
    print(f"类数量:   {result.get('class_count')}{warn}")
    print(f"组件:     {result.get('component_counts')}")
    print(f"框架标记: {result.get('framework_markers')}")
    print(f"Kotlin:   {result.get('has_kotlin')}")
    print(f"native:   {len(result.get('native_libs', []))} 个")
    for lib in result.get("native_libs", []):
        print(f"          {lib}")
    print(f"权限:     {len(result.get('permissions', []))} 项")
    print("\n== 主要包名前缀 (Top 40) ==")
    for k, v in list(result.get("package_prefixes", {}).items())[:40]:
        print(f"{v:6d}  {k}")


if __name__ == "__main__":
    main()
